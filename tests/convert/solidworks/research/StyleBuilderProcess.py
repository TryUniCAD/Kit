from __future__ import annotations

from builtins import getattr as GetAttr, open as OpenFile
from codecs import lookup as FindCodec
from hashlib import sha256 as HashBytes
from importlib import import_module as ImportModule
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import cast as CastValue

KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))
KAuditValue = ImportModule(
    "tests.convert.solidworks.research.ConstructionGuard"
).BuildAudit(KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "defs")
AddAuditHook(KAuditValue.InspectEvent)
KStyles = ImportModule("builders.Styles")
KUnits = ImportModule("builders.Units")
KCore = ImportModule("Core")
KStreams = ImportModule("Streams")
KRegistry = ImportModule("Classes").registry()
KRequest = CastValue(list[dict[str, dict[str, object]]], LoadJson(InputStream.read()))
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))
assert not KAuditValue.DeniedReads
KAuditValue.BeginBuild()


def FieldsOf(Record: object) -> dict[str, object]:
    return CastValue(dict[str, object], GetAttr(Record, "f"))


def BuildRecords(InputData: dict[str, dict[str, object]]) -> list[object]:
    StyleData = KStyles.detail_definitions(**InputData["styles"])
    UnitInput = InputData["units"]
    if "definitions" in UnitInput:
        UnitTable = KUnits.units_table(**UnitInput)
    else:
        UnitTable = KUnits.unit_table_profile(**UnitInput)
    return [KCore.Obj("moDetailDefs_c", StyleData), UnitTable]


def RoundTrip(Record: object) -> tuple[object, bytes]:
    DocValue = KStreams.StreamDoc("rooted", {"base": 1}, [Record])
    BlobValue = CastValue(bytes, KStreams.store_rooted(DocValue, KRegistry, 19000))
    Decoded, Archive = KStreams.load_rooted(BlobValue, KRegistry, 1, 19000)
    assert Archive.left() == 0 and not Decoded.tail
    assert len(Decoded.roots) == 1
    assert KStreams.store_rooted(Decoded, KRegistry, 19000) == BlobValue
    return Decoded.roots[0], BlobValue


def InspectResult(InputData: dict[str, dict[str, object]]) -> dict[str, object]:
    StyleRoot, UnitRoot = BuildRecords(InputData)
    StyleRoot, StyleBytes = RoundTrip(StyleRoot)
    UnitRoot, UnitBytes = RoundTrip(UnitRoot)
    StyleData = FieldsOf(StyleRoot)
    UnitData = FieldsOf(UnitRoot)
    UnitItems = CastValue(list[dict[str, object]], UnitData["items"])
    UnitNodes = [Entry["o"] for Entry in UnitItems]
    TaskData = CastValue(dict[str, object], StyleData["fb8"])
    DimData = CastValue(dict[str, object], StyleData["f13b0"])
    Annotations = CastValue(dict[str, object], StyleData["f1f18"])
    return {
        "style_size": len(StyleBytes),
        "unit_size": len(UnitBytes),
        "style_hash": HashBytes(StyleBytes).hexdigest(),
        "unit_hash": HashBytes(UnitBytes).hexdigest(),
        "standard": StyleData["f10"],
        "font": CastValue(dict[str, object], StyleData["f90"])["f08"],
        "exclusions": StyleData["f58"],
        "exclusion_count": StyleData["n58"],
        "task_labels": TaskData["items"],
        "task_count": TaskData["n"],
        "cutlist": [StyleData[Field] for Field in ("f200", "f208", "f210")],
        "linear_font": CastValue(
            dict[str, object], CastValue(dict[str, object], DimData["fe0"])["fe8"]
        )["f08"],
        "annotation_align": CastValue(dict[str, object], Annotations["f418"])["f1c"],
        "print_widths": list(CastValue(dict[str, object], StyleData["fb0"]).values()),
        "gtol_frames": CastValue(dict[str, object], StyleData["f9a0"])["n08"],
        "unit_count": UnitData["n"],
        "unit_classes": [GetAttr(NodeValue, "cls") for NodeValue in UnitNodes],
        "unit_codes": [FieldsOf(NodeValue).get("fb0") for NodeValue in UnitNodes],
        "unit_precision": [FieldsOf(NodeValue)["f0c"] for NodeValue in UnitNodes],
    }


def ProcessInput(InputData: dict[str, dict[str, object]]) -> dict[str, object]:
    Result: dict[str, object]
    PriorDenied = len(KAuditValue.DeniedReads)
    try:
        Result = InspectResult(InputData)
    except ValueError as ErrorInfo:
        Result = {"error": str(ErrorInfo)}
    assert len(KAuditValue.DeniedReads) == PriorDenied
    try:
        with OpenFile("/style-donor-input.SLDPRT", "rb"):
            raise AssertionError("the construction guard permitted a file open")
    except PermissionError:
        Result["read_blocked"] = True
    Result["import_reads"] = len(KAuditValue.ModuleReads)
    return Result


print(DumpJson([ProcessInput(InputData) for InputData in KRequest]))
