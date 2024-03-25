# add-annotation-overlay-ic

* accepts: idc.api.ImageClassificationData
* generates: idc.api.ImageClassificationData

Adds the image classification label on top of images passing through.

```
usage: add-annotation-overlay-ic [-h] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                                 [-N LOGGER_NAME] [-p X,Y] [-f FONTNAME]
                                 [-s SIZE] [-c R,G,B] [-B] [-C R,G,B]
                                 [-M MARGIN]

Adds the image classification label on top of images passing through.

optional arguments:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        The logging level to use. (default: WARN)
  -N LOGGER_NAME, --logger_name LOGGER_NAME
                        The custom name to use for the logger, uses the plugin
                        name by default (default: None)
  -p X,Y, --position X,Y
                        The position of the label (X,Y). (default: 5,5)
  -f FONTNAME, --font_family FONTNAME
                        The name of the TTF font-family to use, note: any
                        hyphens need escaping with backslash. (default:
                        sans\-serif)
  -s SIZE, --font_size SIZE
                        The size of the font. (default: 14)
  -c R,G,B, --font_color R,G,B
                        The RGB color triplet to use for the font. (default:
                        255,255,255)
  -B, --fill_background
                        Whether to fill the background of the text with the
                        specified color. (default: False)
  -C R,G,B, --background_color R,G,B
                        The RGB color triplet to use for the background.
                        (default: 0,0,0)
  -M MARGIN, --background_margin MARGIN
                        The margin in pixels around the background. (default:
                        2)
```
