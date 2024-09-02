"""
Subtle – GUI Main Window
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
import sys

from dataclasses import dataclass
from pathlib import Path

from subtle import CONFIG
from subtle.core.ocrbase import OCRBase
from subtle.core.pgsreader import DisplaySet
from subtle.core.tesseract import TesseractOCR
from subtle.gui.filetree import GuiFileTree
from subtle.gui.imageviewer import GuiImageViewer
from subtle.gui.mediaplayer import GuiMediaPlayer
from subtle.gui.mediaview import GuiMediaView
from subtle.gui.subsview import GuiSubtitleView
from subtle.gui.texteditor import GuiTextEditor

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QSplitter

logger = logging.getLogger(__name__)


@dataclass
class CurrentObject:

    mediaFile: Path
    trackFile: Path | None = None
    trackInfo: dict | None = None


class GuiMain(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        logger.debug("Create: GUI")
        self.setObjectName("GuiMain")

        # System Info
        # ===========

        logger.info("OS: %s", CONFIG.osType)
        logger.info("Kernel: %s", CONFIG.kernelVer)
        logger.info("Host: %s", CONFIG.hostName)
        logger.info("Qt5: %s (0x%06x)", CONFIG.verQtString, CONFIG.verQtValue)
        logger.info("PyQt5: %s (0x%06x)", CONFIG.verPyQtString, CONFIG.verPyQtValue)
        logger.info("Python: %s (0x%08x)", CONFIG.verPyString, sys.hexversion)

        logger.debug("Ready: GUI")
        logger.info("Subtle is ready ...")

        # Cached Data
        # ===========

        self._mediaFile: Path | None = None
        self._trackFile: Path | None = None
        self._trackInfo: dict = {}

        # Gui Elements
        # ============

        self.fileTree = GuiFileTree(self)
        self.mediaView = GuiMediaView(self)
        self.subsView = GuiSubtitleView(self)
        self.mediaPlayer = GuiMediaPlayer(self)
        self.imageViewer = GuiImageViewer(self)
        self.textEditor = GuiTextEditor(self)

        # Processing
        # ==========

        self.ocrTool: OCRBase | None = None

        # Signals
        # =======
        self.fileTree.newFileSelection.connect(self._newFileSelected)
        self.fileTree.newFileSelection.connect(self.mediaView.setCurrentFile)
        self.fileTree.newFileSelection.connect(self.subsView.newFileSelected)
        self.mediaView.newTrackAvailable.connect(self._newTrackSelected)
        self.mediaView.newTrackAvailable.connect(self.subsView.loadTrack)
        self.subsView.displaySetSelected.connect(self._displaySetSelected)

        # Layout
        # ======

        self.splitContent = QSplitter(Qt.Orientation.Vertical, self)
        self.splitContent.addWidget(self.mediaView)
        self.splitContent.addWidget(self.subsView)
        self.splitContent.setSizes(CONFIG.getSizes("contentSplit"))

        self.splitView = QSplitter(Qt.Orientation.Vertical, self)
        self.splitView.addWidget(self.mediaPlayer)
        self.splitView.addWidget(self.imageViewer)
        self.splitView.addWidget(self.textEditor)
        self.splitView.setSizes(CONFIG.getSizes("viewSplit"))

        self.splitMain = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitMain.addWidget(self.fileTree)
        self.splitMain.addWidget(self.splitContent)
        self.splitMain.addWidget(self.splitView)
        self.splitMain.setSizes(CONFIG.getSizes("mainSplit"))

        self.setCentralWidget(self.splitMain)
        self.resize(CONFIG.getSize("mainWindow"))

        return

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the closing event of the GUI and call the close
        function to handle all the close process steps.
        """
        logger.info("Exiting Subtle")
        self.fileTree.saveSettings()
        self.mediaView.saveSettings()
        self.subsView.saveSettings()
        CONFIG.setSize("mainWindow", self.size())
        CONFIG.setSizes("mainSplit", self.splitMain.sizes())
        CONFIG.setSizes("contentSplit", self.splitContent.sizes())
        CONFIG.setSizes("viewSplit", self.splitView.sizes())
        CONFIG.save()
        CONFIG.cleanup()
        event.accept()
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(Path, dict)
    def _newTrackSelected(self, path: Path, info: dict) -> None:
        """A new track has been selected."""
        self._trackFile = path
        self._trackInfo = info
        return

    @pyqtSlot(Path)
    def _newFileSelected(self, path: Path) -> None:
        """"""
        self._mediaFile = path
        self.ocrTool = TesseractOCR()
        return

    @pyqtSlot(int, DisplaySet)
    def _displaySetSelected(self, index: int, ds: DisplaySet) -> None:
        """"""
        logger.info("Selected display set with composition number %d", ds.pcs.compNumber)
        image = ds.render()
        self.imageViewer.setImage(image)
        if self.ocrTool and (info := self._trackInfo):
            lang = info.get("properties", {}).get("language", "und")
            text = self.ocrTool.processImage(index, image, [lang])
            self.subsView.setText(ds, text)
            self.textEditor.setText(text)
        return
