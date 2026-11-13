from __future__ import annotations
from pathlib import Path as FilePath
import struct as Struct

import pytest as PytestLib

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.configuration.ConfigZero import (
    CONFIG_FIELD_COUNT as Count,
    CONFIG_OPAQUE_BYTES as Bytes,
    CONFIG_OWNER_COUNT as CountA,
    REFERENCE_ATOM_ID as IdInfo,
    REFERENCE_LENGTH as Length,
    REFERENCE_TREE_ID as IdInfoA,
    declared_opaque_split as DeclaredOpaqueSplit,
    encode_config0_stream as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.default.Registry import (
    ConfigOps,
    FieldOwners,
)
from convert.adapters.solidworks.programs.configuration.box.Program import (
    EncodeProgram as EncodeBoxConfigProgram,
    ReferenceLength as BoxReferenceLength,
)
from convert.adapters.solidworks.programs.configuration.box.Registry import (
    ConfigOps as BoxConfigOps,
    FieldOwners as BoxFieldOwners,
)

# centralizes shared evidence so every related assertion uses one value
KBytes = 88

# centralizes shared evidence so every related assertion uses one value
KBytesA = 66


# keeps this focused behavior isolated so regressions remain immediately visible
def Atoms(FeatureCount: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        ((IdInfo + Index, IdInfoA + 8 * Index) for Index in range(FeatureCount))
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestERBHEOTO() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in ConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(FieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
            "stringlist",
        } or KindName.startswith(("primitive:", "direct:"))
        assert "opaque" not in KindName
        assert "raw" not in KindName
        SourceCursor += FieldWidth
    assert SourceCursor == Length
    assert len(ConfigOps) == Count == 4341
    assert len(FieldOwners) == CountA == 1085


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/default/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDBCIET() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in BoxConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(BoxFieldOwners)
        assert "opaque" not in KindName.casefold()
        assert "raw" not in KindName.casefold()
        SourceCursor += FieldWidth
    assert SourceCursor == BoxReferenceLength == 25158
    assert len(EncodeBoxConfigProgram()) == BoxReferenceLength
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/box/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTVRPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/views/pair/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFVPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/fillet/views/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPVPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/pattern/views/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTFAFTEDS() -> None:
    SplitData = DeclaredOpaqueSplit(atoms=Atoms(3), part_name="TypedPart")
    assert SplitData["typed"] == SplitData["stream_bytes"]
    assert SplitData["accounted"] == SplitData["stream_bytes"]
    assert SplitData["opaque"] == Bytes == 0
    assert SplitData["operations"] == len(ConfigOps)
    assert SplitData["owners"] == len(FieldOwners)


def TestNameWidths() -> None:
    for PartName, Shift in (("P", -8), ("Part1RenamedLonger", 26)):
        Payload = EncodeConfig(PartName=PartName, Generation=19000)
        assert len(Payload) == 25476 + Shift
        assert Payload.find(PartName.encode("utf-16le")) == 48
        assert Payload.find(b"moVisualProperties_c") == 88 + Shift
        assert Payload.find(b"moUnitsTable_c") == 931 + Shift
        assert Payload[2796 + Shift : 2812 + Shift] == Struct.pack("<4I", 1, 1, 120, 1)
        assert Payload[19730 + Shift : 19734 + Shift] == bytes(4)


def TestRejectRaw() -> None:
    with PytestLib.raises(SldprtFormatError):
        _ = EncodeConfig(Generation=19000, PartRecordBody=b"")
