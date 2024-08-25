"""
Subtle – GUI Image Viewer
=========================

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

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QHBoxLayout, QWidget

logger = logging.getLogger(__name__)


class GuiImageViewer(QWidget):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._imageSize = QRectF(0.0, 0.0, 0.0, 0.0)

        # Image Widget
        self.imageScene = QGraphicsScene(self)

        self.imageView = QGraphicsView(self)
        self.imageView.setScene(self.imageScene)
        self.imageView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.imageView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Assemble
        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.imageView)

        self.setLayout(self.outerBox)

        return

    def setImage(self, image: QImage) -> None:
        """Display an image of subtitles."""
        self._imageSize = QRectF(image.rect())
        self.imageScene.addPixmap(QPixmap.fromImage(image))
        self.imageScene.setSceneRect(self._imageSize)
        self._updateSizes()
        return

    ##
    #  Event
    ##

    def resizeEvent(self, event: QResizeEvent) -> None:
        """"""
        super().resizeEvent(event)
        self._updateSizes()
        return

    ##
    #  Internal Functions
    ##

    def _updateSizes(self) -> None:
        """"""
        self.imageView.fitInView(self._imageSize, Qt.AspectRatioMode.KeepAspectRatio)
        return
