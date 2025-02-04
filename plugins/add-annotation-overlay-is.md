# add-annotation-overlay-is

* accepts: idc.api.ImageSegmentationData
* generates: idc.api.ImageSegmentationData

Adds the image segmentation annotations on top of images passing through.

```
usage: add-annotation-overlay-is [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                 [-N LOGGER_NAME] [--labels [LABEL ...]]
                                 [-c [R,G,B ...]] [-a INT]

Adds the image segmentation annotations on top of images passing through.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  --labels [LABEL ...]  The labels of annotations to overlay, overlays all if
                        omitted. (default: None)
  -c [R,G,B ...], --colors [R,G,B ...]
                        The color list name (available: colorblind12,colorblin
                        d15,colorblind24,colorblind8,dark,light,x11) or list
                        of RGB triplets (R,G,B) of custom colors to use, uses
                        default colors if not supplied (X11 colors, without
                        dark/light colors) (default: None)
  -a INT, --alpha INT   The alpha value to use for overlaying the annotations
                        (0: transparent, 255: opaque). (default: 64)
```
