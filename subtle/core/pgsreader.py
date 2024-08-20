"""
Subtle – Core PGS Reader
========================

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

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from time import time

from PyQt6.QtCore import QRect, QSize
from PyQt6.QtGui import QColor, QImage, qRgba

logger = logging.getLogger(__name__)

COMP_NORMAL = 0x00
COMP_ACQ    = 0x40
COMP_EPOCH  = 0x80

IMAGE_FILL = 0xff999999


class PGSReader:
    """PGS Reader Class.

    Reference:
    https://blog.thescorpius.com/index.php/2017/07/15/presentation-graphic-stream-sup-files-bluray-subtitle-format/
    """

    def __init__(self, path: Path) -> None:

        self._path = path
        self._data: list[DisplaySet] = []
        self._epochs: list[int] = []

        try:
            self._readData()
        except Exception as e:
            logger.error("Failed to read file data", exc_info=e)
            self._data = []

        self.debug()

        return

    def listEntries(self) -> list[dict]:
        """Generate a list of all subtitle entries in the file."""
        data = []
        prev = None
        for i, ds in enumerate(self._data):
            ts = ds.pcs.timestamp
            curr = {
                "index": i,
                "start": ts,
                "end": 0.0,
                "epoch": ds.pcs.compState == COMP_EPOCH,
                "clear": ds.isClearFrame(),
            }
            data.append(curr)
            if prev:
                prev["end"] = ts
            prev = curr
        return data

    def debug(self) -> None:
        """Debug function."""
        print("Ping!")
        print(len(self._data))
        for ds in self._data[:20]:
            # print(ds, list(ds.pcs.compObjects()), ds._wds[0], ds._ods)
            if not ds.isClearFrame():
                ds.render().save(f"image_{ds.pcs.compNumber}.png")
        return

    ##
    #  Internal Functions
    ##

    def _readData(self) -> None:
        """Read the raw PGS file data and store it as a list of display
        sets of related segments.
        """
        ds = None
        data: list[DisplaySet] = []
        with open(self._path, mode="rb") as fo:
            while h := fo.read(13):
                if len(h) < 13:
                    logger.warning("Invalid header '%s' of length %d", h[:2].hex(), len(h))
                    break

                pos = fo.tell() - 13
                if h[0:2] != b"PG":
                    logger.warning("Skipping invalid segment at position %d", pos)
                    fo.seek(max(1, pos + 1))
                    continue

                ts = int.from_bytes(h[2:6])
                tt = int.from_bytes(h[10:11])
                sz = int.from_bytes(h[11:13])
                dd = fo.read(sz) if sz > 0 else b""
                match tt:
                    case 0x16:  # Presentation Composition Segment
                        ds = DisplaySet(PresentationSegment(ts, dd))
                    case 0x17 if ds is not None:  # Window Definition Segment
                        ds.addWDS(WindowSegment(ts, dd), pos)
                    case 0x14 if ds is not None:  # Palette Definition Segment
                        ds.addPDS(PaletteSegment(ts, dd), pos)
                    case 0x15 if ds is not None:  # Object Definition Segment
                        ds.addODS(ObjectSegment(ts, dd), pos)
                    case 0x80 if ds and ds.isValid():  # End of Display Set Segment
                        data.append(ds)
                        ds = None
                    case _:
                        logger.warning("Invalid or unexpected segment type %02x at %d", tt, pos)

            if ds is not None:
                logger.warning("Data past last END segment, PGS data may be truncated")

        # Compute frames
        epochs: list[int] = []
        for i, ds in enumerate(data):
            if ds.pcs.compState == COMP_EPOCH:
                epochs.append(i)

        epochs.append(len(data))

        self._data = data
        self._epochs = epochs

        # print("\n".join(str(x) for x in self._data))

        return


class DisplaySet:

    __slots__ = ("_pcs", "_wds", "_pds", "_ods")

    def __init__(self, pcs: PresentationSegment) -> None:
        self._pcs: PresentationSegment = pcs
        self._wds: dict[int, QRect] = {}
        self._pds: dict[int, PaletteSegment] = {}
        self._ods: dict[int, list[ObjectSegment]] = {}
        return

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} composition={self._pcs.compNumber} "
            f"windows={len(self._wds)} palettes={len(self._pds)} objects={len(self._ods)}>"
        )

    @property
    def pcs(self) -> PresentationSegment:
        return self._pcs

    @property
    def timestamp(self) -> float:
        return self._pcs.timestamp

    def addWDS(self, wds: WindowSegment, pos: int) -> None:
        """Save all windows defined in the segment."""
        if wds.valid:
            for idx, rect in wds.windows():
                self._wds[idx] = rect
        else:
            logger.warning("Skipping invalid WindowSegment at pos %d", pos)
        return

    def addPDS(self, pds: PaletteSegment, pos: int) -> None:
        """Save the segment mapped to its id."""
        if pds.valid:
            self._pds[pds.id] = pds
        else:
            logger.warning("Skipping invalid PaletteSegment at pos %d", pos)
        return

    def addODS(self, ods: ObjectSegment, pos: int) -> None:
        """Save the segment mapped to its id."""
        if ods.valid:
            if (oid := ods.id) not in self._ods:
                self._ods[oid] = [ods]
            else:
                self._ods[oid].append(ods)
        else:
            logger.warning("Skipping invalid ObjectSegment at pos %d", pos)
        return

    def isValid(self) -> bool:
        return self._pcs is not None and self._pcs.valid and len(self._wds) > 0

    def isClearFrame(self) -> bool:
        return self._pcs.compState == COMP_NORMAL and self._pcs.compObjectCount == 0

    def render(self) -> QImage:
        """Render the content of the display set on a QImage."""
        start = time()
        comp = self._pcs.compNumber
        image = QImage(self._pcs.size, QImage.Format.Format_ARGB32)
        image.fill(IMAGE_FILL)

        if pds := self._pds.get(self._pcs.paletteID):
            palette = pds.palette()
            for oid, wid in self._pcs.compObjects():
                data = b""
                size = None
                length = 0
                for ods in self._ods.get(oid, []):
                    data += ods.rle
                    if ods.sequence & 0x80 == 0x80:
                        size = ods.size
                        length = ods.length

                if length != len(data):
                    logger.warning("Inconsistent image data length in composition %d", comp)
                    length = len(data)  # Try to render what we have
                if size is None:
                    logger.error("Size not defined for composition %d", comp)
                    break
                if (window := self._wds.get(wid)) is None:
                    logger.error("Unknown window %d in composition %d", wid, comp)
                    break

                p = 0
                x = wx = window.x()
                y = window.y()
                data += b"\x00\x00\x00"  # In case data is truncated or malformed
                while p < length:
                    if (b1 := data[p]) > 0x00:
                        c = b1
                        n = 1
                        p += 1
                    elif (b2 := data[p+1]) <= 0x3f:
                        c = 0
                        n = b2
                        p += 2
                    elif b2 <= 0x7f:
                        c = 0
                        n = (b2 & 0x3f)*256 + data[p+2]
                        p += 3
                    elif b2 <= 0xbf:
                        c = data[p+2]
                        n = b2 & 0x3f
                        p += 3
                    else:
                        c = data[p+3]
                        n = (b2 & 0x3f)*256 + data[p+2]
                        p += 4

                    color = palette[c]
                    for i in range(x, x + n):
                        image.setPixel(i, y, color)

                    x += n
                    if c == 0 and n == 0:  # End of line
                        x = wx
                        y += 1

        logger.info("Image rendered in %.3f ms", (time()-start)*1000)

        return image


class BaseSegment(ABC):

    __slots__ = ("_ts", "_data", "_valid")

    def __init__(self, ts: int, data: bytes) -> None:
        self._ts = ts
        self._data = data
        self._valid = False
        self.validate()
        return

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} t={self._ts/90000:.3f} "
            f"size={len(self._data)} valid={self._valid}>"
        )

    @property
    def valid(self) -> bool:
        return self._valid

    @property
    def timestamp(self) -> float:
        return self._ts / 90000.0

    @abstractmethod
    def validate(self) -> None:
        raise NotImplementedError


class PresentationSegment(BaseSegment):
    """Presentation Composition Segment

    The Presentation Composition Segment is used for composing a sub
    picture.
    """

    def validate(self) -> None:
        """Length is 11 + n*8"""
        size = len(self._data)
        self._valid = (size >= 11 and size % 8 == 3)
        return

    @property
    def size(self) -> QSize:
        """Size of the video."""
        return QSize(
            int.from_bytes(self._data[0:2]),
            int.from_bytes(self._data[2:4]),
        )

    @property
    def compNumber(self) -> int:
        """Number of this specific composition. It is incremented by one
        every time a graphics update occurs.
        """
        return int.from_bytes(self._data[5:7])

    @property
    def compState(self) -> int:
        """Type of this composition. Allowed values are:
        0x00: Normal
        0x40: Acquisition Point
        0x80: Epoch Start
        """
        return int.from_bytes(self._data[7:8])

    @property
    def paletteUpdate(self) -> bool:
        """Indicates if this PCS describes a Palette only Display
        Update. Allowed values are:
        0x00: False
        0x80: True
        """
        return int.from_bytes(self._data[8:9]) == 0x80

    @property
    def paletteID(self) -> int:
        """ID of the palette to be used in the Palette only Display
        Update.
        """
        return int.from_bytes(self._data[9:10])

    @property
    def compObjectCount(self) -> int:
        """Number of composition objects defined in this segment."""
        return int.from_bytes(self._data[10:11])

    def compObjects(self) -> Iterable[tuple[int, int]]:
        """The composition objects, also known as window information
        objects, define the position on the screen of every image that
        will be shown.

        These also contain cropping information, which we don't care
        about, and skip. We only return the Object ID and Window ID of
        each entry. They also contain the x and y offset of each window
        and object, but we already have that information elsewhere, so
        we skip bytes 5 to 8.
        """
        pos = 11
        size = len(self._data)
        while pos < size:
            o = int.from_bytes(self._data[pos:pos+2])    # Object ID
            w = int.from_bytes(self._data[pos+2:pos+3])  # Window ID
            f = int.from_bytes(self._data[pos+3:pos+4])  # Crop flag, only used for offset
            pos += (16 if f == 0x40 else 8)
            yield o, w
        return


class WindowSegment(BaseSegment):
    """Window Definition Segment

    This segment is used to define the rectangular area on the screen
    where the sub picture will be shown. This rectangular area is called
    a Window. This segment can define several windows, and all the
    fields from Window ID up to Window Height will repeat each other in
    the segment defining each window.
    """

    def validate(self) -> None:
        """Length is 1 + n*9"""
        size = len(self._data)
        self._valid = (size >= 10 and size % 9 == 1)
        return

    @property
    def count(self) -> int:
        return int.from_bytes(self._data[0:1])

    def windows(self) -> Iterable[tuple[int, QRect]]:
        """Iterate over windows defined in the segment."""
        for pos in range(1, len(self._data), 9):
            yield int.from_bytes(self._data[pos:pos+1]), QRect(
                int.from_bytes(self._data[pos+1:pos+3]),
                int.from_bytes(self._data[pos+3:pos+5]),
                int.from_bytes(self._data[pos+5:pos+7]),
                int.from_bytes(self._data[pos+7:pos+9]),
            )
        return


class PaletteSegment(BaseSegment):
    """Palette Definition Segment

    This segment is used to define a palette for color conversion.
    """
    __slots__ = ("_col")

    def validate(self) -> None:
        """Length is 2 + n*5"""
        size = len(self._data)
        self._valid = (size >= 7 and size % 5 == 2)
        self._col: dict[int, QColor] = {}
        return

    @property
    def id(self) -> int:
        """ID of the palette."""
        return int.from_bytes(self._data[0:1])

    @property
    def version(self) -> int:
        """Version of this palette within the Epoch."""
        return int.from_bytes(self._data[1:2])

    def palette(self) -> list[int]:
        """Generate a 256 colour palette from the object.

        YUV conversion assuming Y range 16-235 and Cb/Cr range 16-240.
        """
        palette = [IMAGE_FILL] * 256
        for pos in range(2, len(self._data), 5):
            i, y, cr, cb, a = tuple(self._data[pos:pos+5])
            y -= 16
            cb -= 128
            cr -= 128
            r = 1.164*y + 1.793*cr
            g = 1.164*y - 0.213*cb - 0.533*cr
            b = 1.164*y + 2.112*cb
            palette[i] = qRgba(int(r), int(g), int(b), a)
        # print([f"{p:08x}" for p in palette])
        return palette


class ObjectSegment(BaseSegment):
    """Object Definition Segment

    This segment defines the graphics object. These are images with
    rendered text on a transparent background.
    """

    def validate(self) -> None:
        """The header is 11 bytes, followed by the raw image data."""
        self._valid = len(self._data) >= 11
        return

    @property
    def id(self) -> int:
        """ID of this object."""
        return int.from_bytes(self._data[0:2])

    @property
    def version(self) -> int:
        """Version of this object."""
        return int.from_bytes(self._data[2:3])

    @property
    def sequence(self) -> int:
        """If the image is split into a series of consecutive fragments,
        the last fragment has this flag set. Possible values:
        0x40: Last in sequence
        0x80: First in sequence
        0xC0: First and last in sequence (0x40 | 0x80)
        """
        return int.from_bytes(self._data[3:4])

    @property
    def length(self) -> int:
        """The length of the Run-length Encoding (RLE) data buffer with
        the compressed image data. The stored value also includes the
        image size, which is the first 4 bytes of the first sequence.
        We subtract this value here.
        """
        return int.from_bytes(self._data[4:7]) - 4

    @property
    def size(self) -> QSize:
        """Size of the image."""
        return QSize(
            int.from_bytes(self._data[7:9]),
            int.from_bytes(self._data[9:11]),
        )

    @property
    def rle(self) -> bytes:
        """This is the image data compressed using Run-length Encoding (RLE).
        The size of the data is defined in the Object Data Length field.
        """
        pos = 4 if self.sequence == 0x40 else 11
        return self._data[pos:]
