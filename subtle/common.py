"""
Subtle – Common Functions
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

import json
import logging

from math import modf
from typing import Any

logger = logging.getLogger(__name__)


def checkInt(value: Any, default: int) -> int:
    """Check if a variable is an integer."""
    try:
        return int(value)
    except Exception:
        return default


def formatInt(value: int) -> str:
    """Formats an integer with k, M, G etc."""
    if not isinstance(value, int):
        return "ERR"

    fVal = float(value)
    if fVal > 1000.0:
        for pF in ["k", "M", "G", "T", "P", "E"]:
            fVal /= 1000.0
            if fVal < 1000.0:
                if fVal < 10.0:
                    return f"{fVal:4.2f}\u202f{pF}"
                elif fVal < 100.0:
                    return f"{fVal:4.1f}\u202f{pF}"
                else:
                    return f"{fVal:3.0f}\u202f{pF}"

    return str(value) + "\u202f"


def jsonEncode(data: dict | list | tuple, n: int = 0, nmax: int = 0) -> str:
    """Encode a dictionary, list or tuple as a json object or array, and
    indent from level n up to a max level nmax if nmax is larger than 0.
    """
    if not isinstance(data, (dict, list, tuple)):
        return "[]"

    buffer = []
    indent = ""

    for chunk in json.JSONEncoder().iterencode(data):
        if chunk == "":  # pragma: no cover
            # Just a precaution
            continue

        first = chunk[0]
        if chunk in ("{}", "[]"):
            buffer.append(chunk)

        elif first in ("{", "["):
            n += 1
            indent = "\n"+"  "*n
            if n > nmax and nmax > 0:
                buffer.append(chunk)
            else:
                buffer.append(chunk[0] + indent + chunk[1:])

        elif first in ("}", "]"):
            n -= 1
            indent = "\n"+"  "*n
            if n >= nmax and nmax > 0:
                buffer.append(chunk)
            else:
                buffer.append(indent + chunk)

        elif first == ",":
            if n > nmax and nmax > 0:
                buffer.append(chunk)
            else:
                buffer.append(chunk[0] + indent + chunk[1:].lstrip())

        else:
            buffer.append(chunk)

    return "".join(buffer)


def formatTS(value: float) -> str:
    """Format float as HH:MM:SS,uuu timestamp."""
    i, f = int(value), round(modf(value)[0]*1000)
    return f"{i//3600:02d}:{i%3600//60:02d}:{i%60:02d},{f:03d}"


def decodeTS(value: str | None, default: float = 0.0) -> float:
    """Decode a time stamp to seconds."""
    if isinstance(value, str):
        try:
            result = 0.0
            bits = value.replace(",", ".").split(":")
            size = len(bits)
            if size > 0:
                result += float(bits[-1])
            if size > 1:
                result += 60*float(bits[-2])
            if size > 2:
                result += 3600*float(bits[-3])
            return result
        except Exception:
            pass
    return default
