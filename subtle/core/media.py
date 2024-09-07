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

from collections.abc import Iterable
from pathlib import Path

from subtle.common import decodeTS
from subtle.constants import MediaType
from subtle.core.mediafile import MediaFile
from subtle.formats.base import FrameBase, SubtitlesBase
from subtle.formats.pgssubs import PGSSubs

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class MediaData(QObject):

    mediaDataCleared = pyqtSignal()
    newMediaLoaded = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._tracks: dict[str, MediaTrack] = {}
        self._file: MediaFile | None = None
        return

    @property
    def hasMedia(self) -> bool:
        """Return True if media is loaded."""
        return self._file is not None

    @property
    def mediaFile(self) -> MediaFile | None:
        """Return the media file object."""
        return self._file

    def clear(self) -> None:
        """Clear the data object."""
        self._tracks.clear()
        self._file = None
        self.mediaDataCleared.emit()
        return

    def loadMediaFile(self, path: Path) -> None:
        """Load a media file into the data store."""
        logger.debug("Loading file: %s", path)
        self.clear()
        media = MediaFile(path)
        if media.valid:
            self._file = media
            for info in media.iterTracks():
                track = MediaTrack(self, info)
                if idx := track.trackID:
                    self._tracks[idx] = track
            self.newMediaLoaded.emit()
        return

    def iterTracks(self) -> Iterable[MediaTrack]:
        """Iterate through all tracks."""
        yield from self._tracks.values()

    def getTrack(self, trackID: str) -> MediaTrack | None:
        """Return a track object."""
        return self._tracks[trackID]


class MediaTrack:

    def __init__(self, media: MediaData, info: dict) -> None:
        self._media = media
        self._info = {}
        self._props = {}
        self._path: Path | None = None
        self._wrapper: SubtitlesBase | None = None

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

        if self._type == MediaType.SUBS:
            match self._props.get("codec_id"):
                case "S_HDMV/PGS":
                    self._wrapper = PGSSubs()

        return

    ##
    #  Properties
    ##

    @property
    def trackID(self) -> str:
        """Return the track's ID."""
        return str(self._info.get("id", ""))

    @property
    def trackType(self) -> MediaType:
        """Return the track's type."""
        return self._type

    @property
    def label(self) -> str:
        """Return the track's label."""
        return str(self._props.get("track_name", ""))

    @property
    def language(self) -> str:
        """Return the track's language."""
        return str(self._props.get("language", "und"))

    @property
    def frames(self) -> int:
        """Return the track's frame count."""
        if self._wrapper:
            return self._wrapper.frameCount()
        return -1

    @property
    def default(self) -> bool:
        """Return the track's default track flag."""
        return bool(self._props.get("default_track", False))

    @property
    def enabled(self) -> bool:
        """Return the track's enabled track flag."""
        return bool(self._props.get("enabled_track", False))

    @property
    def forced(self) -> bool:
        """Return the track's forced track flag."""
        return bool(self._props.get("forced_track", False))

    @property
    def codecName(self) -> str:
        """Return the track's codec."""
        return str(self._info.get("codec", "Unknown"))

    @property
    def codecID(self) -> str:
        """Return the track's codec."""
        return str(self._props.get("codec_id", "NONE"))

    @property
    def duration(self) -> int:
        """Return the track's duration."""
        return decodeTS(self._props.get("tag_duration"))

    ##
    #  Methods
    ##

    def setTrackFile(self, path: Path) -> None:
        """Set the extraction location of the track file."""
        self._path = path
        return

    def readTrackFile(self) -> None:
        """Read the content of the track file."""
        if self._path and self._wrapper:
            self._wrapper.read(self._path)
        return

    def getFrame(self, index: int) -> FrameBase | None:
        """Return a subtitles frame."""
        if self._wrapper:
            return self._wrapper.getFrame(index)
        return None

    def iterFrames(self) -> Iterable[FrameBase]:
        """Iterate over frames."""
        if self._wrapper:
            yield from self._wrapper.iterFrames()
        return

    def copyFrames(self, target: SubtitlesBase) -> None:
        """Copy all frames from current track to target."""
        if self._wrapper:
            target.copyFrames(self._wrapper)
        return
