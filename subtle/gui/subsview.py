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
from subtle.common import formatTS
from subtle.core.pgsreader import DisplaySet, PGSReader
from subtle.core.srtfile import SRTWriter

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)

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
        self._mediaFile: Path | None = None
        self._trackFile: Path | None = None
        self._trackInfo: dict = {}
        self._map: dict[int, QTreeWidgetItem] = {}

        # Entries View
        self.subEntries = QTreeWidget(self)
        self.subEntries.setIndentation(0)
        self.subEntries.setHeaderLabels([
            "#", self.tr("Time Stamp"), self.tr("Length"), self.tr("Text")
        ])
        self.subEntries.clicked.connect(self._itemClicked)

        columns = self.subEntries.columnCount()
        for i, w in enumerate(CONFIG.getSizes("subsViewColumns")):
            if i < columns:
                self.subEntries.setColumnWidth(i, w)

        # Save SRT File
        self.saveLabel = QLabel(self.tr("Save SRT"), self)
        self.savePath = QLineEdit(self)

        self.saveForced = QCheckBox(self.tr("Forced"), self)
        self.saveForced.toggled.connect(self._toggleForceFlag)

        self.saveButton = QPushButton(self.tr("Save"), self)
        self.saveButton.clicked.connect(self._saveSRT)

        self.saveBox = QHBoxLayout()
        self.saveBox.addWidget(self.saveLabel, 0)
        self.saveBox.addWidget(self.savePath, 1)
        self.saveBox.addWidget(self.saveForced, 0)
        self.saveBox.addWidget(self.saveButton, 0)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.subEntries, 1)
        self.outerBox.addLayout(self.saveBox, 0)

        self.setLayout(self.outerBox)

        return

    ##
    #  Methods
    ##

    def saveSettings(self) -> None:
        """Save widget settings."""
        CONFIG.setSizes("subsViewColumns", [
            self.subEntries.columnWidth(i) for i in range(self.subEntries.columnCount())
        ])
        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(Path)
    def newFileSelected(self, path: Path) -> None:
        """Store the path to the selected file for later use."""
        self._mediaFile = path
        self.savePath.setText(str(path.with_suffix(".srt")))
        return

    @pyqtSlot(Path, dict)
    def loadTrack(self, path: Path, info: dict) -> None:
        """Load a new track, if possible."""
        match info.get("codec", ""):
            case "HDMV PGS":
                logger.info("Processing PGS subtitle file")
                self._reader = PGSReader(path)
                self._map.clear()
                self._updateTrackInfo(path, info)
                self.subEntries.clear()
                for entry in self._reader.listEntries():
                    tss = entry.get("start", 0.0)
                    tse = entry.get("end", 0.0)
                    num = entry.get("num", -1)
                    if not entry.get("clear", False):
                        item = QTreeWidgetItem()
                        item.setText(self.C_ID, str(self.subEntries.topLevelItemCount()))
                        item.setText(self.C_TIME, formatTS(tss))
                        item.setText(self.C_LENGTH, f"{tse - tss:.3f}")
                        item.setData(self.C_DATA, self.D_INDEX, entry.get("index", -1))
                        item.setData(self.C_DATA, self.D_START, tss)
                        item.setData(self.C_DATA, self.D_END, tse)
                        self.subEntries.addTopLevelItem(item)
                        self._map[num] = item
        return

    @pyqtSlot(DisplaySet)
    def updateText(self, ds: DisplaySet) -> None:
        """Update text for a specific display set."""
        if item := self._map.get(ds.pcs.compNumber):
            self._updateItemText(item, ds.text)
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _itemClicked(self, index: QModelIndex) -> None:
        """Process track double click in the media view."""
        if self._reader and (item := self.subEntries.itemFromIndex(index)):
            if ds := self._reader.displaySet(item.data(self.C_DATA, self.D_INDEX)):
                self.displaySetSelected.emit(index.row(), ds)
        return

    @pyqtSlot(bool)
    def _toggleForceFlag(self, state: bool) -> None:
        """Update forced status."""
        if self._trackFile and self._trackInfo:
            self._updateTrackInfo(self._trackFile, self._trackInfo, state)
        return

    @pyqtSlot()
    def _saveSRT(self) -> None:
        """Save the processed subtitles to an SRT file."""
        writer = SRTWriter(Path(self.savePath.text()))
        for i in range(self.subEntries.topLevelItemCount()):
            if item := self.subEntries.topLevelItem(i):
                start = item.data(self.C_DATA, self.D_START)
                end = item.data(self.C_DATA, self.D_END)
                text = item.data(self.C_DATA, self.D_TEXT)
                if isinstance(start, float) and isinstance(end, float) and isinstance(text, list):
                    writer.addBlock(start, end, text)
        writer.write()
        return

    ##
    #  Internal Functions
    ##

    def _updateTrackInfo(self, path: Path, info: dict, force: bool | None = None) -> None:
        """Update info about the current track."""
        self._trackFile = path
        self._trackInfo = info
        if isinstance(props := info.get("properties", {}), dict) and (media := self._mediaFile):
            lang = str(props.get("language", "und"))
            forced = bool(props.get("forced_track", False)) if force is None else force
            flags = ".forced" if forced else ""
            self.savePath.setText(str(media.parent / f"{media.stem}.{lang}{flags}.srt"))
            self.saveForced.setChecked(forced)
        return

    def _updateItemText(self, item: QTreeWidgetItem, text: list[str]) -> None:
        """Update the subtitle text for a given item."""
        item.setText(self.C_TEXT, "\u21b2".join(text))
        item.setData(self.C_DATA, self.D_TEXT, text)
        return
