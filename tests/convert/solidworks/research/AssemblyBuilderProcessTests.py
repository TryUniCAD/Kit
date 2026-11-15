from __future__ import annotations

from copy import deepcopy as CopyValues
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# subprocess coverage must resolve source paths independently from the invoking working directory
KRepoRoot = FilePath(__file__).resolve().parents[4]

# the audited assembly entry point keeps fixture access outside construction and codec execution
KProgram = FilePath(__file__).with_name("AssemblyBuilderProcess.py")

# explicit authored identities and timestamps make generated archive dependence observable across process isolation
KInput: dict[str, dict[str, object]] = {
    "configuration": {
        "name": "authored assembly α",
        "description": "authored initial configuration",
        "local_id": 3,
        "date_code": 20261115,
        "parasolid_version": 3800001,
        "updated_at": 1600000000,
    },
    "file": {
        "path_name": "C:\\generated\\authored plate α.SLDPRT",
        "document_kind": "part",
        "created_at": 1600000000,
    },
}


# actual isolated interpreters must construct and decode native records without runtime document access
def RunBuilders(Inputs: list[dict[str, dict[str, object]]]) -> list[dict[str, object]]:
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(KProgram), str(KRepoRoot)],
        input=DumpJson(Inputs),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(list[dict[str, object]], LoadJson(Outcome.stdout))


# longer authored identities exercise native string length transitions without introducing saved metadata
def MakeChangedInput() -> dict[str, dict[str, object]]:
    Changed = CopyValues(KInput)
    Changed["configuration"]["name"] = "renamed " + "装" * 260
    Changed["configuration"][
        "description"
    ] = "authored extended assembly description 輪郭"
    Changed["configuration"]["local_id"] = 11
    Changed["file"] = {
        "path_name": "D:\\generated\\" + "装" * 260 + ".SLDASM",
        "document_kind": "assembly",
        "created_at": 1600000042,
    }
    return Changed


# variable authored names must survive native string growth while owner and allocation identities remain valid
def TestInitialConfigurationArchives() -> None:
    Changed = MakeChangedInput()
    Small, Large = RunBuilders([KInput, Changed])
    assert Small["read_blocked"] and Large["read_blocked"]
    assert CastValue(int, Small["import_reads"]) > 0
    assert all(Result["owner_identity"] for Result in (Small, Large))
    assert all(Result["componentless_default"] for Result in (Small, Large))
    assert [Result["distinct_profiles"] for Result in (Small, Large)] == [3, 3]
    assert Small["profile_schemas"] == Large["profile_schemas"] == [1, 1, 1]
    assert Small["saved_version"] == Large["saved_version"] == 19000
    assert Small["needs_update"] is Large["needs_update"] is False
    assert Small["state_count"] == Large["state_count"] == 1
    assert Small["local_id"] == 3 and Large["local_id"] == 11
    assert Small["name"] == KInput["configuration"]["name"]
    assert Large["name"] == Changed["configuration"]["name"]
    assert Large["description"] == Changed["configuration"]["description"]
    assert Small["path"] == KInput["file"]["path_name"]
    assert Large["path"] == Changed["file"]["path_name"]
    assert Small["stem"] == "authored plate α" and Large["stem"] == "装" * 260
    assert Small["category"] == 2 and Large["category"] == 3
    assert Large["created_at"] == 1600000042
    assert Small["configuration_schema"] == Large["file_schema"] == 1
    assert CastValue(int, Large["size"]) > CastValue(int, Small["size"])
    assert Large["hash"] != Small["hash"]


# invalid semantic requests must fail before an unsupported configuration or file identity reaches the archive
def TestConstructionInputScope() -> None:
    WrongKind = CopyValues(KInput)
    WrongKind["file"]["document_kind"] = "assembly"
    PartialPath = CopyValues(KInput)
    PartialPath["file"]["path_name"] = "C:\\generated\\.SLDPRT"
    InvalidTime = CopyValues(KInput)
    InvalidTime["configuration"]["updated_at"] = True
    Results = RunBuilders([WrongKind, PartialPath, InvalidTime])
    assert all(Result["read_blocked"] for Result in Results)
    assert "extension must agree" in CastValue(str, Results[0]["error"])
    assert "extension must agree" in CastValue(str, Results[1]["error"])
    assert "configuration time" in CastValue(str, Results[2]["error"])
