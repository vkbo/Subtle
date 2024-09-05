"""
Subtle – Subtitles Base
=======================

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

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

logger = logging.getLogger(__name__)


class SubtitlesBase(ABC):

    def __init__(self) -> None:
        self._path: Path | None = None
        self._frames: list[FrameBase] = []
        return

    def frameCount(self) -> int:
        """Return number of frames."""
        return len(self._frames)

    def getFrame(self, index: int) -> FrameBase | None:
        """Return a subtitles frame."""
        if 0 <= index < len(self._frames):
            return self._frames[index]
        return None

    def iterFrames(self) -> Iterable[FrameBase]:
        """Iterate over frames."""
        yield from self._frames

    @abstractmethod
    def read(self, path: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    def write(self, path: Path | None = None) -> None:
        raise NotImplementedError


class FrameBase(ABC):

    def __init__(self, index: int) -> None:
        self._index: int = index
        self._start: float = -1.0
        self._end: float = -1.0
        self._text: list[str] = []
        return

    @property
    def index(self) -> int:
        """The frame's lookup index."""
        return self._index

    @property
    def start(self) -> float:
        """Frame start time."""
        return self._start

    @property
    def end(self) -> float:
        """Frame end time."""
        return self._end

    @property
    def text(self) -> list[str]:
        """Frame text."""
        return self._text

    def setText(self, text: list[str]) -> None:
        """Set the frame's text."""
        self._text = text
        return
