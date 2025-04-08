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

from subtle import SHARED
from subtle.constants import MediaType

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget
)

logger = logging.getLogger(__name__)


class GuiToolsPanel(QWidget):

    D_SUBS_PATH = Qt.ItemDataRole.UserRole

    requestSrtSave = pyqtSignal(Path)
    requestSubsLoad = pyqtSignal(Path)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        # Media Panel
        # ===========
        self.mediaForm = QFormLayout()

        self.mediaDir = QLineEdit(self)
        self.mediaDir.setReadOnly(True)

        self.mediaFile = QLineEdit(self)
        self.mediaFile.setReadOnly(True)

        self.mediaForm.addRow(self.tr("Media Folder"), self.mediaDir)
        self.mediaForm.addRow(self.tr("Media File"), self.mediaFile)

        self.mediaFrame = QGroupBox(self.tr("Current Media"), self)
        self.mediaFrame.setLayout(self.mediaForm)

        # Subs List
        # =========

        self.subsList = QListWidget(self)

        self.subsLoad = QPushButton(self.tr("Load Subs"), self)
        self.subsLoad.clicked.connect(self._clickedLoadSubs)

        # Assemble
        self.subsButtons = QHBoxLayout()
        self.subsButtons.addStretch(1)
        self.subsButtons.addWidget(self.subsLoad)

        self.subsBox = QVBoxLayout()
        self.subsBox.addWidget(self.subsList)
        self.subsBox.addLayout(self.subsButtons)

        self.subsFrame = QGroupBox(self.tr("Existing Subtitles"), self)
        self.subsFrame.setLayout(self.subsBox)

        # SRT Panel
        # =========
        self.srtForm = QFormLayout()

        self.srtSaveDir = QLineEdit(self)
        self.srtForm.addRow(self.tr("Output Folder"), self.srtSaveDir)

        self.srtFileName = QLineEdit(self)
        self.srtForm.addRow(self.tr("File Name"), self.srtFileName)

        self.srtSubsDir = QCheckBox(self.tr("Use 'Subs' folder"), self)
        self.srtSubsDir.clicked.connect(self._updateTrackInfo)

        self.srtForced = QCheckBox(self.tr("Forced"), self)
        self.srtForced.clicked.connect(self._updateTrackInfo)

        self.srtSDH = QCheckBox(self.tr("SDH"), self)
        self.srtSDH.clicked.connect(self._updateTrackInfo)

        self.srtSaveButton = QPushButton(self.tr("Save SRT File"), self)
        self.srtSaveButton.clicked.connect(self._clickedSaveSrt)

        # Assemble
        self.srtOptions = QHBoxLayout()
        self.srtOptions.addWidget(self.srtSubsDir)
        self.srtOptions.addWidget(self.srtForced)
        self.srtOptions.addWidget(self.srtSDH)
        self.srtOptions.addStretch(1)

        self.srtButtons = QHBoxLayout()
        self.srtButtons.addStretch(1)
        self.srtButtons.addWidget(self.srtSaveButton)

        self.srtForm.addRow("", self.srtOptions)
        self.srtForm.addRow("", self.srtButtons)

        self.srtFrame = QGroupBox(self.tr("SubRip / SRT"), self)
        self.srtFrame.setLayout(self.srtForm)

        # Layout
        # ======

        self.leftBox = QVBoxLayout()
        self.leftBox.addWidget(self.mediaFrame)
        self.leftBox.addWidget(self.srtFrame)
        self.leftBox.addStretch(1)

        self.rightBox = QVBoxLayout()
        self.rightBox.addWidget(self.subsFrame)
        self.rightBox.addStretch(1)

        self.outerBox = QHBoxLayout()
        self.outerBox.addLayout(self.leftBox, 3)
        self.outerBox.addLayout(self.rightBox, 2)

        self.setLayout(self.outerBox)

        return

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def processNewMediaLoaded(self) -> None:
        """Store the path to the selected file for later use."""
        if file := SHARED.media.mediaFile:
            path = file.filePath
            self.mediaDir.setText(str(path.parent))
            self.mediaFile.setText(path.name)
            self._scanForSubs(path)
        self._updateTrackInfo()
        return

    @pyqtSlot()
    def processNewTrackLoaded(self) -> None:
        """Load a new track, if possible."""
        if (track := SHARED.media.currentTrack) and track.trackType == MediaType.SUBS:
            self.srtForced.setChecked(track.forced)
            self.srtSDH.setChecked(track.sdh)
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
    def _clickedLoadSubs(self) -> None:
        """Process load subs button click."""
        if items := self.subsList.selectedItems():
            if (path := Path(items[0].data(self.D_SUBS_PATH))).is_file():
                self.requestSubsLoad.emit(path)
        return

    @pyqtSlot()
    def _updateTrackInfo(self) -> None:
        """Update info about the current track."""
        self.srtSaveDir.setText("")
        self.srtFileName.setText("")
        if SHARED.media.currentTrack and (file := SHARED.media.mediaFile):
            if self.srtSubsDir.isChecked():
                folder = file.filePath.parent / "Subs"
            else:
                folder = file.filePath.parent

            bits = [file.filePath.stem]
            bits.append(SHARED.media.currentTrack.language)
            if self.srtForced.isChecked():
                bits.append("forced")
            if self.srtSDH.isChecked():
                bits.append("sdh")
            bits.append("srt")

            self.srtSaveDir.setText(str(folder))
            self.srtFileName.setText(".".join(bits))

        return

    ##
    #  Internal Functions
    ##

    def _scanForSubs(self, path: Path) -> None:
        """Scan for subtitle files in path."""
        self.subsList.clear()
        root = path.parent
        try:
            folders = [root]
            for entry in root.iterdir():
                try:
                    if entry.is_dir() and not entry.is_reserved():
                        folders.append(entry)
                except PermissionError:
                    logger.info("Permission denied: %s", entry)

            prefix = path.stem.lower()
            for folder in folders:
                try:
                    for entry in folder.iterdir():
                        if (
                            entry.is_file()
                            and entry.suffix == ".srt"
                            and entry.stem.lower().startswith(prefix)
                        ):
                            item = QListWidgetItem()
                            item.setText(str(entry.relative_to(root)))
                            item.setData(self.D_SUBS_PATH, entry)
                            self.subsList.addItem(item)
                except PermissionError:
                    logger.info("Permission denied: %s", folder)

        except Exception as exc:
            logger.error("Could not scan path: %s", root, exc_info=exc)

        return
