import argparse
import io
from typing import List

from PIL import Image, ImageDraw

from wai.logging import LOGGING_WARNING
from seppl.io import Filter
from idc.api import ImageClassificationData, flatten_list, make_list, load_font, text_size, DEFAULT_FONT_FAMILY


class AnnotationOverlayIC(Filter):
    """
    Adds the image classification label on top of images passing through.
    """

    def __init__(self, position: str = None, font_family: str = None, font_size: int = None, font_color: str = None,
                 fill_background: bool = False, background_color: str = None, background_margin: int = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the filter.

        :param position: the position of the label (X,Y)
        :type position: str
        :param font_family: the name of the TTF font-family to use, note: any hyphens need escaping with backslash
        :type font_family: str
        :param font_size: the size of the font
        :type font_size: int
        :param font_color: the RGB color triplet to use for the font (R,G,B)
        :type font_color: str
        :param fill_background: whether to fill the background of the text with the specified color
        :type fill_background: bool
        :param background_color: the RGB color triplet to use for the background (R,G,B)
        :type background_color: str
        :param background_margin: the margin in pixels around the background
        :type background_margin: int
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.position = position
        self.font_family = font_family
        self.font_size = font_size
        self.font_color = font_color
        self.fill_background = fill_background
        self.background_color = background_color
        self.background_margin = background_margin
        self._colors = None
        self._font = None
        self._font_color = None
        self._background_color = None
        self._text_x = None
        self._text_y = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "add-annotation-overlay-ic"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Adds the image classification label on top of images passing through."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-p", "--position", type=str, metavar="X,Y", help="The position of the label (X,Y).", required=False, default="5,5")
        parser.add_argument("-f", "--font_family", type=str, metavar="FONTNAME", help="The name of the TTF font-family to use, note: any hyphens need escaping with backslash.", required=False, default=DEFAULT_FONT_FAMILY)
        parser.add_argument("-s", "--font_size", type=int, metavar="SIZE", help="The size of the font.", required=False, default=14)
        parser.add_argument("-c", "--font_color", type=str, metavar="R,G,B", help="The RGB color triplet to use for the font.", required=False, default="255,255,255")
        parser.add_argument("-B", "--fill_background", action="store_true", help="Whether to fill the background of the text with the specified color.")
        parser.add_argument("-C", "--background_color", type=str, metavar="R,G,B", help="The RGB color triplet to use for the background.", required=False, default="0,0,0")
        parser.add_argument("-M", "--background_margin", type=int, metavar="MARGIN", help="The margin in pixels around the background.", required=False, default=2)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.position = ns.position
        self.font_family = ns.font_family
        self.font_size = ns.font_size
        self.font_color = ns.font_color
        self.fill_background = ns.fill_background
        self.background_color = ns.background_color
        self.background_margin = ns.background_margin

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        return [ImageClassificationData]

    def generates(self) -> List:
        """
        Returns the list of classes that get produced.

        :return: the list of classes
        :rtype: list
        """
        return [ImageClassificationData]

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        if self.position is None:
            self.position = "5,5"
        if self.font_family is None:
            self.font_family = DEFAULT_FONT_FAMILY
        if self.font_size is None:
            self.font_size = 14
        if self.font_color is None:
            self.font_color = "255,255,255"
        if self.fill_background is None:
            self.fill_background = False
        if self.background_color is None:
            self.background_color = "0,0,0"
        if self.background_margin is None:
            self.background_margin = 2
        self._font = load_font(self.logger, self.font_family, self.font_size)
        self._font_color = tuple([int(x) for x in self.font_color.split(",")])
        self._background_color = tuple([int(x) for x in self.background_color.split(",")])
        self._text_x, self._text_y = [int(x) for x in self.position.upper().split(",")]

    def _do_process(self, data):
        """
        Processes the data record(s).

        :param data: the record(s) to process
        :return: the potentially updated record(s)
        """
        result = []

        for item in make_list(data):
            img_pil = item.image.copy()
            overlay = Image.new('RGBA', item.image_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # background?
            if self.fill_background:
                w, h = text_size(item.annotation, font=self._font)
                draw.rectangle(
                    (
                        self._text_x - self.background_margin,
                        self._text_y - self.background_margin,
                        self._text_x + w + self.background_margin * 2,
                        self._text_y + h + self.background_margin * 2
                    ),
                    fill=self._background_color)

            # label
            draw.text((self._text_x, self._text_y), item.annotation, font=self._font, fill=self._font_color)

            img_pil.paste(overlay, (0, 0), mask=overlay)

            # convert back to PIL bytes
            img_bytes = io.BytesIO()
            img_pil.save(img_bytes, format=item.image_format)
            item_new = ImageClassificationData(data=img_bytes.getvalue(), image_name=item.image_name,
                                               annotation=item.annotation, metadata=item.get_metadata())

            result.append(item_new)

        return flatten_list(result)
