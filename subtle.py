#!/usr/bin/env python3
"""
Subtle – Start Script
=====================
"""
import os
import sys

os.curdir = os.path.abspath(os.path.dirname(__file__))

if __name__ == "__main__":
    import subtle
    subtle.main(sys.argv[1:])
