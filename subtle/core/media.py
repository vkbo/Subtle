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

from enum import Enum
from pathlib import Path

from subtle.core.mediafile import MediaFile

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class MediaType(Enum):

    VIDEO = 0
    AUDIO = 1
    SUBS  = 2
    OTHER = 4


class MediaData(QObject):

    mediaDataCleared = pyqtSignal()
    newMediaLoaded = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._tracks: dict[str, MediaTrack]
        self._file: MediaFile | None = None
        return

    def clear(self) -> None:
        """Clear the data object."""
        self._tracks.clear()
        self._file = None
        self.mediaDataCleared.emit()
        return

    def loadMediaFile(self, path: Path) -> None:
        """Load a media file into the data store."""
        media = MediaFile(path)
        if media.valid:
            self._file = media
            self.newMediaLoaded.emit()
            for info in media.iterTracks():
                print(info)
                # if idx
                # self._tracks[info]
                # track = MediaTrack(self, info)
        else:
            self._file = None
        return


class MediaTrack:

    def __init__(self, media: MediaData, info: dict) -> None:
        self._media = media
        self._info = {}
        self._props = {}

        if isinstance(info, dict):
            self._info = info
            if isinstance(props := info.get("properties", {}), dict):
                self._props = props

        match str(info.get("type", "")).lower():
            case "video":
                self._type = MediaType.VIDEO
            case "audio":
                self._type = MediaType.AUDIO
            case "subtitles":
                self._type = MediaType.SUBS
            case _:
                self._type = MediaType.OTHER
        return

    @property
    def trackID(self) -> str:
        """Return the track's ID."""
        return str(self._info.get("id", ""))

    @property
    def codeName(self) -> str:
        """Return the track's codec."""
        return str(self._info.get("codec", "Unknown"))

    def analyse(self, info: dict) -> None:
        """Analyse the track by parsing data from mkvmerge."""
        return
