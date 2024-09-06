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

from subtle import CONFIG, SHARED
from subtle.common import formatTS
from subtle.constants import GuiLabels, MediaType, trConst
from subtle.core.media import MediaTrack
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

    newTrackSelection = pyqtSignal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._extract = MkvExtract(self)
        self._extracted: dict[str, Path] = {}
        self._map: dict[str, QTreeWidgetItem] = {}
        self._emitTrack: str | None = None

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
        self.extractButton = QPushButton(self.tr("Extract All"))
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

    @pyqtSlot()
    def processNewMediaLoaded(self) -> None:
        """Process new media signal."""
        self._map.clear()
        self._extracted.clear()
        self.tracksView.clear()
        self.progressBar.setValue(0)
        self.progressText.setText(self.tr("Ready"))
        for track in SHARED.media.iterTracks():
            item = QTreeWidgetItem()
            self._setTrackInfo(track, item)
            self.tracksView.addTopLevelItem(item)
            self._map[track.trackID] = item
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _extractTracks(self) -> None:
        """Extract subtitle tracks from file."""
        if file := SHARED.media.mediaFile:
            tracks = []
            for track in SHARED.media.iterTracks():
                if track.trackType == MediaType.SUBS and (idx := track.trackID):
                    if idx not in self._extracted:
                        path = file.dumpFile(idx)
                        tracks.append((idx, path))
                        track.setTrackFile(path)
            self._runTrackExtraction(file.filePath, tracks)
        return

    @pyqtSlot(QModelIndex)
    def _itemDoubleClicked(self, index: QModelIndex) -> None:
        """Process track double click in the media view."""
        if (file := SHARED.media.mediaFile) and (item := self.tracksView.itemFromIndex(index)):
            idx = item.text(self.C_TRACK)
            if idx not in self._extracted:
                if (track := SHARED.media.getTrack(idx)) and track.trackType == MediaType.SUBS:
                    path = file.dumpFile(idx)
                    track.setTrackFile(path)
                    self._runTrackExtraction(file.filePath, [(idx, path)])
                    self._emitTrack = idx
            if idx in self._extracted:
                self.newTrackSelection.emit(idx)
        return

    @pyqtSlot(int)
    def _extractProgress(self, value: int) -> None:
        """Process track extraction progress count."""
        self.progressBar.setValue(value)
        return

    @pyqtSlot()
    def _extractFinished(self) -> None:
        """Process track extraction finished."""
        self.progressText.setText(self.tr("Reading tracks ..."))
        for idx in self._extracted:
            if track := SHARED.media.getTrack(idx):
                track.readTrackFile()
                self._setTrackInfo(track)

        self.progressText.setText(self.tr("Extraction complete"))
        if self._emitTrack:
            # Emit delayed new track signal
            self.newTrackSelection.emit(self._emitTrack)
            self._emitTrack = None

        return

    ##
    #  Internal Functions
    ##

    def _setTrackInfo(self, track: MediaTrack, item: QTreeWidgetItem | None = None) -> None:
        """Set the info for a media track."""
        if item is None:
            item = self._map.get(track.trackID, None)
        if item is not None:
            item.setText(self.C_TRACK, track.trackID)
            item.setText(self.C_TYPE, trConst(GuiLabels.MEDIA_TYPES[track.trackType]))
            item.setText(self.C_CODEC, track.codecName)
            item.setText(self.C_LANG, track.language)
            item.setText(self.C_LENGTH, formatTS(track.duration)[:8])
            item.setText(self.C_FRAMES, str(track.frames) if track.frames > 0 else "")
            item.setText(self.C_LABEL, track.label)
            item.setText(self.C_ENABLED, self._trYes if track.enabled else "")
            item.setText(self.C_DEFAULT, self._trYes if track.default else "")
            item.setText(self.C_FORCED, self._trYes if track.forced else "")
        return

    def _runTrackExtraction(self, path: Path, tracks: list[tuple[str, Path]]) -> None:
        """Call for extraction for a set of tracks."""
        self.progressText.setText(self.tr("Extracting {0} track(s) ...").format(len(tracks)))
        self.progressBar.setValue(0)
        self._extract.extract(path, tracks)
        self._extracted.update(tracks)
        return
