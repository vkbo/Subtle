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
from pathlib import Path

from PyQt6.QtCore import QRect, QSize

logger = logging.getLogger(__name__)

COMP_NORMAL = 0x00
COMP_ACQ    = 0x40
COMP_EPOCH  = 0x80


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

        return

    def listEntries(self) -> list[dict]:
        """"""
        data = []
        prev = None
        for ds in self._data:
            ts = ds.pcs.timestamp
            curr = {
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
                        ds.addWDS(WindowSegment(ts, dd))
                    case 0x14 if ds is not None:  # Palette Definition Segment
                        ds.addPDS(PaletteSegment(ts, dd))
                    case 0x15 if ds is not None:  # Object Definition Segment
                        ds.addODS(ObjectSegment(ts, dd))
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
        self._wds: list[WindowSegment] = []
        self._pds: list[PaletteSegment] = []
        self._ods: list[ObjectSegment] = []
        return

    def __repr__(self) -> str:
        bits = []
        if self._pcs:
            bits.append("PCS")
        if self._wds:
            bits.append("WDS")
        bits.extend(["PDS"] * len(self._pds))
        bits.extend(["ODS"] * len(self._ods))
        segments = ":".join(bits)
        return f"<{self.__class__.__name__} segments={segments}>"

    @property
    def pcs(self) -> PresentationSegment:
        return self._pcs

    @property
    def wds(self) -> list[WindowSegment]:
        return self._wds

    @property
    def timestamp(self) -> float:
        return self._pcs.timestamp

    def addWDS(self, wds: WindowSegment) -> None:
        self._wds.append(wds)
        return

    def addPDS(self, pds: PaletteSegment) -> None:
        self._pds.append(pds)
        return

    def addODS(self, ods: ObjectSegment) -> None:
        self._ods.append(ods)
        return

    def isValid(self) -> bool:
        return self._pcs is not None and len(self._wds) > 0

    def isClearFrame(self) -> bool:
        return self._pcs.compState == COMP_NORMAL and self._pcs.compObjects == 0


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
    def timestamp(self) -> float:
        return self._ts / 90000.0

    @abstractmethod
    def validate(self) -> None:
        raise NotImplementedError


class PresentationSegment(BaseSegment):

    def validate(self) -> None:
        """"""
        self._valid = len(self._data) >= 11
        return

    @property
    def size(self) -> QSize:
        return QSize(
            int.from_bytes(self._data[0:2]),
            int.from_bytes(self._data[2:4]),
        )

    @property
    def compNumber(self) -> int:
        return int.from_bytes(self._data[5:7])

    @property
    def compState(self) -> int:
        return int.from_bytes(self._data[7:8])

    @property
    def compObjects(self) -> int:
        return int.from_bytes(self._data[10:11])


class WindowSegment(BaseSegment):

    def validate(self) -> None:
        """Length is 1 + n*9"""
        size = len(self._data)
        self._valid = (size >= 10 and size % 9 == 1)
        return

    @property
    def count(self) -> int:
        return int.from_bytes(self._data[0:1])

    def getWindow(self, index: int) -> QRect:
        pos = 1 + index*9
        return QRect(
            int.from_bytes(self._data[pos+1:pos+3]),
            int.from_bytes(self._data[pos+3:pos+5]),
            int.from_bytes(self._data[pos+5:pos+7]),
            int.from_bytes(self._data[pos+7:pos+9]),
        )


class PaletteSegment(BaseSegment):

    def validate(self) -> None:
        """"""
        self._valid = len(self._data) >= 7
        return


class ObjectSegment(BaseSegment):

    def validate(self) -> None:
        """"""
        self._valid = len(self._data) >= 11
        return
