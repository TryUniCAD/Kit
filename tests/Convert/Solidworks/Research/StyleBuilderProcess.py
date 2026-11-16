from __future__ import annotations

from builtins import open as OpenFile
from codecs import lookup as FindCodec
from importlib import import_module as ImportModule
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import cast as CastValue

# isolated style construction needs a stable code root without reading model fixtures
KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))

# import phase auditing prevents module initialization from consuming hidden saved document inputs
KAuditValue = ImportModule(
    "tests.Convert.Solidworks.Research.ConstructionGuard"
).BuildAudit(KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "defs")
AddAuditHook(KAuditValue.InspectEvent)

# the purity process must exercise the actual style constructor with authored settings
KStyles = ImportModule("builders.Styles")

# unit choices must use the shared graph builder under the construction guard
KUnits = ImportModule("builders.Units")

# the process must create real archive objects rather than test shaped replacements
KCore = ImportModule("Core")

# the actual archive codec must verify that constructed style graphs are serializable
KStreams = ImportModule("Streams")

# native class schemas must load before strict construction forbids filesystem discovery
KRegistry = ImportModule("Classes").registry()

# separate construction keeps process orchestration from obscuring forbidden input dependencies
KBuildRecords = ImportModule(
    "tests.Convert.Solidworks.Research.StyleProcessBuild"
).BuildRecords

# generated records must survive real codec boundaries before their fields are reported
KRoundTrip = ImportModule(
    "tests.Convert.Solidworks.Research.StyleProcessCodec"
).RoundTrip

# parent checks need decoded semantic evidence rather than constructor implementation details
KInspectResult = ImportModule(
    "tests.Convert.Solidworks.Research.StyleProcessReport"
).InspectResult

# semantic requests must arrive through standard input without fixture file access
KRequest = CastValue(list[dict[str, dict[str, object]]], LoadJson(InputStream.read()))

# codec initialization must not masquerade as a donor read during strict construction
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))
assert not KAuditValue.DeniedReads
KAuditValue.BeginBuild()


# each authored case must expose construction failures and prove forbidden reads remain blocked
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
