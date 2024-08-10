"""
Subtle – GUI File Tree
======================

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

from PyQt6.QtCore import QModelIndex, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QTreeView, QWidget

logger = logging.getLogger(__name__)


class GuiFileTree(QTreeView):

    newFileSelection = pyqtSignal(Path)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._current = None

        self._model = QFileSystemModel(self)
        self._model.setRootPath("/")
        self._model.setReadOnly(True)

        self.setModel(self._model)

        self.clicked.connect(self._itemClicked)

        return

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _itemClicked(self, index: QModelIndex) -> None:
        """Process item selection in the file tree."""
        if (path := Path(self._model.filePath(index))).is_file():
            if path != self._current:
                self.newFileSelection.emit(path)
                self._current = path
        return
