"""
Subtle – GUI Text Editor
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

from subtle.core.pgsreader import DisplaySet

from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class GuiTextEditor(QWidget):

    newTextForIndex = pyqtSignal(int, list)
    newTextForDisplaySet = pyqtSignal(DisplaySet)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._ds: DisplaySet | None = None
        self._index = -1

        # Editor
        self.textEdit = QPlainTextEdit(self)

        font = self.textEdit.font()
        font.setPointSizeF(font.pointSizeF() * 3)
        self.textEdit.setFont(font)

        # Controls
        self.updateButton = QPushButton(self.tr("Update"), self)
        self.updateButton.clicked.connect(self._updateButtonClicked)

        self.controlBox = QHBoxLayout()
        self.controlBox.addStretch(1)
        self.controlBox.addWidget(self.updateButton)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.textEdit)
        self.outerBox.addLayout(self.controlBox)

        self.setLayout(self.outerBox)

        return

    def setText(self, ds: DisplaySet, index: int) -> None:
        """Set the editor text."""
        self._ds = ds
        self._index = index
        self.textEdit.setPlainText("\n".join(ds.text))
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _updateButtonClicked(self) -> None:
        """The text has been updated."""
        if self._ds:
            logger.debug("Updating text for display set %d", self._ds.pcs.compNumber)
            self._ds.setText(self.textEdit.toPlainText().strip().split("\n"))
            self.newTextForDisplaySet.emit(self._ds)
        return
