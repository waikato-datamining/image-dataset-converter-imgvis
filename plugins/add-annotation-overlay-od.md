# add-annotation-overlay-od

* accepts: idc.api.ObjectDetectionData
* generates: idc.api.ObjectDetectionData

Adds object detection overlays to images passing through.

```
usage: add-annotation-overlay-od [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                 [-N LOGGER_NAME] [--skip]
                                 [--labels [LABEL ...]] [--label_key KEY]
                                 [--text_format KEY] [--text_placement X,Y]
                                 [--font_family FONTNAME] [--font_size SIZE]
                                 [--num_decimals INT] [-c [R,G,B ...]]
                                 [--outline_thickness INT]
                                 [--outline_alpha INT] [--fill]
                                 [--fill_alpha INT] [--vary_colors]
                                 [--force_bbox] [--bbox_outline_outwards]

Adds object detection overlays to images passing through.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  --skip                Disables the plugin, removing it from the pipeline.
                        (default: False)
  --labels [LABEL ...]  The labels of annotations to overlay, overlays all if
                        omitted. (default: None)
  --label_key KEY       The key in the meta-data that contains the label.
                        (default: type)
  --text_format KEY     Template for the text to print on top of the bounding
                        box or polygon, '{PH}' is a placeholder for the 'PH'
                        value from the meta-data or 'label' for the current
                        label; ignored if empty. (default: {label})
  --text_placement X,Y  Comma-separated list of vertical (T=top, C=center,
                        B=bottom) and horizontal (L=left, C=center, R=right)
                        anchoring. (default: T,L)
  --font_family FONTNAME
                        The name of the TTF font-family to use, note: any
                        hyphens need escaping with backslash. (default:
                        sans\-serif)
  --font_size SIZE      The size of the font. (default: 14)
  --num_decimals INT    The number of decimals to use for float numbers in the
                        text format string. (default: 3)
  -c [R,G,B ...], --colors [R,G,B ...]
                        The color list name (available: colorblind12,colorblin
                        d15,colorblind24,colorblind8,dark,light,x11) or list
                        of RGB triplets (R,G,B) of custom colors to use, uses
                        default colors if not supplied (X11 colors, without
                        dark/light colors) (default: None)
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
  --force_bbox          Whether to force a bounding box even if there is a
                        polygon available. (default: False)
  --bbox_outline_outwards
                        Whether to draw the rectangle outline on the outside
                        rather than inside. (default: False)
```
