from __future__ import annotations

from copy import deepcopy as CopyValues
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

KRepoRoot = FilePath(__file__).resolve().parents[4]
KProgram = FilePath(__file__).with_name("MetadataProcess.py")
KStamp = {
    "status": 0,
    "user_index": 0,
    "company_index": 0,
    "timestamp": 1700000000,
    "comment": "authored test revision",
}
KHeader = {
    "next_id": 100,
    "user_names": ["author α"],
    "company_names": ["authored organization"],
    "revision_logs": [{"object_id": 0, "stamps": [KStamp]}],
    "created_at": 1700000000,
    "modified_at": 1700000100,
    "updated_at": 1700000050,
    "model_present": False,
    "component_count": 0,
    "update_stamp": 103,
    "body_stamp": 105,
    "license_flags": 0,
    "license_type": 0,
}
KHistory = {
    "states": [
        {
            "file_version": 19000,
            "date_codes": [{"build_code": 1234567, "native_save": False}],
            "stamp": KStamp,
        }
    ],
    "failure_severity": 0,
    "minimum_free_memory": 4294967295,
    "license_origin": 0,
    "language_id": 1033,
    "cjk_saved": False,
    "cjk_warning": False,
}
KKeywords = {
    "name": "authored <part> & α",
    "timestamp": 1700000100,
    "configurations": [
        {"id": 7, "name": "α configuration", "material": "authored material"}
    ],
    "features": [
        {
            "id": 10,
            "name": "輪郭",
            "kind": "ProfileFeature",
            "tag": "Sketch",
            "dimensions": [{"name": "diameter", "value": 12.5}],
        },
        {
            "id": 11,
            "name": "boss & <one>",
            "kind": "Boss",
            "tag": "Extrusion",
            "children": [10],
            "dissectable": True,
            "root": True,
        },
    ],
}


def MakeInput() -> dict:
    return CopyValues(
        {
            "header2": KHeader,
            "model_headers": {"7": {**KHeader, "model_present": True}},
            "history": KHistory,
            "keywords": KKeywords,
        }
    )


def LargerInput() -> dict:
    InputData = MakeInput()
    InputData["header2"]["next_id"] = 400
    InputData["header2"]["revision_logs"].append({"object_id": 31, "stamps": [KStamp]})
    InputData["model_headers"]["9"] = {**CopyValues(KHeader), "model_present": True}
    InputData["history"]["states"][0]["date_codes"].append(
        {"build_code": 1234570, "native_save": False}
    )
    InputData["keywords"]["configurations"].append(
        {"id": 9, "name": "β configuration", "material": ""}
    )
    InputData["keywords"]["features"].append(
        {"id": 31, "name": "additional authored feature", "kind": "RefPlane"}
    )
    return InputData


def RunMetadata(Inputs: list[dict]) -> list[dict]:
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(KProgram), str(KRepoRoot)],
        input=DumpJson(Inputs),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return LoadJson(Outcome.stdout)


def TestMetadata() -> None:
    Small, Large = RunMetadata([MakeInput(), LargerInput()])
    assert Small["read_blocked"] and Large["read_blocked"]
    assert (Small["next_id"], Large["next_id"]) == (100, 400)
    assert Small["header_owner"] == 0 and set(Small["models"].values()) == {1}
    assert Small["log_ids"] == [0] and Large["log_ids"] == [0, 31]
    assert Small["users"] == ["author α"]
    assert Small["history_codes"] == [[1234567]]
    assert Large["history_codes"] == [[1234567, 1234570]]
    assert Small["biography_count"] == Large["biography_count"] == 0
    assert Small["license_origin"] == 0
    assert Small["name"] == "authored <part> & α"
    assert Small["configs"] == ["7"] and Large["configs"] == ["7", "9"]
    assert Small["features"] == ["輪郭", "boss & <one>"]
    assert len(Large["features"]) == 3 and Small["children"] == ["10"]
    assert Small["dimensions"] == ["12.5"]
    assert len(Small["sizes"]) == 5 and len(Large["sizes"]) == 6
    for StreamName in (
        "Header2",
        "_MO_VERSION_19000/History",
        "swXmlContents/KeyWords",
    ):
        assert Large["sizes"][StreamName] > Small["sizes"][StreamName]
        assert Large["hashes"][StreamName] != Small["hashes"][StreamName]


def TestProvenance() -> None:
    NativeSave = MakeInput()
    NativeSave["history"]["states"][0]["date_codes"][0]["native_save"] = True
    MissingCode = MakeInput()
    MissingCode["history"]["states"][0]["date_codes"] = []
    LicenseFlag = MakeInput()
    LicenseFlag["header2"]["license_flags"] = 1
    Results = RunMetadata([NativeSave, MissingCode, LicenseFlag])
    assert all(Result["read_blocked"] for Result in Results)
    assert "must not be fabricated or cleared" in Results[0]["error"]
    assert "explicit build provenance" in Results[1]["error"]
    assert "provenance must not be cleared" in Results[2]["error"]


def TestStampNames() -> None:
    InputData = MakeInput()
    InputData["model_headers"]["7"]["user_names"] = ["different authored identity"]
    Result = RunMetadata([InputData])[0]
    assert Result["read_blocked"]
    assert "different users or companies" in Result["error"]
