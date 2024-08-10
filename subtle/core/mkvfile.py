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
from pathlib import Path

logger = logging.getLogger(__name__)


class MKVFile:

    def __init__(self, file: Path) -> None:
        self._file = file
        self._info = {}
        return

    def loadFile(self) -> None:
        """Load info about the media file."""
        try:
            p = subprocess.Popen(["mkvmerge", "-J", str(self._file)], stdout=subprocess.PIPE)
            out, _ = p.communicate()
            self._info = json.loads(out.decode("utf-8"))
        except Exception as e:
            logger.error("Failed to load media file info", exc_info=e)
        return

    def tracks(self) -> Iterable[dict]:
        """"""
        yield from self._info.get("tracks", [])
