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

logger = logging.getLogger(__name__)


##
#  Encoder Functions
##

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
