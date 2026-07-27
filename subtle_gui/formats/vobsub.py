"""
Subtle - VobSub File Object
===========================

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

from typing import TYPE_CHECKING, NamedTuple

from subtle_gui.common import decodeTS
from subtle_gui.formats.base import FrameBase, SubtitlesBase

if TYPE_CHECKING:
    from pathlib import Path

    from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)


class IdxEntry(NamedTuple):
    """An entry in a VobSub IDX file."""

    timestamp: int
    filepos: int


class VobSubs(SubtitlesBase):
    """VobSub Subtitles."""

    def __init__(self) -> None:
        super().__init__()

        # IDX Data
        self._idx: list[IdxEntry] = []
        self._forced: bool = False
        self._palette: list[str] = []

    def read(self, path: Path) -> None:
        """Read a VobSub file."""
        self._path = path.with_suffix(".sub")
        try:
            self._readIdxData(path.with_suffix(".idx"))
        except Exception as exc:
            logger.error("Could not read VobSub IDX file: %s", self._path, exc_info=exc)

    def write(self, path: Path | None = None) -> None:
        """Write a VobSub file."""
        raise NotImplementedError("Cannot write VobSub files.")

    def copyFrames(self, other: SubtitlesBase) -> None:
        """Copy frames from another subtitle object."""
        return super()._copyFrames(VobSubFrame, other)

    ##
    #  Internal Functions
    ##

    def _readIdxData(self, path: Path) -> None:
        """Read IDX data from file."""
        self._idx = []
        with open(path, mode="r", encoding="utf-8") as fo:
            for line in fo:
                if line.startswith("timestamp:"):
                    one, _, two = line.partition(",")
                    ts = decodeTS(one.partition(":")[2].strip(), fmt="IDX")
                    fp = int("0x" + two.partition(":")[2].strip(), 16)
                    self._idx.append(IdxEntry(timestamp=ts, filepos=fp))
                elif line.startswith("forced subs:"):
                    self._forced = line.partition(":")[2].strip().lower() == "on"
                elif line.startswith("palette:"):
                    self._palette = [p.strip() for p in line.partition(":")[2].split(",")]

        print(self._idx[:10])

    def _readSubData(self, path: Path) -> None:
        """Read SUB data from file."""


class VobSubFrame(FrameBase):
    """VobSub Subtitle Frame."""

    def __init__(self, index: int, start: int, end: int, text: list[str]) -> None:
        super().__init__(index=index)
        self._start = start
        self._end = end
        self._text = text

    @classmethod
    def fromFrame(cls, index: int, other: FrameBase) -> FrameBase:
        """Populate from another frame."""
        return cls(index, other.start, other.end, other.text)

    @property
    def imageBased(self) -> bool:
        """VobSub frames are images."""
        return True

    def getImage(self) -> QImage:
        """There is no image."""
        raise NotImplementedError
