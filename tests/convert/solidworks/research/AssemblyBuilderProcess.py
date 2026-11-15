from __future__ import annotations

from builtins import open as OpenFile
from codecs import lookup as FindCodec
from importlib import import_module as ImportModule
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import cast as CastValue

# isolated assembly construction needs an explicit source root before guarded module loading begins
KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))

from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

# import time access must be recorded before any assembly builder dependency can read fixtures
KAuditValue = BuildAudit(KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "defs")
AddAuditHook(KAuditValue.InspectEvent)

# the actual fresh assembly implementation must participate in the audited process
KAssembly = ImportModule("builders.Assembly")

# assembly self components must use the shared model constructor and its proved owner domain
KModel = ImportModule("builders.Model")

# typed native objects and seeded archive maps must use the shared codec implementation
KCore = ImportModule("Core")

# native class discovery must finish before construction forbids all file and directory access
KRegistry = ImportModule("Classes").registry()

# graph construction stays focused on generated semantic ownership rather than codec observations
KBuildRecords = ImportModule(
    "tests.convert.solidworks.research.Assembly.Build"
).BuildRecords

# archive boundaries must decode and reproduce every newly constructed record without hidden tails
KRoundTrip = ImportModule("tests.convert.solidworks.research.Assembly.Codec").RoundTrip

# parent assertions need decoded semantic values rather than success flags emitted by constructors
KInspectResult = ImportModule(
    "tests.convert.solidworks.research.Assembly.Report"
).InspectResult

# authored process input must be supplied explicitly instead of loaded from saved model data
KRequest = CastValue(list[dict[str, dict[str, object]]], LoadJson(InputStream.read()))

# lazy string codec discovery must finish before the strict construction phase
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))
assert not KAuditValue.DeniedReads
KAuditValue.BeginBuild()


# strict construction must expose forbidden reads even when builder code catches their exceptions
def ProcessInput(InputData: dict[str, dict[str, object]]) -> dict[str, object]:
    Result: dict[str, object]
    PriorDenied = len(KAuditValue.DeniedReads)
    try:
        ConfigValue, ComponentValue, FileValue = KBuildRecords(
            InputData, KAssembly, KModel, KCore
        )
        Result = KInspectResult(
            *KRoundTrip(ConfigValue, ComponentValue, FileValue, KCore, KRegistry)
        )
    except ValueError as ErrorInfo:
        Result = {"error": str(ErrorInfo)}
    assert len(KAuditValue.DeniedReads) == PriorDenied
    try:
        with OpenFile("/assembly-donor-input.SLDASM", "rb") as DonorStream:
            raise RuntimeError("forbidden donor open succeeded: " + DonorStream.name)
    except PermissionError:
        Result["read_blocked"] = True
    Result["import_reads"] = len(KAuditValue.ModuleReads)
    return Result


print(DumpJson([ProcessInput(InputData) for InputData in KRequest]))
