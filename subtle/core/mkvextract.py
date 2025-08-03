"""
Subtle – Process Wrapper Component
==================================

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

from typing import TYPE_CHECKING

from subtle.common import checkInt

from PyQt6.QtCore import QObject, QProcess, pyqtSignal, pyqtSlot

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class MkvExtract(QObject):

    processProgress = pyqtSignal(int)
    processDone = pyqtSignal(int)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent=parent)
        self._process = None
        self._pid = 0
        return

    def extract(self, file: Path, tracks: list[tuple[str, Path]]) -> None:
        """Start a subprocess running mkvextract."""
        if self._process is None:
            args = ["--gui-mode", "tracks", str(file)]
            args.extend(f"{i}:{p}" for i, p in tracks)
            self._process = QProcess(self)
            self._process.readyReadStandardOutput.connect(self._processStdOut)
            self._process.finished.connect(self._processFinished)
            self._process.start("mkvextract", args)
            self._pid = self._process.processId()
            logger.debug("Starting process %d", self._pid)
        return

    def cancel(self) -> None:
        """Cancel the process."""
        if isinstance(self._process, QProcess):
            logger.debug("Killing process %d", self._pid)
            self._process.kill()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _processStdOut(self) -> None:
        """Send update GUI signal when process prints output."""
        if self._process:
            text = self._process.readAllStandardOutput().data().decode("utf-8").strip()
            if text.startswith("#GUI#progress"):
                self.processProgress.emit(checkInt(text[13:].strip().removesuffix("%"), 0))
        return

    @pyqtSlot()
    def _processFinished(self) -> None:
        """Send finish signal when process exits."""
        if self._process:
            code = self._process.exitCode()
            logger.debug("Process %d exited with return code %d", self._pid, code)
            self.processDone.emit(code)
            self._process = None
        return
