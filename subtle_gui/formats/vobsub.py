"""
Subtle - VobSub File Object
===========================

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

import logging

from typing import TYPE_CHECKING, NamedTuple

from subtle_gui.common import decodeTS
from subtle_gui.formats.base import FrameBase, SubtitlesBase

if TYPE_CHECKING:
    from pathlib import Path

    from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)

HEADER_LEN = 6
MPEG2_HEADER_LEN = 14


class IdxEntry(NamedTuple):
    """An entry in a VobSub IDX file."""

    timestamp: int
    filepos: int


class VobSubs(SubtitlesBase):
    """VobSub Subtitles.

    Reference: https://github.com/SubtitleEdit/subtitleedit
    """

    def __init__(self) -> None:
        super().__init__()

        # IDX Data
        self._idx: list[IdxEntry] = []
        self._forced: bool = False
        self._palette: list[str] = []

    def read(self, path: Path) -> None:
        """Read a VobSub file."""
        self._path = path
        try:
            self._readIdxData(path.with_suffix(".idx"))
        except Exception as exc:
            logger.error("Could not read VobSub IDX file: %s", self._path, exc_info=exc)
        try:
            self._readSubData(path.with_suffix(".sub"))
        except Exception as exc:
            logger.error("Could not read VobSub SUB file: %s", self._path, exc_info=exc)

    def write(self, path: Path | None = None) -> None:
        """Write a VobSub file."""
        raise NotImplementedError("Cannot write VobSub files.")

    def copyFrames(self, other: SubtitlesBase) -> None:
        """Copy frames from another subtitle object."""
        return super()._copyFrames(VobSubFrame, other)

    ##
    #  Internal Functions
    ##

    def _readIdxData(self, path: Path) -> None:
        """Read IDX data from file."""
        self._idx = []
        with open(path, mode="r", encoding="utf-8") as fo:
            for line in fo:
                if line.startswith("timestamp:"):
                    one, _, two = line.partition(",")
                    ts = decodeTS(one.partition(":")[2].strip(), fmt="IDX")
                    fp = int("0x" + two.partition(":")[2].strip(), 16)
                    self._idx.append(IdxEntry(timestamp=ts, filepos=fp))
                elif line.startswith("forced subs:"):
                    self._forced = line.partition(":")[2].strip().lower() == "on"
                elif line.startswith("palette:"):
                    self._palette = [p.strip() for p in line.partition(":")[2].split(",")]

        print(self._idx[:10])

    def _readSubData(self, path: Path) -> None:
        """Read SUB data from file."""
        with open(path, mode="rb") as fo:
            for entry in self._idx[:10]:
                fo.seek(entry.filepos)
                buffer = fo.read(0x0800)
                vsp = VobSubPack(buffer, entry)  # noqa: F841


def isMpeg2PackHeader(data: bytes) -> bool:
    """Check if data is a Mpeg2 pack header."""
    return len(data) >= 4 and int.from_bytes(data[0:4]) == 0x000001BA


def isPrivateStream1(data: bytes, index: int) -> bool:
    """Check if data is a private stream."""
    return len(data) >= index + 4 and int.from_bytes(data[index + 3 : index + 4]) == 0xBD


def isPrivateStream2(data: bytes, index: int) -> bool:
    """Check if data is a private stream."""
    return len(data) >= index + 4 and int.from_bytes(data[index + 3 : index + 4]) == 0xBF


def isPaddingStream(data: bytes, index: int) -> bool:
    """Check if data is a padding stream."""
    return len(data) >= index + 4 and int.from_bytes(data[index + 3 : index + 4]) == 0xBE


def isProgramEnd(data: bytes, index: int) -> bool:
    """Check if data is a program end."""
    return len(data) >= index + 4 and int.from_bytes(data[index + 3 : index + 4]) == 0xB9


def isSubtitleStreamId(streamId: int) -> bool:
    """Check if streamId is a subtitle stream."""
    return 0x20 <= streamId <= 0x3F


def isSubtitlePack(data: bytes) -> bool:
    """Check if data is a subtitle pack."""
    if isMpeg2PackHeader(data) and isPrivateStream1(data, MPEG2_HEADER_LEN):
        length = int.from_bytes(data[MPEG2_HEADER_LEN + 8 : MPEG2_HEADER_LEN + 9])
        offset = MPEG2_HEADER_LEN + 9 + length
        return isSubtitleStreamId(int.from_bytes(data[offset : offset + 1]))
    return False


class VobSubFrame(FrameBase):
    """VobSub Subtitle Frame."""

    def __init__(self, index: int, start: int, end: int, text: list[str]) -> None:
        super().__init__(index=index)
        self._start = start
        self._end = end
        self._text = text

    @classmethod
    def fromFrame(cls, index: int, other: FrameBase) -> FrameBase:
        """Populate from another frame."""
        return cls(index, other.start, other.end, other.text)

    @property
    def imageBased(self) -> bool:
        """VobSub frames are images."""
        return True

    def getImage(self) -> QImage:
        """There is no image."""
        raise NotImplementedError


class VobSubPack:
    """A VobSub pack in a SUB file."""

    __slots__ = ("_buffer", "_idx", "_mpeg2", "_pes")

    def __init__(self, buffer: bytes, idxEntry: IdxEntry) -> None:
        self._buffer = buffer
        self._idx: IdxEntry = idxEntry
        self._pes: PacketizedElementaryStream | None = None
        self._mpeg2: Mpeg2Header | None = None

        if isMpeg2PackHeader(buffer):
            self._mpeg2 = Mpeg2Header(buffer)
            self._pes = PacketizedElementaryStream(buffer, MPEG2_HEADER_LEN)
        elif isPrivateStream1(buffer, 0):
            self._pes = PacketizedElementaryStream(buffer, 0)

        print(">", self._idx)
        print(" ", self._mpeg2)
        print(" ", self._pes)
        if pes := self._pes:
            print(f" PES Data: {int.from_bytes(pes.data[:8]):016X}... ({len(pes.data)} bytes)")


class PacketizedElementaryStream:
    """A packetized elementary stream (PES) in a VobSub file."""

    __slots__ = (
        "_buffer",
        "_data",
        "_decodeTimestamp",
        "_flags6",
        "_flags7",
        "_headerDataLength",
        "_index",
        "_length",
        "_presentationTimestamp",
        "_startCode",
        "_streamId",
        "_subPictureStreamId",
        "_valid",
    )

    def __init__(self, buffer: bytes, index: int) -> None:
        self._buffer = buffer
        self._data = b""
        self._index = index
        self._valid = len(buffer) >= index + 8

        self._startCode = int.from_bytes(buffer[index : index + 3])
        self._streamId = int.from_bytes(buffer[index + 3 : index + 4])
        self._length = int.from_bytes(buffer[index + 4 : index + 6])
        self._flags6 = int.from_bytes(buffer[index + 6 : index + 7])
        self._flags7 = int.from_bytes(buffer[index + 7 : index + 8])
        self._headerDataLength = int.from_bytes(buffer[index + 8 : index + 9])

        # idx6 = buffer[index + 6]
        # self._originalOrCopy = idx6 & 0b00000001
        # self._copyright = idx6 & 0b00000010
        # self._dataAlignmentIndicator = idx6 & 0b00000100
        # self._priority = idx6 & 0b00001000
        # self._scramblingControl = (idx6 & 0b00110000) >> 4

        # idx7 = buffer[index + 7]
        # self._extensionFlag = idx7 & 0b00000010
        # self._additionalCopyInfoFlag = idx7 & 0b00000100
        # self._crcFlag = idx7 & 0b00001000
        # self._dsmTrickModeFlag = idx7 & 0b00001000
        # self._esRateFlag = idx7 & 0b00010000
        # self._elementaryStreamClockReferenceFlag = idx7 & 0b00100000
        # self._presentationTimestampDecodeTimestampFlags = idx7 >> 6

        self._subPictureStreamId: int | None = None
        self._presentationTimestamp: int | None = None
        self._decodeTimestamp: int | None = None

        self._processData(index)

    def __repr__(self) -> str:
        """Return a string representation of the PES."""
        return (
            f"<PacketizedElementaryStream StartCode={self._startCode:06X}, StreamId={self._streamId:02X}, "
            f"Length={self._length}, Flags={self._flags6:02X}{self._flags7:02X}, "
            f"HeaderDataLength={self._headerDataLength} SubPictureStreamId={self._subPictureStreamId}, "
            f"PresentationTimestamp={self._presentationTimestamp}, DecodeTimestamp={self._decodeTimestamp}>"
        )

    @property
    def data(self) -> bytes:
        """Return the PES data."""
        return self._data

    ##
    #  Internal Functions
    ##

    def _processData(self, index: int) -> None:
        """Process the PES data."""
        buffer = self._buffer
        length = len(buffer)

        idOffset = index + 9 + self._headerDataLength
        if length >= idOffset and self._streamId == 0xBD and 0x20 <= (subId := buffer[idOffset]) < 0x40:
            self._subPictureStreamId = subId

        tempIdx = index + 9
        ptsDtsFlags = self._flags7 >> 6

        if length >= tempIdx + 5 and ptsDtsFlags in (0b10, 0b11):
            pts = buffer[tempIdx + 4] >> 1
            pts += buffer[tempIdx + 3] << 7
            pts += (buffer[tempIdx + 2] & 0b11111110) << 14
            pts += buffer[tempIdx + 1] << 22
            pts += (buffer[tempIdx] & 0b00001110) << 29
            self._presentationTimestamp = pts
            tempIdx += 5

        if length >= tempIdx + 5 and ptsDtsFlags == 0b11:
            dts = buffer[tempIdx + 4] >> 1
            dts += buffer[tempIdx + 3] << 7
            dts += (buffer[tempIdx + 2] & 0b11111110) << 14
            dts += buffer[tempIdx + 1] << 22
            dts += (buffer[tempIdx] & 0b00001110) << 29
            self._decodeTimestamp = dts

        dataOffset = idOffset + 1
        dataLength = self._length - self._headerDataLength - 4
        if dataLength > 0:
            self._data = buffer[dataOffset : min(dataOffset + dataLength, length)]


class Mpeg2Header:
    """An Mpeg2 header in a VobSub file."""

    __slots__ = ("_buffer", "_muxRate", "_packId", "_startCode", "_stuffingLength")

    def __init__(self, buffer: bytes) -> None:
        self._buffer = buffer
        self._startCode = int.from_bytes(buffer[0:3])
        self._packId = int.from_bytes(buffer[3:4])
        self._muxRate = int.from_bytes(buffer[10:13]) >> 2
        self._stuffingLength = int.from_bytes(buffer[13:14]) & 0b00000111

    def __repr__(self) -> str:
        """Return a string representation of the Mpeg2 header."""
        return (
            f"<Mpeg2Header StartCode={self._startCode:06X}, PackId={self._packId:02X}, "
            f"ProgramMuxRate={self._muxRate}, PackStuffingLength={self._stuffingLength}>"
        )
