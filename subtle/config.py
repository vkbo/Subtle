"""
Subtle – Main Config
====================

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

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class Config:

    def __init__(self) -> None:

        self.appName = "Subtle"

        return

    def initialise(self) -> None:
        return

    def localisation(self, app: QApplication) -> None:
        return

    def load(self) -> None:
        return
