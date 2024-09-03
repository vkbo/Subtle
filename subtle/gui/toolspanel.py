"""
Subtle – GUI Tools Panel
========================

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

from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget
)

logger = logging.getLogger(__name__)


class GuiToolsPanel(QWidget):

    requestSrtSave = pyqtSignal(Path)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        # Variables
        self._mediaFile: Path | None = None
        self._trackFile: Path | None = None
        self._trackInfo: dict = {}

        # SRT Panel
        self.srtForm = QGridLayout()

        row = 0
        self.srtSaveDir = QLineEdit()
        self.srtSubsDir = QCheckBox(self.tr("Use 'Subs' folder"), self)
        self.srtSubsDir.clicked.connect(self._updateTrackInfo)

        self.srtForm.addWidget(QLabel(self.tr("Output Folder"), self), row, 0)
        self.srtForm.addWidget(self.srtSaveDir, row, 1)
        self.srtForm.addWidget(self.srtSubsDir, row, 2, 1, 2)

        row += 1
        self.srtFileName = QLineEdit()
        self.srtForced = QCheckBox(self.tr("Forced"), self)
        self.srtForced.clicked.connect(self._updateTrackInfo)
        self.srtSDH = QCheckBox(self.tr("SDH"), self)
        self.srtSDH.clicked.connect(self._updateTrackInfo)

        self.srtForm.addWidget(QLabel(self.tr("File Name"), self), row, 0)
        self.srtForm.addWidget(self.srtFileName, row, 1)
        self.srtForm.addWidget(self.srtForced, row, 2)
        self.srtForm.addWidget(self.srtSDH, row, 3)

        row += 1
        self.srtSaveButton = QPushButton(self.tr("Save SRT File"), self)
        self.srtSaveButton.clicked.connect(self._clickedSaveSrt)

        self.srtControls = QHBoxLayout()
        self.srtControls.addStretch(1)
        self.srtControls.addWidget(self.srtSaveButton, 0)

        self.srtForm.addLayout(self.srtControls, row, 0, 1, 4)

        self.srtFrame = QGroupBox(self.tr("SubRip / SRT"), self)
        self.srtFrame.setLayout(self.srtForm)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.srtFrame)
        self.outerBox.addStretch(1)

        self.setLayout(self.outerBox)

        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(Path)
    def newFileSelected(self, path: Path) -> None:
        """Store the path to the selected file for later use."""
        self._mediaFile = path
        self._updateTrackInfo()
        return

    @pyqtSlot(Path, dict)
    def newTrackSelected(self, path: Path, info: dict) -> None:
        """Load a new track, if possible."""
        self._trackFile = path
        self._trackInfo = info

        props = self._trackInfo.get("properties", {})
        self.srtForced.setChecked(bool(props.get("forced_track", False)))

        self._updateTrackInfo()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _clickedSaveSrt(self) -> None:
        """Process save SRT button click."""
        try:
            folder = Path(self.srtSaveDir.text())
            folder.mkdir(exist_ok=True)
            if name := self.srtFileName.text().strip():
                self.requestSrtSave.emit(folder / name)
        except Exception as exc:
            logger.error("Failed to prepare subtitles folder", exc_info=exc)
        return

    @pyqtSlot()
    def _updateTrackInfo(self) -> None:
        """Update info about the current track."""
        if self._mediaFile and self._trackFile and self._trackInfo:
            props = self._trackInfo.get("properties", {})

            if self.srtSubsDir.isChecked():
                folder = self._mediaFile.parent / "Subs"
            else:
                folder = self._mediaFile.parent

            bits = [self._mediaFile.stem]
            bits.append(str(props.get("language", "und")))
            if self.srtForced.isChecked():
                bits.append("forced")
            if self.srtSDH.isChecked():
                bits.append("sdh")
            bits.append("srt")

            self.srtSaveDir.setText(str(folder))
            self.srtFileName.setText(".".join(bits))

        return
