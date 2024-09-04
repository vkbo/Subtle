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
from subtle.core.mediafile import MediaFile
from subtle.core.mkvextract import MkvExtract

from PyQt6.QtCore import QModelIndex, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QProgressBar, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)

logger = logging.getLogger(__name__)


class GuiMediaView(QWidget):

    C_TRACK   = 0
    C_TYPE    = 1
    C_CODEC   = 2
    C_LANG    = 3
    C_LENGTH  = 4
    C_FRAMES  = 5
    C_LABEL   = 6
    C_ENABLED = 7
    C_DEFAULT = 8
    C_FORCED  = 9

    newTrackAvailable = pyqtSignal(Path, dict)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._current: MediaFile | None = None
        self._extract = MkvExtract(self)

        self._trackInfo: dict | None = None
        self._trackFile: Path | None = None
        self._extractedTracks: dict[str, Path] = {}

        self._trUnknown = self.tr("Unknown")
        self._trYes = self.tr("Yes")

        self.tracksView = QTreeWidget(self)
        self.tracksView.setIndentation(0)
        self.tracksView.setHeaderLabels([
            "#", self.tr("Type"), self.tr("Codec"), self.tr("Lang"), self.tr("Length"),
            self.tr("Frames"), self.tr("Label"), self.tr("Enabled"), self.tr("Default"),
            self.tr("Forced"),
        ])
        self.tracksView.doubleClicked.connect(self._itemDoubleClicked)

        columns = self.tracksView.columnCount()
        for i, w in enumerate(CONFIG.getSizes("mediaViewColumns")):
            if i < columns:
                self.tracksView.setColumnWidth(i, w)

        # Progress
        self.progressText = QLabel(self.tr("No file selected ..."), self)
        self.progressBar = QProgressBar(self)

        # Controls
        self.extractButton = QPushButton(self.tr("Extract"))
        self.extractButton.clicked.connect(self._extractTracks)

        # Assemble
        self.controlsBox = QHBoxLayout()
        self.controlsBox.addWidget(self.progressBar, 1)
        self.controlsBox.addWidget(self.extractButton, 0)

        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.tracksView)
        self.outerBox.addWidget(self.progressText)
        self.outerBox.addLayout(self.controlsBox)

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
            self.tracksView.columnWidth(i) for i in range(self.tracksView.columnCount())
        ])
        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(Path)
    def setCurrentFile(self, file: Path) -> None:
        """Set the current file."""
        self._current = MediaFile(file)
        self._current._getInfo()
        self._listTracks()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _extractTracks(self) -> None:
        """Extract subtitle tracks from file."""
        if self._current:
            self._extractedTracks.clear()
            tracks = []
            for track in self._current.iterTracks():
                if track.get("type", "").lower() == "subtitles" and (idx := str(track.get("id"))):
                    tracks.append((idx, self._current.dumpFile(idx)))

            self.progressText.setText(self.tr("Extracting {0} tracks ...").format(len(tracks)))
            self.progressBar.setValue(0)

            self._extract.extract(self._current.filePath, tracks)
            self._extractedTracks = dict(tracks)

        return

    @pyqtSlot(QModelIndex)
    def _itemDoubleClicked(self, index: QModelIndex) -> None:
        """Process track double click in the media view."""
        if self._current and (item := self.tracksView.itemFromIndex(index)):
            track = item.text(self.C_TRACK)
            if track in self._extractedTracks:
                self.newTrackAvailable.emit(
                    self._extractedTracks.get(track), self._current.getTrackInfo(track)
                )
        return

    @pyqtSlot(int)
    def _extractProgress(self, value: int) -> None:
        """Process track extraction progress count."""
        self.progressBar.setValue(value)
        return

    @pyqtSlot()
    def _extractFinished(self) -> None:
        """Process track extraction finished."""
        self.progressText.setText(self.tr("Extraction complete"))
        return

    ##
    #  Internal Functions
    ##

    def _listTracks(self) -> None:
        """"""
        self.tracksView.clear()
        if isinstance(self._current, MediaFile):
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

                self.tracksView.addTopLevelItem(item)
        return
