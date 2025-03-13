import argparse
import copy
from typing import List

from shapely.geometry import Polygon, GeometryCollection, MultiPolygon
from shapely.ops import unary_union
from wai.logging import LOGGING_WARNING
from wai.common.geometry import Polygon as WaiPolygon
from wai.common.geometry import Point as WaiPoint
from wai.common.adams.imaging.locateobjects import LocatedObjects, LocatedObject
from wai.common.file.report import save
from seppl.placeholders import placeholder_list, PlaceholderSupporter
from seppl.io import Filter
from idc.api import ObjectDetectionData, flatten_list, make_list, INTERSECT, UNION, COMBINATIONS, intersect_over_union, locatedobjects_to_shapely

STREAM_INDEX = "stream_index"


class CombineAnnotations(Filter, PlaceholderSupporter):
    """
    Combines object detection annotations from images passing through into a single annotation.
    """

    def __init__(self, min_iou: float = 0.7, combination: str = INTERSECT,
                 output_file: str = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the filter.

        :param min_iou: the minimum IoU (intersect over union) to use for identifying objects that overlap
        :type min_iou: float
        :param combination: how to combine the annotations
        :type combination: str
        :param output_file: the .report file to store the combined annotations in
        :type output_file: str
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.min_iou = min_iou
        if combination not in COMBINATIONS:
            raise ValueError("Unknown combination: %s" % combination)
        self.combination = combination
        self.output_file = output_file
        self._stream_index = None
        self._annotation = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "combine-annotations-od"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Combines object detection annotations from images passing through into a single annotation."

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        return [ObjectDetectionData]

    def generates(self) -> List:
        """
        Returns the list of classes that get produced.

        :return: the list of classes
        :rtype: list
        """
        return [ObjectDetectionData]

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("--min_iou", type=float, default=0.7, help="The minimum IoU (intersect over union) to use for identifying objects that overlap", required=False)
        parser.add_argument("--combination", choices=COMBINATIONS, default=INTERSECT, help="how to combine the annotations (%s); the '%s' key in the meta-data contains the stream index" % ("|".join(COMBINATIONS), STREAM_INDEX), required=False)
        parser.add_argument("-o", "--output_file", type=str, metavar="FILE", help="The .report file to write the combined annotations to. " + placeholder_list(obj=self), required=False, default="./combined.report")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.min_iou = ns.min_iou
        self.combination = ns.combination
        self.output_file = ns.output_file

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        self._stream_index = 0
        if (self.output_file is None) or (len(self.output_file) == 0):
            raise Exception("No output file defined!")

    def _find_matches(self, polygons_old, polygons_new):
        """
        Finds the matches between the old and new annotations.

        :param polygons_old: the old annotations
        :type polygons_old: list
        :param polygons_new: the new annotations
        :type polygons_new: list
        :return: the matches, list of old/new index tuples (an index of -1 means no match found)
        :rtype: list
        """
        result = []
        match_new = set([x for x in range(len(polygons_new))])
        match_old = set([x for x in range(len(polygons_old))])
        for n, poly_new in enumerate(polygons_new):
            for o, poly_old in enumerate(polygons_old):
                iou = intersect_over_union(poly_new, poly_old)
                if iou > 0:
                    if iou >= self.min_iou:
                        if n in match_new:
                            match_new.remove(n)
                        if o in match_old:
                            match_old.remove(o)
                        result.append((o, n, iou))

        # add old polygons that had no match
        for o in match_old:
            result.append((o, -1, 0.0))

        # add new polygons that had no match
        for n in match_new:
            result.append((-1, n, 0.0))

        return result

    def _do_process(self, data):
        """
        Processes the data record(s).

        :param data: the record(s) to process
        :return: the potentially updated record(s)
        """
        result = []

        for item in make_list(data):
            result.append(item)

            if self._annotation is None:
                self._annotation = copy.deepcopy(item.get_absolute())
                continue

            self._stream_index += 1

            # combine annotations
            current_annotation = item.get_absolute()
            polygons_old = locatedobjects_to_shapely(self._annotation)
            polygons_new = locatedobjects_to_shapely(current_annotation)
            matches = self._find_matches(polygons_old, polygons_new)
            combined = []
            for o, n, iou in matches:
                if o == -1:
                    combined.append(current_annotation[n])
                elif n == -1:
                    combined.append(self._annotation[o])
                else:
                    # combine polygons
                    if self.combination == UNION:
                        poly_comb = unary_union([polygons_new[n], polygons_old[o]])
                    elif self.combination == INTERSECT:
                        poly_comb = polygons_new[n].intersection(polygons_old[o])
                    else:
                        raise Exception("Unknown combination method: %s" % self.combination)
                    # grab the first polygon
                    if isinstance(poly_comb, GeometryCollection):
                        for x in poly_comb.geoms:
                            if isinstance(x, Polygon):
                                poly_comb = x
                                break
                    elif isinstance(poly_comb, MultiPolygon):
                        for x in poly_comb.geoms:
                            if isinstance(x, Polygon):
                                poly_comb = x
                                break

                    if isinstance(poly_comb, Polygon):
                        # create new located object
                        minx, miny, maxx, maxy = [int(x) for x in poly_comb.bounds]
                        x_list, y_list = poly_comb.exterior.coords.xy
                        points = []
                        for i in range(len(x_list)):
                            points.append(WaiPoint(x=x_list[i], y=y_list[i]))
                        lobj = LocatedObject(minx, miny, maxx - minx + 1, maxy - miny + 1)
                        lobj.set_polygon(WaiPolygon(*points))
                        lobj.metadata[STREAM_INDEX] = self._stream_index
                        combined.append(lobj)
                    else:
                        self.logger().warning(
                            "Unhandled geometry type returned from combination, skipping: %s" % str(type(poly_comb)))

            self._annotation = LocatedObjects(combined)

        return flatten_list(result)

    def finalize(self):
        """
        Finishes the processing, e.g., for closing files or databases.
        """
        super().finalize()
        if self._annotation is not None:
            report = self._annotation.to_report()
            output_file = self.session.expand_placeholders(self.output_file)
            self.logger().info("Writing combined annotations to: %s" % output_file)
            save(report, output_file)
