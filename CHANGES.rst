Changelog
=========

0.0.5 (????-??-??)
------------------

- added `--bbox_outline_outwards` flag to filter `add-annotation-overlay-od` to make very
  small rectangles/points better visible by drawing the outline on the outside rather
  than the inside of the bbox


0.0.4 (2025-03-14)
------------------

- added support for placeholders: `combine-annotations-od`, `to-annotation-overlay-od`
- using underscores now instead of dashes in dependencies (`setup.py`)


0.0.3 (2025-02-26)
------------------

- switched to underscores in project name
- using `simple_palette_utils` now
- filters `add-annotation-overlay-is`, `add-annotation-overlay-od` and `add-center-overlay-od` are now using
  the `ColorProvider` class to simplify the color handling and can use a color list name as well rather than
  explicit list of R,G,B triplets


0.0.2 (2024-07-02)
------------------

- added `add-center-overlay-od` overlay filter


0.0.1 (2024-05-06)
------------------

- initial release

