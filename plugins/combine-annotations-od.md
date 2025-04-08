# combine-annotations-od

* accepts: idc.api.ObjectDetectionData
* generates: idc.api.ObjectDetectionData

Combines object detection annotations from images passing through into a single annotation.

```
usage: combine-annotations-od [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                              [-N LOGGER_NAME] [--skip] [--min_iou MIN_IOU]
                              [--combination {union,intersect}] [-o FILE]

Combines object detection annotations from images passing through into a
single annotation.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  --skip                Disables the plugin, removing it from the pipeline.
                        (default: False)
  --min_iou MIN_IOU     The minimum IoU (intersect over union) to use for
                        identifying objects that overlap (default: 0.7)
  --combination {union,intersect}
                        how to combine the annotations (union|intersect); the
                        'stream_index' key in the meta-data contains the
                        stream index (default: intersect)
  -o FILE, --output_file FILE
                        The .report file to write the combined annotations to.
                        Supported placeholders: {HOME}, {CWD}, {TMP} (default:
                        ./combined.report)
```

Available placeholders:

* `{HOME}`: The home directory of the current user.
* `{CWD}`: The current working directory.
* `{TMP}`: The temp directory.
