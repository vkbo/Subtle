"""
Subtle – Constants
==================

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

from enum import Enum
from typing import Final

from PyQt6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication


def trConst(text: str) -> str:
    """Wrapper function for locally translating constants."""
    return QCoreApplication.translate("Constant", text)


class MediaType(Enum):

    VIDEO = 0
    AUDIO = 1
    SUBS  = 2
    OTHER = 4


class GuiLabels:

    MEDIA_TYPES: Final[dict[MediaType, str]] = {
        MediaType.VIDEO: QT_TRANSLATE_NOOP("Constant", "Video"),
        MediaType.AUDIO: QT_TRANSLATE_NOOP("Constant", "Audio"),
        MediaType.SUBS:  QT_TRANSLATE_NOOP("Constant", "Subtitles"),
        MediaType.OTHER: QT_TRANSLATE_NOOP("Constant", "Other"),
    }
