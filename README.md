# Subtle

Subtle is a simple editor and OCR wrapper for subtitles. It was created to convert PGS subtitles
to SRT format for MKV files.

It can currently process SRT, PGS and SSA subtitle formats from containers, and output SRT files.

The extraction part requires MkvToolNix to be installed, and the OCR feature requires Tesseract to
be installed. This app assumes the `tesseract`, `mkvextract` and `mkvmerge` commands` can be called
from command line.

This is a work in progress.
