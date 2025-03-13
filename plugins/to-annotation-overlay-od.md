# to-annotation-overlay-od

* accepts: idc.api.ObjectDetectionData

Generates an image with all the annotation shapes (bbox or polygon) overlayed.

```
usage: to-annotation-overlay-od [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                [-N LOGGER_NAME] [-c R,G,B,A] [-b R,G,B,A]
                                [-s WIDTH,HEIGHT] [-w INT] [-o FILE]

Generates an image with all the annotation shapes (bbox or polygon) overlayed.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  -c R,G,B,A, --color R,G,B,A
                        The color to use for drawing the shapes as RGBA byte-
                        quadruplet, e.g.: 255,0,0,64. (default: 255,0,0,64)
  -b R,G,B,A, --background_color R,G,B,A
                        The color to use for the background as RGBA byte-
                        quadruplet, e.g.: 255,255,255,255. (default:
                        255,255,255,255)
  -s WIDTH,HEIGHT, --scale_to WIDTH,HEIGHT
                        The dimensions to scale all images to before
                        overlaying them (format: width,height). (default: )
  -w INT, --width INT   The width to use for drawing the polygons. (default:
                        1)
  -o FILE, --output_file FILE
                        The PNG image to write the generated overlay to.
                        Supported placeholders: {HOME}, {CWD}, {TMP} (default:
                        ./output.png)
```

Available placeholders:

* `{HOME}`: The home directory of the current user.
* `{CWD}`: The current working directory.
* `{TMP}`: The temp directory.
