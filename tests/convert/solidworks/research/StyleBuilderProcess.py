from __future__ import annotations

from builtins import open as OpenFile
from codecs import lookup as FindCodec
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
KBuildRecords = ImportModule(
    "tests.convert.solidworks.research.StyleProcessBuild"
).BuildRecords
KRoundTrip = ImportModule(
    "tests.convert.solidworks.research.StyleProcessCodec"
).RoundTrip
KInspectResult = ImportModule(
    "tests.convert.solidworks.research.StyleProcessReport"
).InspectResult
KRequest = CastValue(list[dict[str, dict[str, object]]], LoadJson(InputStream.read()))
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))
assert not KAuditValue.DeniedReads
KAuditValue.BeginBuild()


def ProcessInput(InputData: dict[str, dict[str, object]]) -> dict[str, object]:
    Result: dict[str, object]
    PriorDenied = len(KAuditValue.DeniedReads)
    try:
        StyleRoot, UnitRoot = KBuildRecords(InputData, KStyles, KUnits, KCore)
        StyleRoot, StyleBytes = KRoundTrip(StyleRoot, KStreams, KRegistry)
        UnitRoot, UnitBytes = KRoundTrip(UnitRoot, KStreams, KRegistry)
        Result = KInspectResult(StyleRoot, UnitRoot, StyleBytes, UnitBytes)
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
