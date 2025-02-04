import argparse
import copy
import io
from typing import List, Union

from PIL import Image, ImageDraw
from seppl.io import Filter
from simple_palette_utils import COLOR_LISTS, COLOR_LIST_X11, ColorProvider, parse_rgb, color_lists
from wai.logging import LOGGING_WARNING

from idc.api import ImageSegmentationData, flatten_list, make_list


class AnnotationOverlayIS(Filter):
    """
    Adds the image classification label on top of images passing through.
    """

    def __init__(self, labels: List[str] = None, alpha: int = None, colors: Union[str, List[str]] = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the filter.

        :param labels: the labels of annotations to overlay, overlays all if omitted
        :type labels: list
        :param alpha: the alpha value to use for overlaying the annotati    ons (0: transparent, 255: opaque)
        :type alpha: int
        :param colors: the color list name or list of RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied
        :type colors: list
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.labels = labels
        self.alpha = alpha
        if isinstance(colors, str):
            colors = [colors]
        self.colors = colors
        self._accepted_labels = None
        self._label_mapping = None
        self._color_provider = None

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
        parser.add_argument("-c", "--colors", type=str, metavar="R,G,B", help="The color list name (available: " + ",".join(color_lists()) + ") or list of RGB triplets (R,G,B) of custom colors to use, uses default colors if not supplied (X11 colors, without dark/light colors)", required=False, nargs="*")
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
            self._color_provider.label_mapping = self._label_mapping

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
                draw.bitmap((0, 0), mask, fill=self._color_provider.get_color(label, alpha=self.alpha))

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
