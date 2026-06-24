"""
Subtle – Subtitles Base
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

from subtle_gui.common import formatTS

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)


class SubtitlesBase(ABC):
    """Base class for subtitle formats."""

    __slots__ = ("_frames", "_path")

    def __init__(self) -> None:
        self._path: Path | None = None
        self._frames: list[FrameBase] = []

    def __repr__(self) -> str:
        """Return a string representation of the subtitle object."""
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

    def checkFrames(self) -> None:
        """Check all frames to ensure that time stamps make sense."""
        for i in range(len(self._frames) - 1):
            cf, nf = self._frames[i : i + 2]
            if cf.end < cf.start:
                te = cf.end
                ts = cf.start
                tn = nf.start - 90
                cf.setRange(end=max(ts + 90, tn))
                logger.warning(
                    "Correcting end time for frame %d to %s (%+.3fs from %+.3fs)",
                    i + 1,
                    formatTS(tn),
                    (tn - ts) / 1000.0,
                    (te - ts) / 1000.0,
                )

    @abstractmethod
    def read(self, path: Path) -> None:
        """Read subtitles from a file."""
        raise NotImplementedError

    @abstractmethod
    def write(self, path: Path | None = None) -> None:
        """Write subtitles to a file."""
        raise NotImplementedError

    @abstractmethod
    def copyFrames(self, other: SubtitlesBase) -> None:
        """Copy frames from another subtitle object."""
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

    def _copyFrames(self, frameType: type[FrameBase], other: SubtitlesBase) -> None:
        """Copy frame content from other class. Must be implemented in
        subclasses by passing its own FrameBase implementation as
        frameType.
        """
        self._frames = [frameType.fromFrame(n, frame) for n, frame in enumerate(other.iterFrames())]


class FrameBase(ABC):
    """Base class for subtitle frames."""

    __slots__ = ("_end", "_index", "_start", "_text")

    def __init__(self, index: int) -> None:
        self._index: int = index
        self._start: int = -1
        self._end: int = -1
        self._text: list[str] = []

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

    def setRange(self, *, start: int | None = None, end: int | None = None) -> None:
        """Update the start and end times."""
        if start:
            self._start = start
        if end:
            self._end = end

    @abstractmethod
    def getImage(self) -> QImage:
        """Extract the subtitles image."""
        raise NotImplementedError
