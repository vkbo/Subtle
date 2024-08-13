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

from collections.abc import Iterable
from hashlib import sha1
from pathlib import Path

from subtle import CONFIG

logger = logging.getLogger(__name__)


class MkvFile:

    def __init__(self, file: Path) -> None:
        self._file = file
        self._id = sha1(bytes(file), usedforsecurity=False).hexdigest()
        self._info = {}
        return

    @property
    def filePath(self) -> Path:
        """The path to the MKV file."""
        return self._file

    def getInfo(self) -> None:
        """Load info about the media file."""
        try:
            p = subprocess.Popen(
                ["mkvmerge", "-J", str(self._file)],
                stdout=subprocess.PIPE,
            )
            out, _ = p.communicate()
            self._info = json.loads(out.decode("utf-8"))
        except Exception as e:
            logger.error("Failed to load media file info", exc_info=e)
            self._info = {}
        return

    def getTrackInfo(self, track: str | int) -> dict:
        """"""
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
