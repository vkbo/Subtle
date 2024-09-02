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

from subtle import CONFIG
from subtle.core.pgsreader import DisplaySet, PGSReader

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class GuiSubtitleView(QWidget):

    C_DATA   = 0
    C_ID     = 0
    C_TIME   = 1
    C_LENGTH = 2
    C_TEXT   = 3

    D_INDEX = Qt.ItemDataRole.UserRole
    D_START = Qt.ItemDataRole.UserRole + 1
    D_END   = Qt.ItemDataRole.UserRole + 2
    D_TEXT  = Qt.ItemDataRole.UserRole + 3

    displaySetSelected = pyqtSignal(int, DisplaySet)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._reader = None
        self._map: dict[int, QTreeWidgetItem] = {}

        self._frames = QTreeWidget(self)
        self._frames.setIndentation(0)
        self._frames.setHeaderLabels([
            "#", self.tr("TimeStamp"), self.tr("Length"), self.tr("Text")
        ])
        self._frames.clicked.connect(self._itemClicked)

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

    def setText(self, ds: DisplaySet, text: list[str]) -> None:
        """"""
        if item := self._map.get(ds.pcs.compNumber):
            item.setText(self.C_TEXT, "\u21b2".join(text))
            item.setData(self.C_DATA, self.D_TEXT, text)
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
                self._reader = PGSReader(path)
                self._frames.clear()
                self._map.clear()
                for entry in self._reader.listEntries():
                    tss = entry.get("start", 0.0)
                    tse = entry.get("end", 0.0)
                    num = entry.get("num", -1)
                    if not entry.get("clear", False):
                        item = QTreeWidgetItem()
                        item.setText(self.C_ID, str(self._frames.topLevelItemCount()))
                        item.setText(self.C_TIME, f"{tss:.3f}")
                        item.setText(self.C_LENGTH, f"{tse - tss:.3f}")
                        item.setData(self.C_DATA, self.D_INDEX, entry.get("index", -1))
                        item.setData(self.C_DATA, self.D_START, tss)
                        item.setData(self.C_DATA, self.D_END, tse)
                        self._frames.addTopLevelItem(item)
                        self._map[num] = item
                    # print(entry)
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _itemClicked(self, index: QModelIndex) -> None:
        """Process track double click in the media view."""
        if self._reader and (item := self._frames.itemFromIndex(index)):
            if ds := self._reader.displaySet(item.data(self.C_DATA, self.D_INDEX)):
                self.displaySetSelected.emit(index.row(), ds)
        return
