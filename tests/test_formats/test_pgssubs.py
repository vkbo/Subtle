"""
Test – PGS Subs
===============

This file is a part of Subtle
Copyright (C) Veronica Berglyd Olsen

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
"""  # noqa

from __future__ import annotations

from PyQt6.QtGui import qRgba

from subtle_gui.formats.pgssubs import (
    IMAGE_FILL,
    ObjectSegment,
    PaletteSegment,
    PresentationSegment,
    SegmentBase,
    WindowSegment,
)


def testPGSSubs_SegmentBase() -> None:
    """Test base segment initialisation and validation dispatch."""

    class DummySegment(SegmentBase):
        def validate(self) -> None:
            self._valid = self._data == b"ok"

    segment = DummySegment(11111, b"ok")
    invalid = DummySegment(11112, b"no")

    assert segment.valid is True
    assert segment.timestamp == 11111
    assert "DummySegment" in repr(segment)

    assert invalid.valid is False
    assert invalid.timestamp == 11112


def testPGSSubs_PresentationSegment() -> None:
    """Test parsing of PGS presentation segment headers and objects."""
    data = bytes.fromhex("0780 0438 10 0012 80 80 34 02 1234 05 40 0010 0020 0000 0000 0000 0000 5678 09 00 0030 0040")
    segment = PresentationSegment(67890, data)

    assert segment.valid is True
    assert segment.timestamp == 67890
    assert segment.size.width() == 1920
    assert segment.size.height() == 1080
    assert segment.compNumber == 0x0012
    assert segment.compState == 0x80
    assert segment.paletteUpdate is True
    assert segment.paletteID == 0x34
    assert segment.compObjectCount == 2

    objects = list(segment.compObjects())

    assert len(objects) == 2
    assert objects[0][0] == 0x1234
    assert objects[0][1] == 0x05
    assert objects[0][2].x() == 16
    assert objects[0][2].y() == 32
    assert objects[1][0] == 0x5678
    assert objects[1][1] == 0x09
    assert objects[1][2].x() == 48
    assert objects[1][2].y() == 64

    data = bytes.fromhex("0780 0438 10 0012 80 80 34")
    invalid = PresentationSegment(67891, data)

    assert invalid.valid is False


def testPGSSubs_WindowSegment() -> None:
    """Test parsing of PGS window segment headers and window entries."""
    data = bytes.fromhex("02 03 0010 0020 0030 0040 04 0050 0060 0070 0080")
    segment = WindowSegment(12345, data)

    assert segment.valid is True
    assert segment.timestamp == 12345
    assert segment.count == 2

    windows = list(segment.windows())

    assert len(windows) == 2
    assert windows[0][0] == 3
    assert windows[0][1].x() == 16
    assert windows[0][1].y() == 32
    assert windows[0][1].width() == 48
    assert windows[0][1].height() == 64
    assert windows[1][0] == 4
    assert windows[1][1].x() == 80
    assert windows[1][1].y() == 96
    assert windows[1][1].width() == 112
    assert windows[1][1].height() == 128

    data = bytes.fromhex("02 03 0010 0020 0030")
    invalid = WindowSegment(12346, data)

    assert invalid.valid is False


def testPGSSubs_PaletteSegment() -> None:
    """Test parsing of PGS palette segment headers and palette data."""
    data = bytes.fromhex("12 34 05 10 80 80 ff 06 20 80 80 00")
    segment = PaletteSegment(45000, data)

    assert segment.valid is True
    assert segment.timestamp == 45000
    assert segment.id == 0x12
    assert segment.version == 0x34

    palette = segment.palette()

    assert len(palette) == 256
    assert palette[0] == IMAGE_FILL.to_bytes(4, "little")
    assert palette[5] == qRgba(0, 0, 0, 255).to_bytes(4, "little")
    assert palette[6] == IMAGE_FILL.to_bytes(4, "little")

    data = bytes.fromhex("12 34 05 10 80 80")
    invalid = PaletteSegment(45001, data)

    assert invalid.valid is False


def testPGSSubs_ObjectSegment() -> None:
    """Test parsing of PGS object segment headers and payloads."""
    data = bytes.fromhex("1234 56 c0 000008 0014 000a deadbeef")
    segment = ObjectSegment(90000, data)

    assert segment.valid is True
    assert segment.timestamp == 90000
    assert segment.id == 0x1234
    assert segment.version == 0x56
    assert segment.sequence == 0xC0
    assert segment.length == 4
    assert segment.size.width() == 20
    assert segment.size.height() == 10
    assert segment.rle == bytes.fromhex("deadbeef")

    data = bytes.fromhex("1234 56 40 cafe")
    invalid = ObjectSegment(90001, data)

    assert invalid.valid is False
    assert invalid.sequence == 0x40
    assert invalid.rle == bytes.fromhex("cafe")
