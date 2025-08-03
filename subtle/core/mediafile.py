"""
Subtle – Core MKV File Object
=============================

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

import json
import logging
import subprocess

from enum import IntEnum
from hashlib import sha1
from typing import TYPE_CHECKING

from subtle import CONFIG

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

logger = logging.getLogger(__name__)


class ContainerType(IntEnum):

    UNKNOWN     = 0
    AVI         = 5
    MATROSKA    = 17
    MPEG_STREAM = 21
    OGM         = 23
    PGSSUP      = 24
    QUICKTIME   = 25
    SRT         = 27
    SSA_ASS     = 28
    VOBSUB      = 34


EXTRACTABLE = (
    ContainerType.AVI,
    ContainerType.MATROSKA,
    ContainerType.MPEG_STREAM,
    ContainerType.OGM,
    ContainerType.QUICKTIME,
)

SUBTITLE_FILE = (
    ContainerType.SRT,
    ContainerType.SSA_ASS,
    ContainerType.PGSSUP,
)


class MediaFile:
    """Media File Wrapper.

    Wraps a single media file and holds media info about it.
    """

    def __init__(self, file: Path) -> None:
        self._file = file
        self._id = sha1(bytes(file), usedforsecurity=False).hexdigest()
        self._info = {}
        self._process()
        return

    @property
    def filePath(self) -> Path:
        """The path to the MKV file."""
        return self._file

    @property
    def valid(self) -> bool:
        """True if the media file was read successfully."""
        return bool(self._info)

    @property
    def container(self) -> ContainerType:
        """Return the file's container type."""
        try:
            container = self._info["container"]["properties"]["container_type"]
            return ContainerType(container)
        except Exception:
            logger.error("Unknown or unsupported media type")
        return ContainerType.UNKNOWN

    @property
    def supported(self) -> bool:
        """True if the format is supported."""
        try:
            return self._info["container"]["supported"]
        except Exception:
            pass
        return False

    def getTrackInfo(self, track: str | int) -> dict:
        """Return information about a specific track."""
        for entry in self._info.get("tracks", []):
            if isinstance(entry, dict) and str(entry.get("id", "")) == str(track):
                return entry
        return {}

    def iterTracks(self) -> Iterable[dict]:
        """List all tracks in the MKV file."""
        yield from self._info.get("tracks", [])

    def dumpFile(self, track: int | str) -> Path:
        """Generate a file name for a track dump."""
        return CONFIG.dumpPath / f"{self._id}.{track}.tmp"

    def infoFile(self) -> Path:
        """Generate a file name for a info dump."""
        return CONFIG.dumpPath / f"{self._id}.info.json"

    ##
    #  Internal Functions
    ##

    def _process(self) -> None:
        """Load info about the media file."""
        try:
            p = subprocess.Popen(
                ["mkvmerge", "-J", str(self._file)],
                stdout=subprocess.PIPE,
            )
            out, _ = p.communicate()
            self._info = json.loads(out.decode("utf-8"))
            with open(self.infoFile(), mode="w", encoding="utf-8") as fo:
                json.dump(self._info, fo, indent=2)
        except Exception as e:
            logger.error("Failed to load media file info", exc_info=e)
            self._info = {}
        return
