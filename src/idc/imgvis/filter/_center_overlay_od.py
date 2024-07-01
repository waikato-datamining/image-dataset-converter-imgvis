import argparse
import copy
import io
from typing import List, Tuple

from PIL import Image, ImageDraw
from seppl.io import Filter
from wai.logging import LOGGING_WARNING

from idc.api import ObjectDetectionData, flatten_list, make_list, LABEL_KEY, default_colors


class CenterOverlayOD(Filter):
    """
    Adds center dots overlays (object detection) to images passing through.
    """

    def __init__(self, labels: List[str] = None, label_key: str = None, radius: float = None,
                 colors: List[str] = None, outline_thickness: int = None, outline_alpha: int = None,
                 fill: bool = False, fill_alpha: int = None, vary_colors: bool = False,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the filter.

        :param labels: the labels of annotations to overlay, overlays all if omitted
        :type labels: list
        :param label_key: the key in the meta-data that contains the label
        :type label_key: str
        :param radius: the radius of the center dot, if less than 1 then diameter relative to width of bbox
        :type radius: float
        :param colors: the RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied
        :type colors: list
        :param outline_thickness: the line thickness to use for the outline, <1 to turn off
        :type outline_thickness: int
        :param outline_alpha: the alpha value to use for the outline (0: transparent, 255: opaque)
        :type outline_alpha: int
        :param fill: whether to fill the bounding boxes/polygons
        :type fill: bool
        :param fill_alpha: the alpha value to use for the filling (0: transparent, 255: opaque)
        :type fill_alpha: int
        :param vary_colors: whether to vary the colors of the outline/filling regardless of label
        :type vary_colors: bool
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.labels = labels
        self.label_key = label_key
        self.radius = radius
        self.colors = colors
        self.outline_thickness = outline_thickness
        self.outline_alpha = outline_alpha
        self.fill = fill
        self.fill_alpha = fill_alpha
        self.vary_colors = vary_colors
        self._colors = dict()
        self._default_colors = None
        self._default_colors_index = None
        self._custom_colors = None
        self._label_mapping = None
        self._accepted_labels = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "add-center-overlay-od"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Adds center dot overlays (object detection) to images passing through."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("--labels", type=str, metavar="LABEL", help="The labels of annotations to overlay, overlays all if omitted.", required=False, nargs="*")
        parser.add_argument("--label_key", type=str, metavar="KEY", help="The key in the meta-data that contains the label.", required=False, default=LABEL_KEY)
        parser.add_argument("--radius", type=float, metavar="FLOAT", help="The size of the dot/circle in pixels or, if <1 the diameter's relative size to the bbox width.", required=False, default=10)
        parser.add_argument("--colors", type=str, metavar="R,G,B", help="The RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied", required=False, nargs="*")
        parser.add_argument("--outline_thickness", type=int, metavar="INT", help="The line thickness to use for the outline, <1 to turn off.", required=False, default=3)
        parser.add_argument("--outline_alpha", type=int, metavar="INT", help="The alpha value to use for the outline (0: transparent, 255: opaque).", required=False, default=255)
        parser.add_argument("--fill", action="store_true", help="Whether to fill the bounding boxes/polygons.", required=False)
        parser.add_argument("--fill_alpha", type=int, metavar="INT", help="The alpha value to use for the filling (0: transparent, 255: opaque).", required=False, default=128)
        parser.add_argument("--vary_colors", action="store_true", help="Whether to vary the colors of the outline/filling regardless of label.", required=False)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.labels = ns.labels
        self.label_key = ns.label_key
        self.radius = ns.radius
        self.colors = ns.colors
        self.outline_thickness = ns.outline_thickness
        self.outline_alpha = ns.outline_alpha
        self.fill = ns.fill
        self.fill_alpha = ns.fill_alpha
        self.vary_colors = ns.vary_colors

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

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()

        if self.label_key is None:
            self.label_key = LABEL_KEY
        if self.radius is None:
            self.radius = 10
        if self.outline_thickness is None:
            self.outline_thickness = 3
        if self.outline_alpha is None:
            self.outline_alpha = 255
        if self.fill is None:
            self.fill = False
        if self.vary_colors is None:
            self.vary_colors = False

        self._colors = dict()
        self._default_colors = default_colors()
        self._default_colors_index = 0
        self._custom_colors = []
        if self.colors is not None:
            for color in self.colors:
                self._custom_colors.append([int(x) for x in color.split(",")])
        self._label_mapping = dict()
        self._accepted_labels = None
        if (self.labels is not None) and (len(self.labels) > 0):
            self._accepted_labels = set(self.labels)

    def _next_default_color(self) -> Tuple:
        """
        Returns the next default color.

        :return: the color tuple
        :rtype: tuple
        """
        if self._default_colors_index >= len(self._default_colors):
            self._default_colors_index = 0
        result = self._default_colors[self._default_colors_index]
        self._default_colors_index += 1
        return result

    def _get_color(self, label: str) -> Tuple:
        """
        Returns the color for the label.

        :param label: the label to get the color for
        :type label: str
        :return: the RGB color tuple
        :rtype: tuple
        """
        if label not in self._colors:
            has_custom = False
            if label in self._label_mapping:
                index = self._label_mapping[label]
                if index < len(self._custom_colors):
                    has_custom = True
                    self._colors[label] = self._custom_colors[index]
            if not has_custom:
                self._colors[label] = self._next_default_color()
        return self._colors[label]

    def _get_outline_color(self, label: str) -> Tuple[int, int, int, int]:
        """
        Generates the color for the outline.

        :param label: the label to get the color for
        :type label: str
        :return: the RGBA color tuple
        :rtype: tuple
        """
        r, g, b = self._get_color(label)
        return r, g, b, self.outline_alpha

    def _get_fill_color(self, label: str) -> Tuple[int, int, int, int]:
        """
        Generates the color for the filling.

        :param label: the label to get the color for
        :type label: str
        :return: the RGBA color tuple
        :rtype: tuple
        """
        r, g, b = self._get_color(label)
        return r, g, b, self.fill_alpha

    def _do_process(self, data):
        """
        Processes the data record(s).

        :param data: the record(s) to process
        :return: the potentially updated record(s)
        """
        result = []

        for item in make_list(data):
            if not item.has_annotation():
                result.append(item)
                continue

            img_pil = item.image.copy()

            overlay = Image.new('RGBA', img_pil.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            for i, lobj in enumerate(item.annotation):
                # determine label/color
                label = "object"
                if self.label_key in lobj.metadata:
                    label = lobj.metadata[self.label_key]
                if self._accepted_labels is not None:
                    if label not in self._accepted_labels:
                        continue
                if label not in self._label_mapping:
                    self._label_mapping[label] = len(self._label_mapping)
                if self.vary_colors:
                    color_label = "object-%d" % i
                else:
                    color_label = label

                # assemble polygon
                points = []
                rect = lobj.get_rectangle()
                center_x = rect.left() + (rect.right() - rect.left() + 1) // 2
                center_y = rect.top() + (rect.bottom() - rect.top() + 1) // 2
                if self.radius < 1:
                    width = rect.right() - rect.left() + 1
                    radius = int(width / 2 * self.radius)
                else:
                    radius = self.radius
                points.append((center_x - radius, center_y - radius))
                points.append((center_x + radius, center_y + radius))
                if self.fill:
                    draw.ellipse(tuple(points), outline=self._get_outline_color(color_label),
                                 fill=self._get_fill_color(color_label), width=self.outline_thickness)
                else:
                    draw.ellipse(tuple(points), outline=self._get_outline_color(color_label),
                                 width=self.outline_thickness)

            img_pil.paste(overlay, (0, 0), mask=overlay)

            # convert back to PIL bytes
            img_bytes = io.BytesIO()
            img_pil.save(img_bytes, format=item.image_format)
            item_new = ObjectDetectionData(image_name=item.image_name, data=img_bytes.getvalue(),
                                           annotation=copy.deepcopy(item.annotation), metadata=item.get_metadata())

            result.append(item_new)

        return flatten_list(result)
