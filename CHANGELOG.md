# Subtle Changelog

## Version 26.1.1 [2026-06-24]

### Release Notes

Small bugfix release that renames the root package to `subtle_gui` since a project named `subtle`
already exists.

### Detailed Changelog

* Renames the installed package to `subtle_gui`.
* Updates main readme with PyPI info.

----

## Version 26.1 [2026-06-24]

### Release Notes

Initial release of the app with basic functionality. It can read media files, and extract SRT,
PGS and SSA subtitles. PGS subtitles can be OCR scanned to extract the text, which can then be
edited and spell checked. Italics is the only supported formatting.

SSA subs can also be read, and are converted on the fly to plain text with the italics HTML tags.

### Detailed Changelog

* Initial release.
