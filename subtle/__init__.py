"""
Subtle – Init File
==================

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

import getopt
import logging
import os
import sys

from typing import TYPE_CHECKING

from subtle.config import Config
from subtle.shared import SharedData

from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:  # pragma: no cover
    from subtle.guimain import GuiMain

# Package Meta
# ============

__package__    = "subtle"
__copyright__  = "Copyright 2024, Veronica Berglyd Olsen"
__license__    = "GPLv3"
__author__     = "Veronica Berglyd Olsen"
__maintainer__ = "Veronica Berglyd Olsen"
__email__      = "code@vkbo.net"
__version__    = "0.1.0"
__hexversion__ = "0x000100a0"
__date__       = "2024-10-11"

logger = logging.getLogger(__name__)


##
#  Main Program
##

CONFIG = Config()
SHARED = SharedData()

# ANSI Colours
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
WHITE  = "\033[97m"
END    = "\033[0m"

# Log Format Components
TIME = "[{asctime:}]"
FILE = "{filename:>18}"
LINE = "{lineno:<4d}"
LVLP = "{levelname:8}"
LVLC = "{levelname:17}"
TEXT = "{message:}"

# Read Environment
FORCE_COLOR = bool(os.environ.get("FORCE_COLOR"))
NO_COLOR    = bool(os.environ.get("NO_COLOR"))


def main(sysArgs: list | None = None) -> GuiMain | None:
    """Parse command line, set up logging, and launch main GUI."""
    if sysArgs is None:
        sysArgs = sys.argv[1:]

    # Valid Input Options
    shortOpt = "hvicd"
    longOpt = [
        "help",
        "version",
        "info",
        "debug",
        "color",
    ]

    helpMsg = (
        f"Subtle {__version__} ({__date__})\n"
        f"{__copyright__}\n"
        "\n"
        "This program is distributed in the hope that it will be useful,\n"
        "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
        "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\n"
        "GNU General Public Licence for more details.\n"
        "\n"
        "Usage:\n"
        " -h, --help     Print this message.\n"
        " -v, --version  Print program version and exit.\n"
        " -i, --info     Print additional runtime information.\n"
        " -d, --debug    Print debug output. Includes --info.\n"
        " -c, --color    Add ANSI colors to log output.\n"
    )

    # Defaults
    logLevel = logging.WARN
    fmtColor = FORCE_COLOR
    fmtLong  = False

    # Parse Options
    try:
        inOpts, inRemain = getopt.getopt(sysArgs, shortOpt, longOpt)
    except getopt.GetoptError as exc:
        print(helpMsg)
        print(f"ERROR: {str(exc)}")
        sys.exit(2)

    for inOpt, inArg in inOpts:
        if inOpt in ("-h", "--help"):
            print(helpMsg)
            sys.exit(0)
        elif inOpt in ("-v", "--version"):
            print("Subtle Version %s [%s]" % (__version__, __date__))
            sys.exit(0)
        elif inOpt in ("-i", "--info"):
            logLevel = logging.INFO
        elif inOpt in ("-d", "--debug"):
            fmtLong = True
            logLevel = logging.DEBUG
        elif inOpt in ("-c", "--color"):
            fmtColor = not NO_COLOR

    if fmtColor:
        # This will overwrite the default level names, and also ensure that
        # they can be converted back to integer levels
        logging.addLevelName(logging.DEBUG,    f"{BLUE}DEBUG{END}")
        logging.addLevelName(logging.INFO,     f"{GREEN}INFO{END}")
        logging.addLevelName(logging.WARNING,  f"{YELLOW}WARNING{END}")
        logging.addLevelName(logging.ERROR,    f"{RED}ERROR{END}")
        logging.addLevelName(logging.CRITICAL, f"{RED}CRITICAL{END}")

    logTxt = f"{LVLC}  {TEXT}" if fmtColor else f"{LVLP}  {TEXT}"
    logPos = f"{BLUE}{FILE}{END}:{WHITE}{LINE}{END}" if fmtColor else f"{FILE}:{LINE}"
    logFmt = f"{TIME}  {logPos}  {logTxt}" if fmtLong else logTxt

    # Setup Logging
    pkgLogger = logging.getLogger(__package__)
    pkgLogger.setLevel(logLevel)
    if len(pkgLogger.handlers) == 0:
        # Make sure we only create one logger (mostly an issue with tests)
        cHandle = logging.StreamHandler()
        cHandle.setFormatter(logging.Formatter(fmt=logFmt, style="{"))
        pkgLogger.addHandler(cHandle)

    logger.info("Starting Subtle %s (%s) %s", __version__, __hexversion__, __date__)

    # Finish initialising config
    CONFIG.initialise()

    from subtle.guimain import GuiMain

    app = QApplication([CONFIG.appName])
    app.setApplicationName(CONFIG.appName)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName(CONFIG.appName)

    # Run Config steps that require the QApplication
    CONFIG.load()
    CONFIG.fonts(app)
    CONFIG.localisation(app)

    # Launch main GUI
    gui = GuiMain()
    gui.show()

    sys.exit(app.exec())
