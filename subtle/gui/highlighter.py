"""
Subtle – Syntax Highlighter
===========================

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
import re

from subtle import SHARED

from PyQt6.QtGui import (
    QColor, QSyntaxHighlighter, QTextBlockUserData, QTextCharFormat,
    QTextDocument
)
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

SPELL_RX = re.compile(r"\b[^\s\-–—\/<>]+\b", re.UNICODE)
IGNORE_PATTERNS = [
    re.compile(r"[0-9][0-9,\.:]+[0-9]", re.UNICODE),
]


class GuiDocHighlighter(QSyntaxHighlighter):

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        self._spellErr = QTextCharFormat()
        self._spellErr.setUnderlineColor(QColor(224, 0, 0))
        self._spellErr.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

        self._syntaxCol = QTextCharFormat()
        self._syntaxCol.setForeground(QApplication.palette().highlight().color())

        return

    def highlightBlock(self, text: str) -> None:
        """Highlight a single block."""
        data = self.currentBlockUserData()
        if not isinstance(data, TextBlockData):
            data = TextBlockData()
            self.setCurrentBlockUserData(data)

        for xPos, xEnd in data.spellCheck(text):
            for x in range(xPos, xEnd):
                cFmt = self.format(x)
                cFmt.merge(self._spellErr)
                self.setFormat(x, 1, cFmt)

        return


class TextBlockData(QTextBlockUserData):

    __slots__ = ("_spellErrors")

    def __init__(self) -> None:
        super().__init__()
        self._spellErrors: list[tuple[int, int]] = []
        return

    @property
    def spellErrors(self) -> list[tuple[int, int]]:
        """Return spell error data from last check."""
        return self._spellErrors

    def spellCheck(self, text: str) -> list[tuple[int, int]]:
        """Run the spell checker and cache the result, and return the
        list of spell check errors.
        """
        self._spellErrors = []
        checker = SHARED.spelling

        for rX in IGNORE_PATTERNS:
            for match in rX.finditer(text):
                if (s := match.start(0)) >= 0 and (e := match.end(0)) >= 0:
                    text = text[:s] + " "*(e - s) + text[e:]

        for match in re.finditer(SPELL_RX, text.replace("_", " ")):
            if (
                (word := match.group(0))
                and not (word.isnumeric() or word.isupper() or checker.checkWord(word))
            ):
                self._spellErrors.append((match.start(0), match.end(0)))
        return self._spellErrors
