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

from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, pyqtSignal, pyqtSlot
from subtle.common import checkInt

logger = logging.getLogger(__name__)


class MkvExtract(QObject):

    processProgress = pyqtSignal(int)
    processDone = pyqtSignal(int)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent=parent)
        self._process = None
        self._pid = 0
        return

    def extract(self, file: Path, track: str | int, output: Path) -> None:
        """"""
        if self._process is None:
            self._process = QProcess(self)
            self._process.readyReadStandardOutput.connect(self._processStdOut)
            self._process.finished.connect(self._processFinished)
            self._process.start("mkvextract", [
                "--gui-mode", "tracks", str(file), f"{track}:{output}"
            ])
            self._pid = self._process.processId()
            logger.debug("Starting process %d", self._pid)
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _processStdOut(self) -> None:
        """"""
        if self._process:
            text = self._process.readAllStandardOutput().data().decode("utf-8").strip()
            if text.startswith("#GUI#progress"):
                self.processProgress.emit(checkInt(text[14:].rstrip("%"), 0))
        return

    @pyqtSlot()
    def _processFinished(self) -> None:
        """"""
        if self._process:
            code = self._process.exitCode()
            logger.debug("Ending process %d with return code %d", self._pid, code)
            self.processDone.emit(code)
            self._process = None
        return
