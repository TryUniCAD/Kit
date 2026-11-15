from __future__ import annotations

from builtins import open as OpenFile
from codecs import lookup as FindCodec
from importlib import import_module as ImportModule
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import cast as CastValue

# audited metadata construction needs an explicit repository root without depending on ambient imports
KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))

from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

# construction purity must cover builder imports before any donor access can occur
KAuditValue = BuildAudit(KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "defs")
AddAuditHook(KAuditValue.InspectEvent)

# the audited child must exercise the actual metadata builder rather than a surrogate
KMetadata = ImportModule("builders.Metadata")

# real archive boundaries must expose malformed metadata rather than accepting constructed objects
KStreams = ImportModule("Streams")

# shared native class dispatch must be fixed before strict construction forbids directory reads
KRegistry = ImportModule("Classes").registry()

# focused construction keeps audited orchestration independent from individual stream creation details
KBuildStreams = ImportModule(
    "tests.convert.solidworks.research.MetadataProcessBuild"
).BuildStreams

# complete codec verification must finish before semantic observations can be accepted
KDecodeStreams = ImportModule(
    "tests.convert.solidworks.research.MetadataProcessCodec"
).DecodeStreams

# parent assertions need observations from decoded records instead of builder implementation details
KInspectResult = ImportModule(
    "tests.convert.solidworks.research.MetadataProcessReport"
).InspectResult

# authored requests must enter through process input rather than runtime fixture files
KRequest = CastValue(list[dict[str, dict[str, object]]], LoadJson(InputStream.read()))

# lazy codec discovery must finish before strict construction forbids every file read
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))
assert not KAuditValue.DeniedReads
KAuditValue.BeginBuild()


# invalid provenance and forbidden reads must remain observable across the subprocess boundary
def ProcessInput(InputData: dict[str, dict[str, object]]) -> dict[str, object]:
    Result: dict[str, object]
    PriorDenied = len(KAuditValue.DeniedReads)
    try:
        StreamData = KBuildStreams(InputData, KMetadata, KRegistry)
        Records = KDecodeStreams(StreamData, KStreams, KRegistry)
        Result = KInspectResult(StreamData, Records)
    except ValueError as ErrorInfo:
        Result = {"error": str(ErrorInfo)}
    assert len(KAuditValue.DeniedReads) == PriorDenied
    try:
        with OpenFile("/metadata-donor-input.SLDPRT", "rb") as DonorStream:
            raise RuntimeError("forbidden donor open succeeded: " + DonorStream.name)
    except PermissionError:
        Result["read_blocked"] = True
    Result["import_reads"] = len(KAuditValue.ModuleReads)
    return Result


print(DumpJson([ProcessInput(InputData) for InputData in KRequest]))
