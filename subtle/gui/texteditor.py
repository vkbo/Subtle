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

from subtle.formats.pgssubs import DisplaySet

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QShortcut, QTextCursor
from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class GuiTextEditor(QWidget):

    newTextForIndex = pyqtSignal(int, list)
    newTextForDisplaySet = pyqtSignal(DisplaySet)
    requestNewDisplaySet = pyqtSignal(int)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._ds: DisplaySet | None = None
        self._block = False

        # Editor
        self.textEdit = QTextEdit(self)
        self.textEdit.textChanged.connect(self._textChanged)

        if document := self.textEdit.document():
            options = document.defaultTextOption()
            options.setAlignment(Qt.AlignmentFlag.AlignCenter)
            document.setDefaultTextOption(options)
            document.setDocumentMargin(20.0)

        font = self.textEdit.font()
        font.setPointSizeF(font.pointSizeF() * 3)
        self.textEdit.setFont(font)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.textEdit)

        self.setLayout(self.outerBox)

        # Shortcuts
        self.kbPageUp = QShortcut(self.textEdit)
        self.kbPageUp.setKey(Qt.Key.Key_PageUp)
        self.kbPageUp.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.kbPageUp.activated.connect(self._keyPressPageUp)

        self.kbPageDn = QShortcut(self.textEdit)
        self.kbPageDn.setKey(Qt.Key.Key_PageDown)
        self.kbPageDn.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.kbPageDn.activated.connect(self._keyPressPageDown)

        self.kbItalic = QShortcut(self.textEdit)
        self.kbItalic.setKey("Ctrl+I")
        self.kbItalic.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.kbItalic.activated.connect(self._keyPressItalic)

        self.kbNote = QShortcut(self.textEdit)
        self.kbNote.setKey("Ctrl+J")
        self.kbNote.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.kbNote.activated.connect(self._keyPressNote)

        return

    def setText(self, ds: DisplaySet) -> None:
        """Set the editor text."""
        self._ds = ds
        self._block = True
        self.textEdit.setPlainText("\n".join(ds.text))
        self._block = False
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _textChanged(self) -> None:
        """Update display set text when editor changes."""
        if self._ds and not self._block:
            self._ds.setText(self.textEdit.toPlainText().strip().split("\n"))
            self.newTextForDisplaySet.emit(self._ds)
        return

    @pyqtSlot()
    def _keyPressPageUp(self) -> None:
        """Process Page Up key press."""
        self.requestNewDisplaySet.emit(-1)
        return

    @pyqtSlot()
    def _keyPressPageDown(self) -> None:
        """Process Page Down key press."""
        self.requestNewDisplaySet.emit(1)
        return

    @pyqtSlot()
    def _keyPressItalic(self) -> None:
        """Process Ctrl+I key press."""
        if document := self.textEdit.document():
            cursor = self.textEdit.textCursor()
            if uSelect := cursor.hasSelection():
                posS = cursor.selectionStart()
                posE = cursor.selectionEnd()
                block = document.findBlock(posS)
                posE = min(posE, block.position() + block.length())
            else:
                block = document.findBlock(cursor.position())
                posS = block.position()
                posE = posS + block.length() - 1

            cursor.beginEditBlock()
            cursor.setPosition(posE)
            cursor.insertText("</i>")
            cursor.setPosition(posS)
            cursor.insertText("<i>")
            cursor.endEditBlock()

            if uSelect:
                cursor.setPosition(posE+3, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(posS+3, QTextCursor.MoveMode.KeepAnchor)
                self.textEdit.setTextCursor(cursor)

        return

    @pyqtSlot()
    def _keyPressNote(self) -> None:
        """Process Ctrl+J key press."""
        cursor = self.textEdit.textCursor()
        cursor.insertText("\u266a")
        return
