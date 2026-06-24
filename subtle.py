#!/usr/bin/env python3
"""
Subtle – Start Script
=====================
"""  # noqa

import os
import sys

os.curdir = os.path.abspath(os.path.dirname(__file__))

if __name__ == "__main__":
    import subtle_gui

    subtle_gui.main(sys.argv[1:])
