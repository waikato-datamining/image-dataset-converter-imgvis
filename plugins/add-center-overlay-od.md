# add-center-overlay-od

* accepts: idc.api.ObjectDetectionData
* generates: idc.api.ObjectDetectionData

Adds center dot overlays (object detection) to images passing through.

```
usage: add-center-overlay-od [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                             [-N LOGGER_NAME] [--labels [LABEL [LABEL ...]]]
                             [--label_key KEY] [--radius INT]
                             [--colors [R,G,B [R,G,B ...]]]
                             [--outline_thickness INT] [--outline_alpha INT]
                             [--fill] [--fill_alpha INT] [--vary_colors]

Adds center dot overlays (object detection) to images passing through.

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
  --label_key KEY       The key in the meta-data that contains the label.
                        (default: type)
  --radius INT          The size of the dot/circle in pixels. (default: 10)
  --colors [R,G,B [R,G,B ...]]
                        The RGB triplets (R,G,B) of custom colors to use, uses
                        default colors if not supplied (default: None)
  --outline_thickness INT
                        The line thickness to use for the outline, <1 to turn
                        off. (default: 3)
  --outline_alpha INT   The alpha value to use for the outline (0:
                        transparent, 255: opaque). (default: 255)
  --fill                Whether to fill the bounding boxes/polygons. (default:
                        False)
  --fill_alpha INT      The alpha value to use for the filling (0:
                        transparent, 255: opaque). (default: 128)
  --vary_colors         Whether to vary the colors of the outline/filling
                        regardless of label. (default: False)
```
