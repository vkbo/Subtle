"""
Subtle – GUI Subtitle View
==========================

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

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QTreeWidget, QVBoxLayout, QWidget
from subtle import CONFIG

logger = logging.getLogger(__name__)


class GuiSubtitleView(QWidget):

    C_ID     = 0
    C_TIME   = 1
    C_LENGTH = 2
    C_TEXT   = 3

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._frames = QTreeWidget(self)
        self._frames.setHeaderLabels([
            "#", self.tr("TimeStamp"), self.tr("Length"), self.tr("Text")
        ])

        columns = self._frames.columnCount()
        for i, w in enumerate(CONFIG.getSizes("subsViewColumns")):
            if i < columns:
                self._frames.setColumnWidth(i, w)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self._frames)

        self.setLayout(self.outerBox)

        return

    ##
    #  Methods
    ##

    def saveSettings(self) -> None:
        """Save widget settings."""
        CONFIG.setSizes("subsViewColumns", [
            self._frames.columnWidth(i) for i in range(self._frames.columnCount())
        ])
        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(Path, dict)
    def loadTrack(self, path: Path, info: dict) -> None:
        """Load a new track, if possible."""
        match info.get("codec", ""):
            case "HDMV PGS":
                logger.info("Processing PGS subtitle file")
                print(path)
        return
