"""
Subtle – SRT File Object
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

from subtle.common import closeItalics, decodeTS, formatTS, textCleanup
from subtle.formats.base import FrameBase, SubtitlesBase

from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)


class SRTSubs(SubtitlesBase):

    def __init__(self) -> None:
        super().__init__()
        return

    def read(self, path: Path) -> None:
        """Read SRT info from file."""
        try:
            self._readData(path)
            self._path = path
        except Exception as exc:
            logger.error("Could not read SRT file: %s", self._path, exc_info=exc)
        return

    def write(self, path: Path | None = None) -> None:
        """Writer SRT data to file."""
        try:
            if path is None:
                path = self._path
            if path:
                self._writeData(path)
        except Exception as exc:
            logger.error("Could not write SRT file: %s", self._path, exc_info=exc)
        return

    def copyFrames(self, other: SubtitlesBase) -> None:
        return super()._copyFrames(SRTFrame, other)

    ##
    #  Internal Functions
    ##

    def _readData(self, path: Path) -> None:
        """Read SRT text file data."""
        self._frames = []
        with open(path, mode="r", encoding="utf-8") as fo:
            block = []
            for line in fo:
                if line := line.strip():
                    block.append(line)
                else:
                    self._parseFrame(block)
                    block = []
        return

    def _writeData(self, path: Path) -> None:
        """Write SRT text to file."""
        with open(path, mode="w", encoding="utf-8") as fo:
            prev = -1.0
            index = 0
            skipped = 0
            for frame in self._frames:
                if frame.start > prev and frame.text:
                    index += 1
                    fo.write(f"{index}\n{formatTS(frame.start)} --> {formatTS(frame.end)}\n")
                    fo.write("\n".join(frame.text))
                    fo.write("\n\n")
                    prev = frame.start
                elif frame.start <= prev:
                    logger.warning("Out of order text at t=%s", formatTS(frame.start))
                else:
                    skipped += 1
            if skipped:
                logger.warning("Skipping %d entries with no text", skipped)
            logger.info("Saved %d subtitle entries to SRT file.", index)
        return

    def _parseFrame(self, block: list[str]) -> None:
        """Add a new frame to internal data."""
        if len(block) > 2:
            start, _, end = block[1].partition(" --> ")
            self._frames.append(
                SRTFrame(
                    len(self._frames),
                    decodeTS(start),
                    decodeTS(end),
                    closeItalics([textCleanup(t) for t in block[2:]]),
                )
            )
        return


class SRTFrame(FrameBase):

    def __init__(self, index: int, start: int, end: int, text: list[str]) -> None:
        super().__init__(index)
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
