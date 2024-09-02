"""
Subtle – GUI Media View
=======================

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
from subtle.common import formatInt
from subtle.core.mkvextract import MkvExtract
from subtle.core.mkvfile import MkvFile

from PyQt6.QtCore import QModelIndex, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QLabel, QProgressBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

logger = logging.getLogger(__name__)


class GuiMediaView(QWidget):

    C_TRACK   = 0
    C_TYPE    = 1
    C_CODEC   = 2
    C_LANG    = 3
    C_LENGTH  = 4
    C_LABEL   = 5
    C_ENABLED = 6
    C_DEFAULT = 7
    C_FORCED  = 8

    newTrackAvailable = pyqtSignal(Path, dict)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._current: MkvFile | None = None
        self._extract = MkvExtract(self)

        self._trackInfo: dict | None = None
        self._trackFile: Path | None = None

        self._trUnknown = self.tr("Unknown")
        self._trYes = self.tr("Yes")

        self._tracks = QTreeWidget(self)
        self._tracks.setIndentation(0)
        self._tracks.setHeaderLabels([
            "#", self.tr("Type"), self.tr("Codec"), self.tr("Lang"), self.tr("Length"),
            self.tr("Label"), self.tr("Enabled"), self.tr("Default"), self.tr("Forced"),
        ])
        self._tracks.doubleClicked.connect(self._itemDoubleClicked)

        columns = self._tracks.columnCount()
        for i, w in enumerate(CONFIG.getSizes("mediaViewColumns")):
            if i < columns:
                self._tracks.setColumnWidth(i, w)

        # Progress
        self._progressText = QLabel(self)
        self._progressBar = QProgressBar(self)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self._tracks)
        self.outerBox.addWidget(self._progressText)
        self.outerBox.addWidget(self._progressBar)

        self.setLayout(self.outerBox)

        # Connect Signals
        self._extract.processProgress.connect(self._extractProgress)
        self._extract.processDone.connect(self._extractFinished)

        return

    ##
    #  Methods
    ##

    def saveSettings(self) -> None:
        """Save widget settings."""
        CONFIG.setSizes("mediaViewColumns", [
            self._tracks.columnWidth(i) for i in range(self._tracks.columnCount())
        ])
        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(Path)
    def setCurrentFile(self, file: Path) -> None:
        """Set the current file."""
        self._current = MkvFile(file)
        self._current.getInfo()
        self._listTracks()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _itemDoubleClicked(self, index: QModelIndex) -> None:
        """Process track double click in the media view."""
        if self._current and (item := self._tracks.itemFromIndex(index)):
            track = item.text(self.C_TRACK)
            mkvFile = self._current.filePath
            outFile = self._current.dumpFile(track)

            self._progressText.setText("Extracting ...")
            self._progressBar.setValue(0)

            self._trackInfo = self._current.getTrackInfo(track)
            self._trackFile = outFile
            self._extract.extract(mkvFile, track, outFile)

        return

    @pyqtSlot(int)
    def _extractProgress(self, value: int) -> None:
        """Process track extraction progress count."""
        if (file := self._trackFile) and (info := self._trackInfo):
            tID    = str(info.get("id", "-"))
            tType  = info.get("type", self._trUnknown).title()
            tCodec = info.get("codec", self._trUnknown)
            tSize  = formatInt(file.stat().st_size)
            self._progressText.setText(f"Extracting Track {tID}: {tType} ({tCodec}) - {tSize}B")
            self._progressBar.setValue(value)
        return

    @pyqtSlot()
    def _extractFinished(self) -> None:
        """Process track extraction finished."""
        if (file := self._trackFile) and (info := self._trackInfo):
            self.newTrackAvailable.emit(file, info)
        return

    ##
    #  Internal Functions
    ##

    def _listTracks(self) -> None:
        """"""
        self._tracks.clear()
        if isinstance(self._current, MkvFile):
            for track in self._current.iterTracks():
                props = track.get("properties", {})

                tID      = str(track.get("id", "-"))
                tType    = track.get("type", self._trUnknown).title()
                tCodec   = track.get("codec", self._trUnknown)
                tLang    = props.get("language", "und")
                tLength  = props.get("tag_duration", "Unknown")[:8]
                tLabel   = props.get("track_name", "")
                tEnabled = self._trYes if props.get("enabled_track", False) else ""
                tDefault = self._trYes if props.get("default_track", False) else ""
                tForced  = self._trYes if props.get("forced_track", False) else ""

                item = QTreeWidgetItem()
                item.setText(self.C_TRACK, tID)
                item.setText(self.C_TYPE, tType)
                item.setText(self.C_CODEC, tCodec)
                item.setText(self.C_LANG, tLang)
                item.setText(self.C_LENGTH, tLength)
                item.setText(self.C_LABEL, tLabel)
                item.setText(self.C_ENABLED, tEnabled)
                item.setText(self.C_DEFAULT, tDefault)
                item.setText(self.C_FORCED, tForced)

                self._tracks.addTopLevelItem(item)
        return
