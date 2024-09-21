"""
Subtle – Shared Data Object
===========================

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QLocale

if TYPE_CHECKING:
    from subtle.core.media import MediaData, MediaTrack
    from subtle.core.spellcheck import SpellEnchant
    from subtle.ocr.base import OCRBase

logger = logging.getLogger(__name__)


class SharedData:

    def __init__(self) -> None:
        self._media: MediaData | None = None
        self._ocr: OCRBase | None = None
        self._spell: SpellEnchant | None = None
        return

    @property
    def media(self) -> MediaData:
        """Return the media data object."""
        if self._media is not None:
            return self._media
        raise RuntimeError("Shared data object not yet initialised.")

    @property
    def ocr(self) -> OCRBase:
        """Return the ocr object."""
        if self._ocr is not None:
            return self._ocr
        raise RuntimeError("Shared data object not yet initialised.")

    @property
    def spelling(self) -> SpellEnchant:
        """Return the spell checker object."""
        if self._spell is not None:
            return self._spell
        raise RuntimeError("Shared data object not yet initialised.")

    def initSharedData(self, media: MediaData, ocr: OCRBase, spell: SpellEnchant) -> None:
        """Init the shared data object. This must be called right after
        the GUI is created.
        """
        self._media = media
        self._ocr = ocr
        self._spell = spell
        return

    def setSpellLanguage(self, track: MediaTrack | None) -> None:
        """Set the current spell checking language."""
        if track is not None:
            locale = QLocale(track.language)
            self.spelling.setLanguage(locale.bcp47Name())
        else:
            self.spelling.setLanguage(None)
        return
