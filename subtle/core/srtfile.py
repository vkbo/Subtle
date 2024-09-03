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

from collections.abc import Iterable
from pathlib import Path

from subtle.common import checkInt, formatTS

logger = logging.getLogger(__name__)


class SRTReader:

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[int, tuple[str, str, list[str]]] = {}
        self._readData()
        return

    def iterBlocks(self) -> Iterable[tuple[int, str, str, list[str]]]:
        """Iterate through blocks."""
        for num, (start, end, text) in self._data.items():
            if num >= 0:
                yield num, start, end, text
        return

    def _readData(self) -> bool:
        """Read SRT info from file."""
        try:
            with open(self._path, mode="r", encoding="utf-8") as fo:
                block = []
                for line in fo:
                    if line := line.strip():
                        block.append(line)
                    else:
                        self._addBlock(block)
                        block = []
        except Exception as exc:
            logger.error("Could not read SRT file: %s", self._path, exc_info=exc)
            return False
        return True

    def _addBlock(self, block: list[str]) -> None:
        """Add a new frame to internal data."""
        if len(block) > 2:
            num = checkInt(block[0], -1)
            start, _, end = block[1].partition(" --> ")
            text = block[2:]
            self._data[num] = (start, end, text)
        return


class SRTWriter:

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: list[tuple[float, float, list[str]]] = []
        return

    def addBlock(self, start: float, end: float, text: list[str]) -> bool:
        """Add a subtitles frame if the timestamps are ok."""
        if start >= 0.0 and end > start:
            self._data.append((start, end, text))
        else:
            logger.warning("Skipping invalid subtitle timestamps start=%.3f end=%.3f", start, end)
            return False
        return True

    def write(self) -> bool:
        """Writer SRT data to file."""
        try:
            with open(self._path, mode="w", encoding="utf-8") as fo:
                prev = -1.0
                for i, (start, end, text) in enumerate(self._data, 1):
                    if start > prev and text:
                        fo.write(f"{i}\n{formatTS(start)} --> {formatTS(end)}\n")
                        fo.write("\n".join(text))
                        fo.write("\n\n")
                        prev = start
                    elif start <= prev:
                        logger.warning("Out of order text at t=%s", formatTS(start))
                    else:
                        logger.warning("Skipping entry with no text at t=%s", formatTS(start))
        except Exception as exc:
            logger.error("Could not write SRT file: %s", self._path, exc_info=exc)
            return False
        return True
