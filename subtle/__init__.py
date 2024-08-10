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
import sys

from PyQt6.QtWidgets import QApplication
from subtle.config import Config
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
__date__       = "2024-08-10"

logger = logging.getLogger(__name__)


##
#  Main Program
##

CONFIG = Config()


def main(sysArgs: list | None = None) -> GuiMain | None:
    """Parse command line, set up logging, and launch main GUI."""
    if sysArgs is None:
        sysArgs = sys.argv[1:]

    # Valid Input Options
    shortOpt = "hv"
    longOpt = [
        "help",
        "version",
        "info",
        "debug",
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
        "     --info     Print additional runtime information.\n"
        "     --debug    Print debug output. Includes --info.\n"
    )

    # Defaults
    logLevel = logging.WARN
    logFormat = "{levelname:8}  {message:}"

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
        elif inOpt == "--info":
            logLevel = logging.INFO
        elif inOpt == "--debug":
            logLevel = logging.DEBUG
            logFormat  = "[{asctime:}]  {filename:>18}:{lineno:<4d}  {levelname:8}  {message:}"

    # Setup Logging
    pkgLogger = logging.getLogger(__package__)
    pkgLogger.setLevel(logLevel)
    if len(pkgLogger.handlers) == 0:
        # Make sure we only create one logger (mostly an issue with tests)
        cHandle = logging.StreamHandler()
        cHandle.setFormatter(logging.Formatter(fmt=logFormat, style="{"))
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
    CONFIG.localisation(app)

    # Launch main GUI
    gui = GuiMain()
    gui.show()

    sys.exit(app.exec())
