"""
Subtle – OCR Base Class
=======================

This file is a part of Subtle
Copyright (C) Veronica Berglyd Olsen

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
"""  # noqa

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from subtle_gui import CONFIG
from subtle_gui.constants import Constants

if TYPE_CHECKING:
    from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)


class OCRBase(ABC):
    """Base class for OCR implementations."""

    def __init__(self) -> None:
        return

    @abstractmethod
    def processImage(self, index: int, image: QImage, lang: list[str]) -> list[str]:
        """Process an image and return the recognized text."""
        raise NotImplementedError

    def postProcessText(self, text: list[str]) -> list[str]:
        """Run standard text post-processing tasks."""
        dialogLine = CONFIG.getSetting("dialogLine")
        dialogSpace = CONFIG.getFlag("dialogSpace")
        result = []
        for line in text:
            if line.startswith(Constants.DIALOG_LINES):
                post = dialogLine + (" " if dialogSpace else "") + line[1:].lstrip()
            else:
                post = line

            if post != line:
                logger.debug("Post Before: '%s'", line)
                logger.debug("Post Result: '%s'", post)

            result.append(post)

        return result
