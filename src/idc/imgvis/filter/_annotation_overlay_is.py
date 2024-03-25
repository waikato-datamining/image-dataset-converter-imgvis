import argparse
import copy
import io
from typing import List, Tuple

from PIL import Image, ImageDraw
from seppl.io import Filter
from wai.logging import LOGGING_WARNING

from idc.api import ImageSegmentationData, flatten_list, make_list, default_colors


class AnnotationOverlayIS(Filter):
    """
    Adds the image classification label on top of images passing through.
    """

    def __init__(self, labels: List[str] = None, alpha: int = None, colors: List[str] = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the filter.

        :param labels: the labels of annotations to overlay, overlays all if omitted
        :type labels: list
        :param alpha: the alpha value to use for overlaying the annotations (0: transparent, 255: opaque)
        :type alpha: int
        :param colors: the RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied
        :type colors: list
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.labels = labels
        self.alpha = alpha
        self.colors = colors
        self._colors = None
        self._default_colors = None
        self._default_colors_index = None
        self._custom_colors = None
        self._accepted_labels = None
        self._label_mapping = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "add-annotation-overlay-is"

    def description(self) -> str:
        """
        Returns a description of the handler.

        :return: the description
        :rtype: str
        """
        return "Adds the image segmentation annotations on top of images passing through."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("--labels", type=str, metavar="LABEL", help="The labels of annotations to overlay, overlays all if omitted.", required=False, nargs="*")
        parser.add_argument("-c", "--colors", type=str, metavar="R,G,B", help="The RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied", required=False, nargs="*")
        parser.add_argument("-a", "--alpha", type=int, metavar="INT", help="The alpha value to use for overlaying the annotations (0: transparent, 255: opaque).", required=False, default=64)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.labels = ns.labels
        self.alpha = ns.alpha
        self.colors = ns.colors

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        return [ImageSegmentationData]

    def generates(self) -> List:
        """
        Returns the list of classes that get produced.

        :return: the list of classes
        :rtype: list
        """
        return [ImageSegmentationData]

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        if self.alpha is None:
            self.alpha = 64
        self._colors = dict()
        self._default_colors = default_colors()
        self._default_colors_index = 0
        self._custom_colors = []
        if self.colors is not None:
            for color in self.colors:
                self._custom_colors.append([int(x) for x in color.split(",")])
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

    def _get_color(self, label: str) -> Tuple[int, int, int, int]:
        """
        Returns the color for the label.

        :param label: the label to get the color for
        :type label: str
        :return: the RGBA color tuple
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
        r, g, b = self._colors[label]
        return r, g, b, self.alpha

    def _do_process(self, data):
        """
        Processes the data record(s).

        :param data: the record(s) to process
        :return: the potentially updated record(s)
        """
        result = []

        for item in make_list(data):
            img_pil = item.image

            # create label/index mapping for custom colors
            self._label_mapping = dict()
            for index, label in enumerate(item.annotation.labels):
                self._label_mapping[label] = index

            # create overlay for annotations
            overlay = Image.new('RGBA', img_pil.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            updated = False
            for label in item.annotation.layers:
                # skip label?
                if (self._accepted_labels is not None) and (label not in self._accepted_labels):
                    continue
                # draw overlay
                updated = True
                mask = item.annotation.layers[label]
                mask = Image.fromarray(mask, "L")
                draw.bitmap((0, 0), mask, fill=self._get_color(label))

            if updated:
                # add overlay
                img_pil.paste(overlay, (0, 0), mask=overlay)
                # convert back to PIL bytes
                img_bytes = io.BytesIO()
                img_pil.save(img_bytes, format=item.image_format)
                item_new = ImageSegmentationData(image_name=item.image_name, data=img_bytes.getvalue(),
                                                 annotation=copy.deepcopy(item.annotation), metadata=item.get_metadata())
            else:
                item_new = item

            result.append(item_new)

        return flatten_list(result)
