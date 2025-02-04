import argparse
import copy
import io
from typing import List, Tuple, Dict, Union

from PIL import Image, ImageDraw
from seppl.io import Filter
from simple_palette_utils import COLOR_LISTS, COLOR_LIST_X11, ColorProvider, parse_rgb, color_lists
from wai.logging import LOGGING_WARNING

from idc.api import ObjectDetectionData, flatten_list, make_list, load_font, text_size, DEFAULT_FONT_FAMILY, LABEL_KEY, text_color


class AnnotationOverlayOD(Filter):
    """
    Adds object detection overlays to images passing through.
    """

    def __init__(self, labels: List[str] = None, label_key: str = None,
                 text_format: str = None, text_placement: str = None,
                 font_family: str = None, font_size: int = None,
                 num_decimals: int = None, colors: Union[str, List[str]] = None,
                 outline_thickness: int = None, outline_alpha: int = None,
                 fill: bool = False, fill_alpha: int = None,
                 vary_colors: bool = False, force_bbox: bool = False,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the filter.

        :param labels: the labels of annotations to overlay, overlays all if omitted
        :type labels: list
        :param label_key: the key in the meta-data that contains the label
        :type label_key: str
        :param text_format: template for the text to print on top of the bounding box or polygon, '{PH}' is a placeholder for the 'PH' value from the meta-data or 'label' for the current label; ignored if empty
        :type text_format: str
        :param text_placement: comma-separated list of vertical (T=top, C=center, B=bottom) and horizontal (L=left, C=center, R=right) anchoring
        :type text_placement: str
        :param font_family: the name of the TTF font-family to use, note: any hyphens need escaping with backslash
        :type font_family: str
        :param font_size: the size of the font
        :type font_size: int
        :param num_decimals: the number of decimals to use for float numbers in the text format string
        :type num_decimals: int
        :param colors: the color list name or list of RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied
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
        :param force_bbox: whether to force a bounding box even if there is a polygon available
        :type force_bbox: bool
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.labels = labels
        self.label_key = label_key
        self.text_format = text_format
        self.text_placement = text_placement
        self.font_family = font_family
        self.font_size = font_size
        self.num_decimals = num_decimals
        if isinstance(colors, str):
            colors = [colors]
        self.colors = colors
        self.outline_thickness = outline_thickness
        self.outline_alpha = outline_alpha
        self.fill = fill
        self.fill_alpha = fill_alpha
        self.vary_colors = vary_colors
        self.force_bbox = force_bbox
        self._label_mapping = None
        self._font = None
        self._text_vertical = None
        self._text_horizontal = None
        self._accepted_labels = None
        self._color_provider = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "add-annotation-overlay-od"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Adds object detection overlays to images passing through."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("--labels", type=str, metavar="LABEL", help="The labels of annotations to overlay, overlays all if omitted.", required=False, nargs="*")
        parser.add_argument("--label_key", type=str, metavar="KEY", help="The key in the meta-data that contains the label.", required=False, default=LABEL_KEY)
        parser.add_argument("--text_format", type=str, metavar="KEY", help="Template for the text to print on top of the bounding box or polygon, '{PH}' is a placeholder for the 'PH' value from the meta-data or 'label' for the current label; ignored if empty.", required=False, default="{label}")
        parser.add_argument("--text_placement", type=str, metavar="X,Y", help="Comma-separated list of vertical (T=top, C=center, B=bottom) and horizontal (L=left, C=center, R=right) anchoring.", required=False, default="T,L")
        parser.add_argument("--font_family", type=str, metavar="FONTNAME", help="The name of the TTF font-family to use, note: any hyphens need escaping with backslash.", required=False, default=DEFAULT_FONT_FAMILY)
        parser.add_argument("--font_size", type=int, metavar="SIZE", help="The size of the font.", required=False, default=14)
        parser.add_argument("--num_decimals", type=int, metavar="INT", help="The number of decimals to use for float numbers in the text format string.", required=False, default=3)
        parser.add_argument("-c", "--colors", type=str, metavar="R,G,B", help="The color list name (available: " + ",".join(color_lists()) + ") or list of RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied (X11 colors, without dark/light colors)", required=False, nargs="*")
        parser.add_argument("--outline_thickness", type=int, metavar="INT", help="The line thickness to use for the outline, <1 to turn off.", required=False, default=3)
        parser.add_argument("--outline_alpha", type=int, metavar="INT", help="The alpha value to use for the outline (0: transparent, 255: opaque).", required=False, default=255)
        parser.add_argument("--fill", action="store_true", help="Whether to fill the bounding boxes/polygons.", required=False)
        parser.add_argument("--fill_alpha", type=int, metavar="INT", help="The alpha value to use for the filling (0: transparent, 255: opaque).", required=False, default=128)
        parser.add_argument("--vary_colors", action="store_true", help="Whether to vary the colors of the outline/filling regardless of label.", required=False)
        parser.add_argument("--force_bbox", action="store_true", help="Whether to force a bounding box even if there is a polygon available.", required=False)
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
        self.text_format = ns.text_format
        self.text_placement = ns.text_placement
        self.font_family = ns.font_family
        self.font_size = ns.font_size
        self.num_decimals = ns.num_decimals
        self.colors = ns.colors
        self.outline_thickness = ns.outline_thickness
        self.outline_alpha = ns.outline_alpha
        self.fill = ns.fill
        self.fill_alpha = ns.fill_alpha
        self.vary_colors = ns.vary_colors
        self.force_bbox = ns.force_bbox

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
        if self.text_format is None:
            self.text_format = "{label}"
        if self.text_placement is None:
            self.text_placement = "T,L"
        if self.font_family is None:
            self.font_family = DEFAULT_FONT_FAMILY
        if self.font_size is None:
            self.font_size = 14
        if self.num_decimals is None:
            self.num_decimals = 3
        if self.outline_thickness is None:
            self.outline_thickness = 3
        if self.outline_alpha is None:
            self.outline_alpha = 255
        if self.fill is None:
            self.fill = False
        if self.vary_colors is None:
            self.vary_colors = False
        if self.force_bbox is None:
            self.force_bbox = False

        self._label_mapping = dict()
        self._font = load_font(self.logger, self.font_family, self.font_size)
        self._text_vertical, self._text_horizontal = self.text_placement.upper().split(",")
        self._accepted_labels = None
        if (self.labels is not None) and (len(self.labels) > 0):
            self._accepted_labels = set(self.labels)
        color_list = COLOR_LIST_X11
        custom_colors = None
        if self.colors is not None:
            # color list name?
            if (len(self.colors) == 1) and ("," not in self.colors[0]):
                color_list = self.colors[0]
                if self.colors[0] not in COLOR_LISTS:
                    raise Exception("Unknown color list '%s'! Available lists: %s" % (color_list, ",".join(sorted(COLOR_LISTS.keys()))))
            else:
                custom_colors = parse_rgb(self.colors)
        self._color_provider = ColorProvider(color_list=color_list, custom_colors=custom_colors)

    def _expand_label(self, label: str, metadata: Dict) -> str:
        """
        Expands the label text.

        :param label: the current label
        :type label: str
        :param metadata: the metadata associated with the label
        :type metadata: dict
        :return: the expanded label text
        :rtype: str
        """
        result = self.text_format.replace("{label}", label)
        for key in metadata:
            value = metadata[key]
            if isinstance(value, str) or isinstance(value, int) or isinstance(value, bool):
                result = result.replace("{%s}" % key, str(value))
            elif isinstance(value, float):
                result = result.replace("{%s}" % key, ("%." + str(self.num_decimals) + "f") % float(value))
        return result

    def _text_coords(self, text: str, rect) -> Tuple[int, int, int, int]:
        """
        Determines the text coordinates in the image.

        :param text: the text to output
        :type text: str
        :param rect: the rectangle to use as reference
        :return: the x, y, w, h tuple
        :rtype: tuple
        """
        w, h = text_size(text, font=self._font)

        # x
        if self._text_horizontal == "L":
            x = rect.left()
        elif self._text_horizontal == "C":
            x = rect.left() + (rect.right() - rect.left() - w) // 2
        elif self._text_horizontal == "R":
            x = rect.right() - w
        else:
            raise Exception("Unhandled horizontal text position: %s" % self._text_horizontal)

        # y
        if self._text_vertical == "T":
            y = rect.top()
        elif self._text_vertical == "C":
            y = rect.top() + (rect.bottom() - rect.top() - h) // 2
        elif self._text_vertical == "B":
            y = rect.bottom() - h
        else:
            raise Exception("Unhandled horizontal text position: %s" % self._text_horizontal)

        return x, y, w, h

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
                self._color_provider.label_mapping = self._label_mapping

                # assemble polygon
                points = []
                if lobj.has_polygon() and not self.force_bbox:
                    poly_x = lobj.get_polygon_x()
                    poly_y = lobj.get_polygon_y()
                    for x, y in zip(poly_x, poly_y):
                        points.append((x, y))
                else:
                    rect = lobj.get_rectangle()
                    points.append((rect.left(), rect.top()))
                    points.append((rect.right(), rect.top()))
                    points.append((rect.right(), rect.bottom()))
                    points.append((rect.left(), rect.bottom()))
                if self.fill:
                    draw.polygon(tuple(points), outline=self._color_provider.get_color(color_label, alpha=self.outline_alpha),
                                 fill=self._color_provider.get_color(color_label, alpha=self.fill_alpha), width=self.outline_thickness)
                else:
                    draw.polygon(tuple(points), outline=self._color_provider.get_color(color_label, alpha=self.outline_alpha),
                                 width=self.outline_thickness)

                # output text
                if len(self.text_format) > 0:
                    text = self._expand_label(label, lobj.metadata)
                    rect = lobj.get_rectangle()
                    x, y, w, h = self._text_coords(text, rect)
                    draw.rectangle((x, y, x + w, y + h), fill=self._color_provider.get_color(color_label, alpha=self.outline_alpha))
                    draw.text((x, y), text, font=self._font, fill=text_color(self._color_provider.get_color(color_label)))

            img_pil.paste(overlay, (0, 0), mask=overlay)

            # convert back to PIL bytes
            img_bytes = io.BytesIO()
            img_pil.save(img_bytes, format=item.image_format)
            item_new = ObjectDetectionData(image_name=item.image_name, data=img_bytes.getvalue(),
                                           annotation=copy.deepcopy(item.annotation), metadata=item.get_metadata())

            result.append(item_new)

        return flatten_list(result)
