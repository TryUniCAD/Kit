# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from pathlib import Path as FilePath
from struct import pack_into as PackInto
from zipfile import ZipFile

from convert.Formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from convert.Formats.Fusion.Sketches.Dimensional.DimRecord import (
    DimRecordBody,
    ReadDimRecord,
)
from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import (
    KDimensionSpecs,
    KLinearDimension,
)


# native control changes exercise the complete archive decoder instead of replacing projected model records
def AlterDimRoles(Source: FilePath, CaseName: str) -> bytes:
    BulkData, Spans = ReadDesignZip(Source.read_bytes())
    Dimensions = tuple(
        SpanValue
        for SpanValue in Spans
        if SpanValue.IsPrimary and SpanValue.ClassGuid == KLinearDimension
    )
    assert len(Dimensions) == 2
    First, Second = Dimensions
    Native = ReadDimRecord(DimRecordBody(BulkData, First), First.ClassGuid)
    Start = First.PayloadOffset + 4
    Changed = bytearray(BulkData)
    if CaseName in ("reference", "unknown-flag"):
        Position = Start + Native.PrefixEnd + KDimensionSpecs[Native.Code].FlagOffset
        Changed[Position] = 1 if CaseName == "reference" else 2
    elif CaseName == "shared":
        assert First.EndOffset - Start == Second.EndOffset - Second.PayloadOffset - 4
        Changed[Second.PayloadOffset + 4 : Second.EndOffset] = BulkData[
            Start : First.EndOffset
        ]
    elif CaseName == "unsupported":
        PackInto("<Q", Changed, Start + Native.BindingOffset - 8, 0xDEAD)
    elif CaseName == "binding":
        Other = ReadDimRecord(DimRecordBody(BulkData, Second), Second.ClassGuid)
        PackInto(
            "<Q",
            Changed,
            Second.PayloadOffset + 4 + Other.BindingOffset + 1,
            Native.BindingId,
        )
    else:
        raise ValueError("Unknown dimensional role archive control")
    Buffer = BytesIO()
    with ZipFile(Source) as Before, ZipFile(Buffer, "w") as After:
        for NameValue in Before.namelist():
            After.writestr(
                NameValue,
                (
                    bytes(Changed)
                    if NameValue == KDesignPrefix + "BulkStream.dat"
                    else Before.read(NameValue)
                ),
            )
    return Buffer.getvalue()
