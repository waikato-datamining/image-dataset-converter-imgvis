import argparse
from typing import List

from PIL import Image, ImageDraw
from wai.logging import LOGGING_WARNING

from seppl.placeholders import placeholder_list, PlaceholderSupporter, expand_placeholders
from idc.api import ObjectDetectionData, StreamWriter, make_list


class AnnotationOverlay(StreamWriter, PlaceholderSupporter):

    def __init__(self, color: str = None, background_color: str = None, scale_to: str = None,
                 width: int = None, output_file: str = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the reader.

        :param color: the color to use for drawing the shapes as RGBA byte-quadruplet, e.g.: 255,0,0,64
        :type color: str
        :param background_color: the color to use for the background as RGBA byte-quadruplet, e.g.: 255,255,255,255
        :type background_color: str
        :param scale_to: the dimensions to scale all images to before overlaying them (format: width,height)
        :type scale_to: str
        :param width: the width to use for drawing the polygons
        :type width: int
        :param output_file: the PNG image to write the generated overlay to
        :type output_file: str
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.color = color
        self.background_color = background_color
        self.scale_to = scale_to
        self.width = width
        self.output_file = output_file
        self._color = None
        self._background_color = None
        self._scale_to = None
        self._overlay = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "to-annotation-overlay-od"

    def description(self) -> str:
        """
        Returns a description of the writer.

        :return: the description
        :rtype: str
        """
        return "Generates an image with all the annotation shapes (bbox or polygon) overlayed."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-c", "--color", type=str, metavar="R,G,B,A", help="The color to use for drawing the shapes as RGBA byte-quadruplet, e.g.: 255,0,0,64.", required=False, default="255,0,0,64")
        parser.add_argument("-b", "--background_color", type=str, metavar="R,G,B,A", help="The color to use for the background as RGBA byte-quadruplet, e.g.: 255,255,255,255.", required=False, default="255,255,255,255")
        parser.add_argument("-s", "--scale_to", type=str, metavar="WIDTH,HEIGHT", help="The dimensions to scale all images to before overlaying them (format: width,height).", required=False, default="")
        parser.add_argument("-w", "--width", type=int, metavar="INT", help="The width to use for drawing the polygons.", required=False, default=1)
        parser.add_argument("-o", "--output_file", type=str, metavar="FILE", help="The PNG image to write the generated overlay to. " + placeholder_list(obj=self), required=False, default="./output.png")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.color = ns.color
        self.background_color = ns.background_color
        self.scale_to = ns.scale_to
        self.width = ns.width
        self.output_file = ns.output_file

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        return [ObjectDetectionData]

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        if self.color is None:
            self.color = "255,0,0,64"
        if self.background_color is None:
            self.background_color = "255,255,255,255"
        if self.scale_to is None:
            self.scale_to = ""
        if self.width is None:
            self.width = 1
        if self.output_file is None:
            self.output_file = "./overlay.png"

    def output_overlay(self):
        """
        Outputs the overlay image.
        """
        if self._overlay is not None:
            self._overlay.save(expand_placeholders(self.output_file), format="PNG")
        else:
            self.logger().warning("No overlay generated!")

    def write_stream(self, data):
        """
        Saves the data one by one.

        :param data: the data to write (single record or iterable of records)
        """
        for item in make_list(data):
            img = item.image

            if self._overlay is None:
                self._scale_to = None
                if len(self.scale_to) > 0:
                    self._scale_to = [int(x) for x in self.scale_to.split(",")]
                    if len(self._scale_to) != 2:
                        self.logger().error(
                            "'--scale_to' option requires format 'width,height' but received: %s" % self.scale_to)
                        self._scale_to = None
                # initialize overlay
                self._color = tuple([int(x) for x in self.color.split(",")])
                self._background_color = tuple([int(x) for x in self.background_color.split(",")])
                self._overlay = Image.new('RGBA', img.size if (self._scale_to is None) else self._scale_to, self._background_color)
            else:
                # do we have to make the overlay larger?
                if self._scale_to is None:
                    if (img.size[0] > self._overlay.size[0]) or (img.size[1] > self._overlay.size[1]):
                        new_size = (max(img.size[0], self._overlay.size[0]), max(img.size[1], self._overlay.size[1]))
                        tmp = Image.new('RGBA', new_size, self._background_color)
                        tmp.paste(self._overlay, (0, 0))
                        self._overlay = tmp

            if self._scale_to is None:
                scale_x = 1.0
                scale_y = 1.0
            else:
                scale_x = self._overlay.size[0] / img.size[0]
                scale_y = self._overlay.size[1] / img.size[1]

            if item.has_annotation():
                draw = ImageDraw.Draw(self._overlay)

                for lobj in item.annotation:
                    points = []
                    if lobj.has_polygon():
                        poly_x = lobj.get_polygon_x()
                        poly_y = lobj.get_polygon_y()
                        for x, y in zip(poly_x, poly_y):
                            points.append((int(x * scale_x), int(y * scale_y)))
                    else:
                        rect = lobj.get_rectangle()
                        points.append((int(rect.left() * scale_x), int(rect.top() * scale_y)))
                        points.append((int(rect.right() * scale_x), int(rect.top() * scale_y)))
                        points.append((int(rect.right() * scale_x), int(rect.bottom() * scale_y)))
                        points.append((int(rect.left() * scale_x), int(rect.bottom() * scale_y)))

                    draw.polygon(tuple(points), outline=self._color, width=self.width)

    def finalize(self):
        """
        Finishes the processing, e.g., for closing files or databases.
        """
        super().finalize()
        self.output_overlay()
