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
from PyQt6.QtGui import QShortcut, QTextBlock, QTextBlockFormat, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox, QMenu, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget
)

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

        self.btnUp = QToolButton(self)
        self.btnUp.setIcon(SHARED.icons.icon("up"))
        self.btnUp.setShortcut("PgUp")
        self.btnUp.clicked.connect(self._requestPrevious)

        self.btnDown = QToolButton(self)
        self.btnDown.setIcon(SHARED.icons.icon("down"))
        self.btnDown.setShortcut("PgDown")
        self.btnDown.clicked.connect(self._requestNext)

        self.btnItalic = QToolButton(self)
        self.btnItalic.setIcon(SHARED.icons.icon("italic"))
        self.btnItalic.setShortcut("Ctrl+I")
        self.btnItalic.clicked.connect(self._formatItalic)

        self.btnNote = QToolButton(self)
        self.btnNote.setIcon(SHARED.icons.icon("note"))
        self.btnNote.setShortcut("Ctrl+J")
        self.btnNote.clicked.connect(self._insertNoteSymbol)

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
        self.controlsBox = QToolBar()
        self.controlsBox.addWidget(self.btnUp)
        self.controlsBox.addWidget(self.btnDown)
        self.controlsBox.addSeparator()
        self.controlsBox.addWidget(self.btnItalic)
        self.controlsBox.addWidget(self.btnNote)
        self.controlsBox.addSeparator()
        self.controlsBox.addWidget(self.spellLang)

        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.controlsBox)
        self.outerBox.addWidget(self.textEdit)

        self.setLayout(self.outerBox)

        # Shortcuts
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

        bFmt = QTextBlockFormat()
        bFmt.setLineHeight(120.0, 1)

        self.textEdit.clear()
        cursor = self.textEdit.textCursor()
        cursor.setBlockFormat(bFmt)
        for n, line in enumerate(frame.text):
            if n > 0:
                cursor.insertBlock()
            cursor.insertHtml(line)

        cursor.setPosition(0)
        self.textEdit.setTextCursor(cursor)

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
            self._frame.setText(self._getText())
            self.newTextForFrame.emit(self._frame)
        return

    @pyqtSlot(int)
    def _spellLangChanged(self, index: int) -> None:
        """Process change in spell check language."""
        SHARED.spelling.setLanguage(self.spellLang.currentData())
        self.highlight.rehighlight()
        return

    @pyqtSlot()
    def _requestPrevious(self) -> None:
        """Process Page Up key press."""
        self.requestNewFrame.emit(-1)
        return

    @pyqtSlot()
    def _requestNext(self) -> None:
        """Process Page Down key press."""
        self.requestNewFrame.emit(1)
        return

    @pyqtSlot()
    def _formatItalic(self) -> None:
        """Process Ctrl+I key press."""
        if document := self.textEdit.document():
            cursor = self.textEdit.textCursor()
            posO = cursor.position()
            italic = cursor.charFormat().fontItalic()
            if cursor.hasSelection():
                posS = cursor.selectionStart()
                posE = cursor.selectionEnd()
                block = document.findBlock(posS)
                posE = min(posE, block.position() + block.length())
            else:
                block = document.findBlock(cursor.position())
                posS = block.position()
                posE = posS + block.length() - 1
                cursor.setPosition(posS, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(posE, QTextCursor.MoveMode.KeepAnchor)

            cFmt = QTextCharFormat()
            cFmt.setFontItalic(not italic)

            cursor.beginEditBlock()
            cursor.setCharFormat(cFmt)
            cursor.setPosition(posO)
            cursor.endEditBlock()

            self.textEdit.setTextCursor(cursor)

        return

    @pyqtSlot()
    def _insertNoteSymbol(self) -> None:
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
            if action := ctxMenu.addAction(self.tr("Ignore Word")):
                action.triggered.connect(lambda: self._addWord(word, block, False))
            if action := ctxMenu.addAction(self.tr("Add Word to Dictionary")):
                action.triggered.connect(lambda: self._addWord(word, block, True))

        # Execute the context menu
        if viewport := self.textEdit.viewport():
            ctxMenu.exec(viewport.mapToGlobal(pos))
            ctxMenu.deleteLater()

        return

    ##
    #  Internal Functions
    ##

    def _getText(self) -> list[str]:
        """Get the text of the document."""
        result = []
        if document := self.textEdit.document():
            for i in range(document.blockCount()):
                if (block := document.findBlockByNumber(i)).isValid():
                    line = ""
                    it = block.begin()
                    while not it.atEnd():
                        if (fragment := it.fragment()).isValid():
                            fmt = fragment.charFormat()
                            text = fragment.text()
                            if fmt.fontItalic():
                                line = f"{line}<i>{text}</i>"
                            else:
                                line = f"{line}{text}"
                        it += 1
                    if line := line.strip():
                        result.append(line)
        return result

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

    def _addWord(self, word: str, block: QTextBlock, save: bool) -> None:
        """Slot for the spell check context menu triggered when the user
        wants to add a word to the user dictionary, or ignore it for the
        current session.
        """
        logger.debug("Added '%s' to session dictionary, saved = %s", word, str(save))
        SHARED.spelling.addWord(word, save=save)
        self.highlight.rehighlightBlock(block)
        return

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
