"""
Subtle – SSA File Object
========================

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

from pathlib import Path
from typing import NamedTuple

from subtle.common import decodeTS
from subtle.formats.base import FrameBase, SubtitlesBase

from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)


class EventFormat(NamedTuple):

    length: int
    start: int
    end: int
    text: int


class SSASubs(SubtitlesBase):

    def __init__(self) -> None:
        super().__init__()
        self._format: EventFormat | None = None
        self._line = -1
        return

    def read(self, path: Path) -> None:
        """Read a PGS file."""
        try:
            self._readData(path)
            self._path = path
        except Exception as e:
            logger.error("Failed to read file data", exc_info=e)
        return

    def write(self, path: Path | None = None) -> None:
        """Write a PGS file."""
        raise NotImplementedError("Cannot write PGS files.")

    def copyFrames(self, other: SubtitlesBase) -> None:
        return super()._copyFrames(SSAFrame, other)

    ##
    #  Internal Functions
    ##

    def _readData(self, path: Path) -> None:
        """Read SubStation Alpha text file data."""
        with open(path, mode="r", encoding="utf-8") as fo:
            parse = False
            for line in fo:
                self._line += 1
                if (line := line.strip()) == "[Events]":
                    parse = True
                elif parse:
                    if line.startswith("Dialogue:"):
                        self._parseDialogue(line[9:])
                    elif line.startswith("Format:"):
                        self._parseFormat(line[7:])
        return

    def _parseFormat(self, line: str) -> None:
        """Parse dialogue format."""
        parts = [f.strip() for f in line.split(",")]
        try:
            self._format = EventFormat(
                len(parts),
                parts.index("Start"),
                parts.index("End"),
                parts.index("Text")
            )
            print(self._format)
        except ValueError:
            logger.error("Invalid events format string")
        return

    def _parseDialogue(self, line: str) -> None:
        """Parse a dialogue entry."""
        if self._format is None:
            logger.error("Dialogue before format, skipping line %d", self._line)
            return
        fmt = self._format
        bits = line.split(",", fmt.length - 1)
        if len(bits) == fmt.length:
            start = decodeTS(bits[fmt.start])
            end = decodeTS(bits[fmt.end])
            text = bits[fmt.text]
            print(start, end, text)
        else:
            logger.error("Dialogue entry is malformed on line %d", self._line)
        return


class SSAFrame(FrameBase):

    def __init__(self, index: int, start: int, end: int, text: list[str]) -> None:
        super().__init__(index=index)
        self._start = start
        self._end = end
        self._text = text
        return

    @classmethod
    def fromFrame(cls, index: int, other: FrameBase) -> FrameBase:
        """Populate from another frame."""
        return cls(index, other.start, other.end, other.text)

    @property
    def imageBased(self) -> bool:
        """SRT frames are not images."""
        return False

    def getImage(self) -> QImage:
        """There is no image."""
        raise NotImplementedError
