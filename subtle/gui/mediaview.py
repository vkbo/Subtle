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

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from subtle import CONFIG
from subtle.core.mkvfile import MKVFile

logger = logging.getLogger(__name__)


class GuiMediaView(QWidget):

    C_TRACK   = 0
    C_TYPE    = 1
    C_CODEC   = 2
    C_LANG    = 3
    C_LABEL   = 4
    C_ENABLED = 5
    C_DEFAULT = 6
    C_FORCED  = 7

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._current: MKVFile | None = None

        self._trUnknown = self.tr("Unknown")
        self._trYes = self.tr("Yes")

        self._tracks = QTreeWidget(self)
        self._tracks.setIndentation(0)
        self._tracks.setHeaderLabels([
            "#", self.tr("Type"), self.tr("Codec"), self.tr("Lang"), self.tr("Label"),
            self.tr("Enabled"), self.tr("Default"), self.tr("Forced"),
        ])

        columns = self._tracks.columnCount()
        for i, w in enumerate(CONFIG.getSizes("mediaViewColumns")):
            if i < columns:
                self._tracks.setColumnWidth(i, w)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self._tracks)

        self.setLayout(self.outerBox)

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
        self._current = MKVFile(file)
        self._current.loadFile()
        self._listTracks()
        return

    ##
    #  Internal Functions
    ##

    def _listTracks(self) -> None:
        """"""
        self._tracks.clear()
        if isinstance(self._current, MKVFile):
            for track in self._current.tracks():
                props = track.get("properties", {})

                tID      = str(track.get("id", "-"))
                tType    = track.get("type", self._trUnknown).title()
                tCodec   = track.get("codec", self._trUnknown)
                tLang    = props.get("language", "und")
                tLabel   = props.get("track_name", "")
                tEnabled = self._trYes if props.get("enabled_track", False) else ""
                tDefault = self._trYes if props.get("default_track", False) else ""
                tForced  = self._trYes if props.get("forced_track", False) else ""

                item = QTreeWidgetItem()
                item.setText(self.C_TRACK, tID)
                item.setText(self.C_TYPE, tType)
                item.setText(self.C_CODEC, tCodec)
                item.setText(self.C_LANG, tLang)
                item.setText(self.C_LABEL, tLabel)
                item.setText(self.C_ENABLED, tEnabled)
                item.setText(self.C_DEFAULT, tDefault)
                item.setText(self.C_FORCED, tForced)

                self._tracks.addTopLevelItem(item)
        return
