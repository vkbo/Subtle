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

from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)


class SubtitlesBase(ABC):

    def __init__(self) -> None:
        self._path: Path | None = None
        self._frames: list[FrameBase] = []
        return

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: id={id(self)}>"

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

    @abstractmethod
    def copyFrames(self, other: SubtitlesBase) -> None:
        raise NotImplementedError

    def copyText(self, other: SubtitlesBase) -> None:
        """Copy text elements from other subtitle."""
        frames = {f.start: f for f in self._frames}
        missing: list[FrameBase] = []
        for source in other.iterFrames():
            if text := source.text:
                if (start := source.start) in frames:
                    frames[start].setText(text)
                else:
                    missing.append(source)

        if missing:
            logger.info("Found %d subtitles with non-matching timestamps", len(missing))
            for frame in missing:
                for offset in (-2, -1, 1, 2):
                    if (pos := frame.start + offset) in frames:
                        frames[pos].setText(frame.text)

        return

    def _copyFrames(self, frameType: type[FrameBase], other: SubtitlesBase) -> None:
        """Copy frame content from other class. Must be implemented in
        subclasses by passing its own FrameBase implementation as
        frameType.
        """
        self._frames = [
            frameType.fromFrame(n, frame) for n, frame in enumerate(other.iterFrames())
        ]
        return


class FrameBase(ABC):

    def __init__(self, index: int) -> None:
        self._index: int = index
        self._start: int = -1
        self._end: int = -1
        self._text: list[str] = []
        return

    @classmethod
    @abstractmethod
    def fromFrame(cls, index: int, other: FrameBase) -> FrameBase:
        """Copy another frame."""
        raise NotImplementedError

    @property
    def index(self) -> int:
        """The frame's lookup index."""
        return self._index

    @property
    def start(self) -> int:
        """Frame start time."""
        return self._start

    @property
    def end(self) -> int:
        """Frame end time."""
        return self._end

    @property
    def length(self) -> int:
        """Frame length."""
        return self._end - self._start

    @property
    def text(self) -> list[str]:
        """Frame text."""
        return self._text

    @property
    @abstractmethod
    def imageBased(self) -> bool:
        """Check if image-based."""
        raise NotImplementedError

    def setText(self, text: list[str]) -> None:
        """Set the frame's text."""
        self._text = [t.strip() for t in text if t.strip()]
        return

    @abstractmethod
    def getImage(self) -> QImage:
        """Extract the subtitles image."""
        raise NotImplementedError
