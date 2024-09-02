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

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QHBoxLayout, QWidget

logger = logging.getLogger(__name__)


class GuiImageViewer(QWidget):

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._imageSize = QRect(0, 0, 0, 0)

        # Image Widget
        self.imageView = QGraphicsView(self)
        self.imageView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.imageView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Assemble
        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.imageView)

        self.setLayout(self.outerBox)

        return

    def setImage(self, image: QImage) -> None:
        """Display an image of subtitles."""
        self._imageSize = image.rect()
        scene = QGraphicsScene(self)
        scene.addPixmap(QPixmap.fromImage(image))
        scene.setSceneRect(QRectF(self._imageSize))
        self.imageView.setScene(scene)
        self._updateSizes()
        return

    ##
    #  Event
    ##

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Capture resize to update image scaling."""
        super().resizeEvent(event)
        self._updateSizes()
        return

    ##
    #  Internal Functions
    ##

    def _updateSizes(self) -> None:
        """Scale down the image if it does not fit."""
        if not self.imageView.rect().contains(self._imageSize):
            self.imageView.fitInView(QRectF(self._imageSize), Qt.AspectRatioMode.KeepAspectRatio)
        return
