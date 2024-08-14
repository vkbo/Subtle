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

import json
import logging
import shutil
import sys

from copy import deepcopy
from pathlib import Path

from subtle.common import jsonEncode

from PyQt6.QtCore import (
    PYQT_VERSION, PYQT_VERSION_STR, QT_VERSION, QT_VERSION_STR, QSize,
    QStandardPaths, QSysInfo
)
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


DEFAULTS: dict = {
    "Sizes": {
        "mainWindow": [800, 600],
        "mainSplit": [300, 500],
        "contentSplit": [300, 300],
        "fileTreeColumns": [],
        "mediaViewColumns": [],
        "subsViewColumns": [],
    }
}


class Config:

    def __init__(self) -> None:

        self._data: dict[str, dict] = deepcopy(DEFAULTS)

        self.appName   = "Subtle"
        self.appHandle = "subtle"

        # Set Paths
        confRoot = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.ConfigLocation)
        )
        cacheRoot = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.CacheLocation)
        )
        self._confPath = confRoot.absolute() / self.appHandle  # The user config location
        self._cachePath = cacheRoot.absolute() / self.appHandle  # The user cache location
        self._homePath = Path.home().absolute()  # The user's home directory

        self._appPath = Path(__file__).parent.absolute()
        self._appRoot = self._appPath.parent

        self._confFile = self._confPath / "subtle.json"

        # Check Qt6 Versions
        self.verQtString   = QT_VERSION_STR
        self.verQtValue    = QT_VERSION
        self.verPyQtString = PYQT_VERSION_STR
        self.verPyQtValue  = PYQT_VERSION

        # Check Python Version
        self.verPyString = sys.version.split()[0]

        # Check OS Type
        self.osType    = sys.platform
        self.osLinux   = False
        self.osWindows = False
        self.osDarwin  = False
        self.osUnknown = False
        if self.osType.startswith("linux"):
            self.osLinux = True
        elif self.osType.startswith("darwin"):
            self.osDarwin = True
        elif self.osType.startswith(("win32", "cygwin")):
            self.osWindows = True
        else:
            self.osUnknown = True

        # Other System Info
        self.hostName  = QSysInfo.machineHostName()
        self.kernelVer = QSysInfo.kernelVersion()

        return

    ##
    #  Properties
    ##

    @property
    def dumpPath(self) -> Path:
        """Return a location for dumping files during a session."""
        path = self._cachePath / "dump"
        path.mkdir(exist_ok=True)
        return path

    ##
    #  Getters
    ##

    def getSize(self, key: str) -> QSize:
        """Get a size from config."""
        try:
            size = QSize(*self._data["Sizes"][key])
        except Exception:
            size = QSize()
        return size

    def getSizes(self, key: str) -> list[int]:
        """Get a list of sizes from config."""
        try:
            size = list(self._data["Sizes"][key])
        except Exception:
            size = []
        return size

    ##
    #  Setters
    ##

    def setSize(self, key: str, value: QSize) -> None:
        """Set a size in config."""
        if isinstance(value, QSize):
            self._data["Sizes"][key] = [value.width(), value.height()]
        return

    def setSizes(self, key: str, value: list[int]) -> None:
        """Set a size in config."""
        if isinstance(value, list):
            try:
                self._data["Sizes"][key] = [int(x) for x in value]
            except Exception as e:
                logger.error("Problem when saving sizes list", exc_info=e)
        return

    ##
    #  Methods
    ##

    def initialise(self) -> None:
        """Initialise the config."""
        self._confPath.mkdir(exist_ok=True)
        self._cachePath.mkdir(exist_ok=True)
        return

    def cleanup(self) -> None:
        """Called before exit to clean up cache."""
        path = self._cachePath / "dump"
        if path.exists():
            logger.debug("Clearing session cache")
            shutil.rmtree(path)
        return

    def localisation(self, app: QApplication) -> None:
        return

    def load(self) -> None:
        """Load the app config."""
        if self._confFile.is_file():
            try:
                logger.debug("Loading config")
                with open(self._confFile, mode="r", encoding="utf-8") as fo:
                    data = json.load(fo)
                self._storeConfigGroup(data, "Sizes")
            except Exception as e:
                logger.error("Could not load config", exc_info=e)
        return

    def save(self) -> None:
        """Save the app config."""
        try:
            logger.debug("Saving config")
            with open(self._confFile, mode="w+", encoding="utf-8") as fo:
                fo.write(jsonEncode(self._data, nmax=2))
        except Exception:
            logger.error("Could not save config")
        return

    ##
    #  Internal Functions
    ##

    def _storeConfigGroup(self, data: dict, group: str) -> None:
        """Process a group from config and save the data."""
        if isinstance(data, dict) and group in self._data:
            loaded = data.get(group, {})
            default = DEFAULTS.get(group, {})
            values = {k: v for k, v in loaded.items() if k in default}
            self._data[group].update(values)
        return
