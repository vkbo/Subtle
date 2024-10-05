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
import re

from pathlib import Path
from typing import NamedTuple

from subtle.common import closeItalics, decodeTS, regexCleanup
from subtle.formats.base import FrameBase, SubtitlesBase

from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)

RX_REPLACE = [
    (re.compile(r"(\{\\[ub]1\})", re.UNICODE), "<i>"),
    (re.compile(r"(\{\\[ub]0\})", re.UNICODE), "</i>"),
    (re.compile(r"(\{\\.+?\})", re.UNICODE), ""),
]


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
        self._frames = []
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
            self._frames.append(SSAFrame(
                len(self._frames),
                decodeTS(bits[fmt.start], fmt="SSA"),
                decodeTS(bits[fmt.end], fmt="SSA"),
                self._processText(bits[fmt.text]),
            ))
        else:
            logger.error("Dialogue entry is malformed on line %d", self._line)
        return

    def _processText(self, text: str) -> list[str]:
        """Process SSA dialogue format and preserve supported syntax."""
        temp = text.replace(r"\n", " ").replace(r"\h", " ")
        temp = temp.replace(r"{\i1}", "<i>").replace(r"{\i0}", "</i>")

        # Strip or replace other formatting
        fixed = regexCleanup(temp, RX_REPLACE)
        if fixed != temp:
            logger.debug("Rx Before: '%s'", temp.replace("\n", "|"))
            logger.debug("Rx Result: '%s'", fixed.replace("\n", "|"))

        return closeItalics(fixed.split(r"\N"))


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
