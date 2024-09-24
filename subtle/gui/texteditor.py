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

from subtle import CONFIG, SHARED
from subtle.formats.base import FrameBase
from subtle.gui.highlighter import GuiDocHighlighter, TextBlockData

from PyQt6.QtCore import QPoint, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QShortcut, QTextBlock, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QMenu, QTextEdit, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class GuiTextEditor(QWidget):

    newTextForFrame = pyqtSignal(FrameBase)
    requestNewFrame = pyqtSignal(int)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._frame: FrameBase | None = None
        self._block = False

        # Controls
        self.spellLang = QComboBox(self)
        self.spellLang.addItem(self.tr("Default"), "None")
        for tag, language in SHARED.spelling.listDictionaries():
            self.spellLang.addItem(language, tag)

        self.spellLang.currentIndexChanged.connect(self._spellLangChanged)

        # Editor
        self.textEdit = QTextEdit(self)
        self.textEdit.setFont(CONFIG.subsFont)
        self.textEdit.textChanged.connect(self._textChanged)

        if document := self.textEdit.document():
            options = document.defaultTextOption()
            options.setAlignment(Qt.AlignmentFlag.AlignCenter)
            document.setDefaultTextOption(options)
            document.setDocumentMargin(20.0)
            self.highlight = GuiDocHighlighter(document)

        # Context Menu
        self.textEdit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect(self._openContextMenu)

        # Assemble
        self.controlsBox = QHBoxLayout()
        self.controlsBox.addWidget(self.spellLang)
        self.controlsBox.addStretch(1)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.controlsBox)
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

        self.keyContext = QShortcut(self.textEdit)
        self.keyContext.setKey("Ctrl+.")
        self.keyContext.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.keyContext.activated.connect(self._openContextFromCursor)

        return

    ##
    #  Public Slots
    ##

    @pyqtSlot(FrameBase)
    def setEditorText(self, frame: FrameBase) -> None:
        """Set the editor text."""
        self._frame = frame
        self._block = True

        self.textEdit.setPlainText("\n".join(frame.text))

        blockFmt = QTextBlockFormat()
        blockFmt.setLineHeight(120.0, 1)
        cursor = self.textEdit.textCursor()
        cursor.clearSelection()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(blockFmt)

        self._block = False
        return

    @pyqtSlot(str)
    def updateSpellLanguage(self, language: str) -> None:
        """Update the spell check language box."""
        self.spellLang.blockSignals(True)
        if (idx := self.spellLang.findData(language)) != -1:
            self.spellLang.setCurrentIndex(idx)
        else:
            self.spellLang.setCurrentIndex(0)
        self.spellLang.blockSignals(False)
        return

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _textChanged(self) -> None:
        """Update display set text when editor changes."""
        if self._frame and not self._block:
            self._frame.setText(self.textEdit.toPlainText().strip().split("\n"))
            self.newTextForFrame.emit(self._frame)
        return

    @pyqtSlot(int)
    def _spellLangChanged(self, index: int) -> None:
        """Process change in spell check language."""
        SHARED.spelling.setLanguage(self.spellLang.currentData())
        self.highlight.rehighlight()
        return

    @pyqtSlot()
    def _keyPressPageUp(self) -> None:
        """Process Page Up key press."""
        self.requestNewFrame.emit(-1)
        return

    @pyqtSlot()
    def _keyPressPageDown(self) -> None:
        """Process Page Down key press."""
        self.requestNewFrame.emit(1)
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

    @pyqtSlot()
    def _openContextFromCursor(self) -> None:
        """Open the spell check context menu at the cursor."""
        self._openContextMenu(self.textEdit.cursorRect().center())
        return

    @pyqtSlot("QPoint")
    def _openContextMenu(self, pos: QPoint) -> None:
        """Open the editor context menu at a given coordinate."""
        pCursor = self.textEdit.cursorForPosition(pos)

        ctxMenu = QMenu(self)
        ctxMenu.setObjectName("ContextMenu")

        # Spell Checking
        word, cPos, cLen, suggest = self._spellErrorAtPos(pCursor.position())
        if word and cPos >= 0 and cLen > 0:
            logger.debug("Word '%s' is misspelled", word)
            block = pCursor.block()
            sCursor = self.textEdit.textCursor()
            sCursor.setPosition(block.position() + cPos)
            sCursor.movePosition(
                QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, cLen
            )
            if suggest:
                ctxMenu.addSeparator()
                ctxMenu.addAction(self.tr("Spelling Suggestion(s)"))
                for option in suggest[:15]:
                    if action := ctxMenu.addAction(option):
                        action.triggered.connect(
                            lambda _, option=option: self._correctWord(sCursor, option)
                        )
            else:
                ctxMenu.addAction(self.tr("No Suggestions"))

            ctxMenu.addSeparator()
            if action := ctxMenu.addAction(self.tr("Add Word to Dictionary")):
                action.triggered.connect(lambda: self._addWord(word, block))

        # Execute the context menu
        if viewport := self.textEdit.viewport():
            ctxMenu.exec(viewport.mapToGlobal(pos))
            ctxMenu.deleteLater()

        return

    @pyqtSlot("QTextCursor", str)
    def _correctWord(self, cursor: QTextCursor, word: str) -> None:
        """Slot for the spell check context menu triggering the
        replacement of a word with the word from the dictionary.
        """
        pos = cursor.selectionStart()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()
        cursor.setPosition(pos)
        self.textEdit.setTextCursor(cursor)
        return

    @pyqtSlot(str, "QTextBlock")
    def _addWord(self, word: str, block: QTextBlock) -> None:
        """Slot for the spell check context menu triggered when the user
        wants to add a word to the project dictionary.
        """
        logger.debug("Added '%s' to project dictionary", word)
        SHARED.spelling.addWord(word)
        self.highlight.rehighlightBlock(block)
        return

    ##
    #  Internal Functions
    ##

    def _spellErrorAtPos(self, pos: int) -> tuple[str, int, int, list[str]]:
        """Check if there is a misspelled word at a given position in
        the document, and if so, return it.
        """
        cursor = self.textEdit.textCursor()
        cursor.setPosition(pos)
        block = cursor.block()
        data = block.userData()
        if block.isValid() and isinstance(data, TextBlockData):
            text = block.text()
            check = pos - block.position()
            if check >= 0:
                for cPos, cEnd in data.spellErrors:
                    cLen = cEnd - cPos
                    if cPos <= check <= cEnd:
                        word = text[cPos:cEnd]
                        return word, cPos, cLen, SHARED.spelling.suggestWords(word)
        return "", -1, -1, []
