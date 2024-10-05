"""
Test – Common Functions
=======================

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

from subtle.common import closeItalics


def testCommon_closeItalics():
    """Test the closeItalics function."""
    assert closeItalics(["<i>Foo", "Bar</i>"]) == [
        "<i>Foo</i>", "<i>Bar</i>"
    ]
    assert closeItalics(["<i>Foo", "Bar", "Baz</i>"]) == [
        "<i>Foo</i>", "<i>Bar</i>", "<i>Baz</i>",
    ]
    assert closeItalics(["<i>Foo</i> foo <i>foo", "Bar</i>"]) == [
        "<i>Foo</i> foo <i>foo</i>", "<i>Bar</i>",
    ]
    return
