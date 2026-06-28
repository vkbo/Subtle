"""
Subtle – GUI File Tree
======================

This file is a part of Subtle
Copyright (C) Veronica Berglyd Olsen

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
"""  # noqa

from __future__ import annotations

import logging

from pathlib import Path

from PyQt6.QtCore import QModelIndex, pyqtSlot
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QTreeView, QWidget

from subtle_gui import CONFIG, SHARED

logger = logging.getLogger(__name__)


class GuiFileTree(QTreeView):
    """GUI File Tree."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._current = None

        self._model = QFileSystemModel(self)
        self._model.setRootPath("/")
        self._model.setReadOnly(True)
        self._model.directoryLoaded.connect(self._directoryLoaded)

        self.setModel(self._model)

        columns = self._model.columnCount()
        for i, w in enumerate(CONFIG.getSizes("fileTreeColumns")):
            if i < columns:
                self.setColumnWidth(i, w)

        self.doubleClicked.connect(self._itemDoubleClicked)

    ##
    #  Methods
    ##

    def saveSettings(self) -> None:
        """Save widget settings."""
        CONFIG.setSizes("fileTreeColumns", [self.columnWidth(i) for i in range(self._model.columnCount())])

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _itemDoubleClicked(self, index: QModelIndex) -> None:
        """Process item double click in the file tree."""
        if (path := Path(self._model.filePath(index))).is_file() and path != self._current:
            SHARED.media.loadMediaFile(path)
            self._current = path

    @pyqtSlot(str)
    def _directoryLoaded(self, path: str) -> None:
        """Process model finished loading directory."""
        if path == "/":
            self.expand(self._model.index(path))
