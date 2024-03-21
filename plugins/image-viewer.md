# image-viewer

* accepts: idc.api.ImageData

Displays images.

```
usage: image-viewer [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [-N LOGGER_NAME] [-t TITLE] [-p X,Y] [-s WIDTH,HEIGHT]
                    [-d MSEC]

Displays images.

optional arguments:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  -t TITLE, --title TITLE
                        The title for the window. (default: image-dataset-
                        converter)
  -p X,Y, --position X,Y
                        The position of the window on screen (X,Y). (default:
                        0,0)
  -s WIDTH,HEIGHT, --size WIDTH,HEIGHT
                        the maximum size for the image: WIDTH,HEIGHT.
                        (default: 640,480)
  -d MSEC, --delay MSEC
                        The delay in milli-seconds between images, use 0 to
                        wait for keypress, ignored if <0 (default: 500)
```
