# Subtle

Subtle is a simple editor and OCR wrapper for subtitles. It was created to convert PGS subtitles
to SRT format for MKV files.

It can currently process SRT, PGS and SSA subtitle formats from containers, and output SRT files.

The extraction part requires MkvToolNix to be installed, and the OCR feature requires Tesseract to
be installed. This app assumes the `tesseract`, `mkvextract` and `mkvmerge` commands can be called
from command line.

The app uses PyQt6 for the GUI, and Enchant for spell checking.

## Disclaimer

This is most definitely a work in progress, and there are probably plenty of issues. However, the
app works and I've used it to convert subtitles from numerous movies and TV episodes already.

The app is developed on Debian Linux, and I have no idea if it runs on other systems. The file
browser certainly assumes that file system root is `/`, so it probably doesn't work on Windows
without modification.

## Usage

Install the PyQt6 and enchant dependencies, either from distro repo or in a Python virtual env
using the `requirements.txt` file.

Install MkvToolNix and Tesseract. For Debian, this is:

```bash
sudo apt install mkvtoolnix tesseract-ocr
```

Launch the Subtle start script from the root of the source:

```bash
./subtle.py
```

Add `--info` or `--debug` for more log output.
