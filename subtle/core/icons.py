"""
Subtle – Icons
==============

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

from PyQt6.QtCore import QPoint, QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QIconEngine, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

RAW_SVG = {
    "up": (
        b'<path d="m20.247 17.565c1.0042-1.0029 1.0042-2.6332 0-3.6361l-8.2467-8.248-8.2467 8.248c'
        b'-0.50272 0.50144-0.75344 1.1597-0.75344 1.818s0.25072 1.3166 0.75344 1.818c1.0042 1.0042'
        b' 2.6319 1.0042 3.6361 0l4.6107-4.6094 4.6107 4.6094c1.0042 1.0042 2.6319 1.0042 3.6361 0'
        b'z" fill="{foreground}" stroke-width="1.2857"/>'
    ),
    "down": (
        b'<path d="m3.7531 6.4345c-1.0042 1.0029-1.0042 2.6332 0 3.6361l8.2467 8.248 8.2467-8.248c'
        b'0.50272-0.50144 0.75344-1.1597 0.75344-1.818s-0.25072-1.3166-0.75344-1.818c-1.0042-1.004'
        b'2-2.6319-1.0042-3.6361 0l-4.6107 4.6094-4.6107-4.6094c-1.0042-1.0042-2.6319-1.0042-3.636'
        b'1 0z" fill="{foreground}" stroke-width="1.2857"/>'
    ),
    "italic": (
        b'<path d="m8.7248 21 3.5779-18h2.9724l-3.5779 18z" fill="{foreground}" '
        b'stroke-width="2.0642"/>'
    ),
    "note": (
        b'<path d="m12.679 3q0.09536 0.5245 0.26225 0.95364 0.16689 0.4053 0.47682 0.8106 0.30993 '
        b'0.4053 0.8106 0.88212 0.50066 0.45298 1.2636 1.0728 1.1921 0.97748 1.7881 1.9788 0.61987'
        b' 0.97748 0.61987 2.1934 0 1.0728-0.45298 2.1934-0.42914 1.0967-1.0728 2.0026l-0.83444-0.'
        b'45298q0.50066-1.0728 0.50066-2.1934 0-0.97748-0.35762-1.5258-0.35762-0.57218-0.90596-1.0'
        b'967-0.45298-0.42914-0.90596-0.78675-0.45298-0.35762-0.95364-0.76291v7.9629q0 2.1695-1.07'
        b'28 3.4808-1.0728 1.2874-2.9801 1.2874-0.57219 0-1.0728-0.11921-0.50066-0.1192-0.88212-0.'
        b'38146-0.35762-0.26225-0.59603-0.64371-0.21457-0.4053-0.21457-0.95364 0-0.61987 0.28609-1'
        b'.1444 0.28609-0.5245 0.78676-0.90596 0.5245-0.4053 1.2397-0.61987 0.71523-0.23841 1.5735'
        b'-0.23841 0.69139 0 1.2636 0.14305v-13.136z" fill="{foreground}" stroke-linecap="round" '
        b'stroke-width="1.7881"/>'
    ),
}

BASE = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n<svg width="24" height="24" version="1.2" viewBox="0'
    b' 0 24 24" xmlns="http://www.w3.org/2000/svg">\n{content}\n</svg>'
)


class GuiIcons:

    def __init__(self) -> None:
        palette = QApplication.palette()
        self._cache: dict[str, QIcon] = {}
        self._color = palette.buttonText().color().name(QColor.NameFormat.HexRgb).encode()
        return

    def icon(self, key: str) -> QIcon:
        """Return an icon, either from the cache or generate it."""
        if key not in self._cache:
            self._cache[key] = QIcon(
                _IconEngine(
                    BASE
                    .replace(b"{content}", RAW_SVG.get(key, b""))
                    .replace(b"{foreground}", self._color)
                )
            )
        return self._cache[key]


class _IconEngine(QIconEngine):

    def __init__(self, data: bytes) -> None:
        super().__init__()
        self._data = data
        return

    def clone(self) -> QIconEngine | None:
        """Clone the icon engine."""
        return _IconEngine(self._data)

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        """Create pixmap object."""
        img = QImage(size, QImage.Format.Format_ARGB32)
        img.fill(0x000000)
        pix = QPixmap.fromImage(img, Qt.ImageConversionFlag.NoFormatConversion)
        painter = QPainter(pix)
        self.paint(painter, QRect(QPoint(0, 0), size), mode, state)
        return pix

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State) -> None:
        """SVG icon painter."""
        renderer = QSvgRenderer(self._data)
        renderer.render(painter, QRectF(rect))
        return
