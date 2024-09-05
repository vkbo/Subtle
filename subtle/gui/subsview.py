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

from subtle import CONFIG, SHARED
from subtle.common import formatTS
from subtle.constants import MediaType
from subtle.core.media import MediaTrack
from subtle.formats.base import FrameBase

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

    subsFrameSelected = pyqtSignal(FrameBase)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._map: dict[int, QTreeWidgetItem] = {}
        self._track: MediaTrack | None = None

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

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.subEntries, 1)

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

    @pyqtSlot(str)
    def newTrackLoaded(self, idx: str) -> None:
        """Display subtitles for a given track."""
        if (track := SHARED.media.getTrack(idx)) and track.trackType == MediaType.SUBS:
            self._map.clear()
            self.subEntries.clear()
            self._track = track
            for frame in track.iterFrames():
                tss = frame.start
                tse = frame.end
                item = QTreeWidgetItem()
                item.setText(self.C_ID, str(self.subEntries.topLevelItemCount()))
                item.setText(self.C_TIME, formatTS(tss))
                item.setText(self.C_LENGTH, f"{tse - tss:.3f}")
                item.setData(self.C_DATA, self.D_INDEX, frame.index)
                self._map[frame.index] = item
                self._updateItemText(item, frame.text)
                self.subEntries.addTopLevelItem(item)
        return

    @pyqtSlot(FrameBase)
    def updateText(self, frame: FrameBase) -> None:
        """Update text for a specific frame."""
        if item := self._map.get(frame.index):
            self._updateItemText(item, frame.text)
        return

    @pyqtSlot(Path)
    def writeSrtFile(self, path: Path) -> None:
        """Save the processed subtitles to an SRT file."""
        # writer = SRTWriter(path)
        # for i in range(self.subEntries.topLevelItemCount()):
        #     if item := self.subEntries.topLevelItem(i):
        #         start = item.data(self.C_DATA, self.D_START)
        #         end = item.data(self.C_DATA, self.D_END)
        #         text = item.data(self.C_DATA, self.D_TEXT)
        #         writer.addBlock(start, end, text)
        # writer.write()
        return

    @pyqtSlot(Path)
    def readSubsFile(self, path: Path) -> None:
        """Read a subs file and update entries."""
        # if path.is_file() and path.suffix == ".srt" and self._reader:
        #     rdSrt = SRTReader(path)
        #     for num, _, _, text in rdSrt.iterBlocks():
        #         idx = num - 1
        #         if item := self.subEntries.topLevelItem(idx):
        #             if ds := self._reader.displaySet(item.data(self.C_DATA, self.D_INDEX)):
        #                 ds.setText(text)
        #                 self._updateItemText(item, text)
        return

    @pyqtSlot(int)
    def selectNearby(self, step: int) -> None:
        """Select a different display set."""
        if self._track and (items := self.subEntries.selectedItems()):
            index = items[0].data(self.C_DATA, self.D_INDEX) + step
            if item := self.subEntries.topLevelItem(index):
                self.subEntries.clearSelection()
                self.subEntries.scrollToItem(item)
                item.setSelected(True)
                if frame := self._track.getFrame(index):
                    self.subsFrameSelected.emit(frame)
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _itemClicked(self, index: QModelIndex) -> None:
        """Process item click in the subtitles list."""
        if self._track and (item := self.subEntries.itemFromIndex(index)):
            if frame := self._track.getFrame(item.data(self.C_DATA, self.D_INDEX)):
                self.subsFrameSelected.emit(frame)
        return

    ##
    #  Internal Functions
    ##

    def _updateItemText(self, item: QTreeWidgetItem, text: list[str]) -> None:
        """Update the subtitle text for a given item."""
        item.setText(self.C_TEXT, "\u21b2".join(text))
        return
