# add-annotation-overlay-is

* accepts: idc.api.ImageSegmentationData
* generates: idc.api.ImageSegmentationData

Adds the image segmentation annotations on top of images passing through.

```
usage: add-annotation-overlay-is [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                 [-N LOGGER_NAME]
                                 [--labels [LABEL [LABEL ...]]]
                                 [-c [R,G,B [R,G,B ...]]] [-a INT]

Adds the image segmentation annotations on top of images passing through.

optional arguments:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  --labels [LABEL [LABEL ...]]
                        The labels of annotations to overlay, overlays all if
                        omitted. (default: None)
  -c [R,G,B [R,G,B ...]], --colors [R,G,B [R,G,B ...]]
                        The RGB triplets (R,G,B) of custom colors to use, uses
                        default colors if not supplied (default: None)
  -a INT, --alpha INT   The alpha value to use for overlaying the annotations
                        (0: transparent, 255: opaque). (default: 64)
```
