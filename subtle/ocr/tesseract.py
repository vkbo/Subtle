"""
Subtle – Tesseract OCR Wrapper
==============================

This file is a part of Subtle
Copyright 2024, Veronica Berglyd Olsen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import logging
import re
import subprocess
import uuid

from pathlib import Path

from subtle import CONFIG
from subtle.common import regexCleanup, simplified
from subtle.ocr.base import OCRBase

from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)

TXT_REPLACE = {
    "|": "I",
    "--": "\u2014",
    "....": "...",
    "\u2018": "\u0027",
    "\u2019": "\u0027",
    "\u201c": "\u0022",
    "\u201d": "\u0022",
}

RX_REPLACE = {
    "all": [
        (re.compile(r"^(-\s)[\w]", re.UNICODE), "-"),
        (re.compile(r"^(\.{2})[\s\w]", re.UNICODE), "..."),
        (re.compile(r"^(\.{3}\s)\w", re.UNICODE), "..."),

        # Wrong capitalisation in the middle of words
        (re.compile(r"[a-z]+(S)", re.UNICODE), "s"),
        (re.compile(r"[a-z]+(O)", re.UNICODE), "o"),

        # Slash for I in italics
        (re.compile(r"(?:^|\s)(\/)\s", re.UNICODE), "I"),

        # Notes
        (re.compile(r"(?:^|\s|\[|\()(J|f)(?:$|\s|\]|\))", re.UNICODE), "\u266a"),
    ],
    "eng": [
        # Misinterpreted words
        (re.compile(r"\b(tt)\b", re.UNICODE), "it"),
        (re.compile(r"\b(fo)\b", re.UNICODE), "to"),

        # Wrong capitalisation at the start of words
        (re.compile(r"(?<![.!?\)\]-])\s(K)now", re.UNICODE), "k"),
        (re.compile(r"(?<![.!?\)\]-])\s(I)t+", re.UNICODE), "i"),
        (re.compile(r"(?<![.!?\)\]-])\s(S)o+", re.UNICODE), "s"),

        # Missing apostrophe
        (re.compile(r"\b[D|d]id(nt)\b", re.UNICODE), "n't"),
        (re.compile(r"\b[T|t]hey(re)\b", re.UNICODE), "'re"),
        (re.compile(r"\b[Y|y]ou(ll)\b", re.UNICODE), "'ll"),
        (re.compile(r"\b(l'll)\b", re.UNICODE), "I'll"),
    ]
}


class TesseractOCR(OCRBase):

    def __init__(self) -> None:
        super().__init__()
        return

    def processImage(self, index: int, image: QImage, lang: list[str]) -> list[str]:
        """Perform OCR on a QImage."""
        tmpFile = CONFIG.dumpPath / f"{str(uuid.uuid4())}.png"
        image.save(str(tmpFile), quality=100)
        result = self._processText(self._callTesseract(tmpFile, lang), lang)
        tmpFile.unlink(missing_ok=True)
        return result

    ##
    #  Internal Functions
    ##

    def _callTesseract(self, file: Path, lang: list[str]) -> str:
        """Call tesseract on an image file."""
        try:
            cmd = ["tesseract", str(file), "-", "-l", "+".join(lang)]
            if tessData := CONFIG.getSetting("tessData"):
                cmd += ["--tessdata-dir", tessData]
            p = subprocess.Popen(
                ["tesseract", str(file), "-", "-l", "+".join(lang)],
                stdout=subprocess.PIPE,
            )
            out, _ = p.communicate()
            return out.decode("utf-8")
        except Exception as e:
            logger.error("Failed to extract text with tesseract", exc_info=e)
        return ""

    def _processText(self, text: str, lang: list[str]) -> list[str]:
        """Post-process text returned from tesseract."""
        temp = text.strip()
        for a, b in TXT_REPLACE.items():
            temp = temp.replace(a, b)

        fixed = temp
        for key, patterns in RX_REPLACE.items():
            if key in ("all", *lang):
                prev = fixed
                fixed = regexCleanup(prev, patterns)
                if fixed != prev:
                    logger.debug("Rx Before: '%s'", prev.replace("\n", "|"))
                    logger.debug("Rx Result: '%s'", fixed.replace("\n", "|"))

        return [r for r in [simplified(t) for t in fixed.split("\n")] if r]
