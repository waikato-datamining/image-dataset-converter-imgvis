import argparse
from typing import List

import cv2
import numpy as np
from wai.logging import LOGGING_WARNING

from idc.api import ImageData, StreamWriter, make_list


class ImageViewer(StreamWriter):

    def __init__(self, title: str = None, position: str = None, size: str = None, delay: int = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the reader.

        :param title: the title for the window
        :type title: str
        :param position: the position of the window (X,Y)
        :type position: str
        :param size: the size of the window (WIDTH,HEIGHT)
        :type size: str
        :param delay: the delay between images, ignored if <0
        :type delay: int
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.title = title
        self.position = position
        self.size = size
        self.delay = delay
        self._x = None
        self._y = None
        self._width = None
        self._height = None
        self._ratio = None
        self._window_positioned = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "image-viewer"

    def description(self) -> str:
        """
        Returns a description of the writer.

        :return: the description
        :rtype: str
        """
        return "Displays images."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-t", "--title", type=str, help="The title for the window.", required=False, default="image-dataset-converter")
        parser.add_argument("-p", "--position", type=str, metavar="X,Y", help="The position of the window on screen (X,Y).", required=False, default="0,0")
        parser.add_argument("-s", "--size", type=str, metavar="WIDTH,HEIGHT", help="the maximum size for the image: WIDTH,HEIGHT.", required=False, default="640,480")
        parser.add_argument("-d", "--delay", type=int, metavar="MSEC", help="The delay in milli-seconds between images, use 0 to wait for keypress, ignored if <0", required=False, default=500)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.title = ns.title
        self.position = ns.position
        self.size = ns.size
        self.delay = ns.delay

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        return [ImageData]

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        if self.title is None:
            self.title = "image-dataset-converter"
        if self.position is None:
            self.position = "0,0"
        if self.size is None:
            self.size = "640,480"
        if self.delay is None:
            self.delay = 500
        self._x, self._y = [int(x) for x in self.position.split(",")]
        self._width, self._height = [int(x) for x in self.size.split(",")]
        self._ratio = self._width / self._height
        self._window_positioned = None

    def write_stream(self, data):
        """
        Saves the data one by one.

        :param data: the data to write (single record or iterable of records)
        """
        for item in make_list(data):
            img = np.array(item.image)
            # convert RGB to BGR
            img = img[:, :, ::-1].copy()

            # resize image, if necessary
            h, w, _ = img.shape
            if (h > self._height) or (w > self._width):
                img_ratio = w / h
                if img_ratio > self._ratio:
                    w_new = self._width
                    h_new = w_new / img_ratio
                else:
                    h_new = self._height
                    w_new = h_new * img_ratio
                img = cv2.resize(img, (int(w_new), int(h_new)))

            cv2.imshow(self.title, img)

            # position window
            if self._window_positioned is None:
                cv2.moveWindow(self.title, self._x, self._y)
                self._window_positioned = True

            # delay
            if self.delay >= 0:
                cv2.waitKey(self.delay)

    def finalize(self):
        """
        Finishes the processing, e.g., for closing files or databases.
        """
        super().finalize()
        cv2.destroyAllWindows()
