from __future__ import annotations

from copy import deepcopy as CopyValues
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# isolated subprocesses need an explicit repository anchor independent of the invoking directory
KRepoRoot = FilePath(__file__).resolve().parents[4]

# metadata purity must be exercised beyond the test interpreter boundary
KProgram = FilePath(__file__).with_name("MetadataProcess.py")

# authored revision identity prevents tests from relying on captured native provenance
KStamp: dict[str, object] = {
    "status": 0,
    "user_index": 0,
    "company_index": 0,
    "timestamp": 1700000000,
    "comment": "authored test revision",
}

# independent authored counters distinguish construction rules from saved document metadata
KHeader: dict[str, object] = {
    "next_id": 100,
    "user_names": ["author α"],
    "company_names": ["authored organization"],
    "revision_logs": [
        {"object_id": 0, "stamps": [KStamp], "name": "authored <part> & α"}
    ],
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

# explicit nonnative build provenance prevents fabricated vendor save history from passing
KHistory: dict[str, object] = {
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

# authored unicode names and references expose metadata escaping and graph ownership errors
KKeywords: dict[str, object] = {
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


# independent request graphs prevent mutations in one compatibility case from contaminating another
def MakeInput() -> dict[str, object]:
    InputData: dict[str, object] = {
        "header2": KHeader,
        "model_headers": {"7": {**CopyValues(KHeader), "model_present": True}},
        "history": KHistory,
        "keywords": KKeywords,
    }
    return CopyValues(InputData)


# growth across configurations logs and features must change only their dependent streams
def LargerInput() -> dict[str, object]:
    InputData = MakeInput()
    Header = CastValue(dict[str, object], InputData["header2"])
    Header["next_id"] = 400
    CastValue(list[object], Header["revision_logs"]).append(
        {"object_id": 31, "stamps": [KStamp]}
    )
    CastValue(dict[str, object], InputData["model_headers"])["9"] = {
        **CopyValues(KHeader),
        "model_present": True,
    }
    History = CastValue(dict[str, object], InputData["history"])
    State = CastValue(dict[str, object], CastValue(list[object], History["states"])[0])
    CastValue(list[object], State["date_codes"]).append(
        {"build_code": 1234570, "native_save": False}
    )
    Keyword = CastValue(dict[str, object], InputData["keywords"])
    CastValue(list[object], Keyword["configurations"]).append(
        {"id": 9, "name": "β configuration", "material": ""}
    )
    CastValue(list[object], Keyword["features"]).append(
        {"id": 31, "name": "additional authored feature", "kind": "RefPlane"}
    )
    return InputData


# a separate audited interpreter exposes runtime file dependencies hidden by in process calls
def RunMetadata(Inputs: list[dict[str, object]]) -> list[dict[str, object]]:
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


# neutral semantic changes must survive encoding and decoding without unrelated metadata drift
def TestMetadata() -> None:
    Small, Large = RunMetadata([MakeInput(), LargerInput()])
    assert Small["read_blocked"] and Large["read_blocked"]
    assert CastValue(int, Small["import_reads"]) > 0
    assert CastValue(int, Large["import_reads"]) > 0
    assert (Small["next_id"], Large["next_id"]) == (100, 400)
    assert Small["header_owner"] == 0 and Small["models"] == {
        "Contents/Config-7-ModelHeader": 1
    }
    assert Small["log_ids"] == [0] and Large["log_ids"] == [0, 31]
    assert Small["log_names"] == {
        "Header2": ["authored <part> & α"],
        "Contents/Config-7-ModelHeader": ["authored <part> & α"],
    }
    assert CastValue(dict[str, object], Large["log_names"])["Header2"] == [
        "authored <part> & α",
        "",
    ]
    assert Small["users"] == ["author α"]
    assert Small["history_codes"] == [[1234567]]
    assert Large["history_codes"] == [[1234567, 1234570]]
    assert Small["biography_count"] == Large["biography_count"] == 0
    assert Small["license_origin"] == 0
    assert Small["name"] == "authored <part> & α"
    assert Small["configs"] == ["7"] and Large["configs"] == ["7", "9"]
    assert Small["features"] == ["輪郭", "boss & <one>"]
    assert len(CastValue(list[object], Large["features"])) == 3 and Small[
        "children"
    ] == ["10"]
    assert Small["dimensions"] == ["12.5"]
    SmallSizes = CastValue(dict[str, int], Small["sizes"])
    LargeSizes = CastValue(dict[str, int], Large["sizes"])
    SmallHashes = CastValue(dict[str, str], Small["hashes"])
    LargeHashes = CastValue(dict[str, str], Large["hashes"])
    assert len(SmallSizes) == 5 and len(LargeSizes) == 6
    assert (
        SmallHashes["Contents/Config-7-ModelHeader"]
        == LargeHashes["Contents/Config-7-ModelHeader"]
    )
    for StreamName in (
        "Header2",
        "_MO_VERSION_19000/History",
        "swXmlContents/KeyWords",
    ):
        assert LargeSizes[StreamName] > SmallSizes[StreamName]
        assert LargeHashes[StreamName] != SmallHashes[StreamName]


# document renaming must reach persisted log ownership without changing unrelated provenance streams
def TestLogNames() -> None:
    Renamed = MakeInput()
    DocumentName = "renamed " + "文" * 260 + " & <α>"
    CastValue(dict[str, object], Renamed["keywords"])["name"] = DocumentName
    ModelHeaders = CastValue(dict[str, dict[str, object]], Renamed["model_headers"])
    Headers = [CastValue(dict[str, object], Renamed["header2"]), *ModelHeaders.values()]
    for Header in Headers:
        for LogRecord in CastValue(list[dict[str, object]], Header["revision_logs"]):
            LogRecord["name"] = DocumentName
    OriginalResult, RenamedResult = RunMetadata([MakeInput(), Renamed])
    assert OriginalResult["read_blocked"] and RenamedResult["read_blocked"]
    assert CastValue(int, RenamedResult["import_reads"]) > 0
    assert RenamedResult["name"] == DocumentName
    assert RenamedResult["log_names"] == {
        "Header2": [DocumentName],
        "Contents/Config-7-ModelHeader": [DocumentName],
    }
    OriginalHashes = CastValue(dict[str, str], OriginalResult["hashes"])
    RenamedHashes = CastValue(dict[str, str], RenamedResult["hashes"])
    OriginalSizes = CastValue(dict[str, int], OriginalResult["sizes"])
    RenamedSizes = CastValue(dict[str, int], RenamedResult["sizes"])
    for StreamName in (
        "Header2",
        "Contents/Config-7-ModelHeader",
        "swXmlContents/KeyWords",
    ):
        assert OriginalHashes[StreamName] != RenamedHashes[StreamName]
        assert OriginalSizes[StreamName] < RenamedSizes[StreamName]
    for StreamName in ("_MO_VERSION_19000/Biography", "_MO_VERSION_19000/History"):
        assert OriginalHashes[StreamName] == RenamedHashes[StreamName]
        assert OriginalSizes[StreamName] == RenamedSizes[StreamName]


# unsupported vendor provenance must fail explicitly instead of being invented or silently discarded
def TestProvenance() -> None:
    NativeSave = MakeInput()
    NativeSave["history"] = {
        **KHistory,
        "states": [
            {
                "file_version": 19000,
                "date_codes": [{"build_code": 1234567, "native_save": True}],
                "stamp": KStamp,
            }
        ],
    }
    MissingCode = MakeInput()
    MissingCode["history"] = {
        **KHistory,
        "states": [{"file_version": 19000, "date_codes": [], "stamp": KStamp}],
    }
    LicenseFlag = MakeInput()
    LicenseFlag["header2"] = {**KHeader, "license_flags": 1}
    Results = RunMetadata([NativeSave, MissingCode, LicenseFlag])
    assert all(Result["read_blocked"] for Result in Results)
    assert "must not be fabricated or cleared" in CastValue(str, Results[0]["error"])
    assert "explicit build provenance" in CastValue(str, Results[1]["error"])
    assert "provenance must not be cleared" in CastValue(str, Results[2]["error"])


# revision indices must remain bound to the identities authored for their owning headers
def TestStampNames() -> None:
    InputData = MakeInput()
    InputData["model_headers"] = {
        "7": {
            **KHeader,
            "model_present": True,
            "user_names": ["different authored identity"],
        }
    }
    Result = RunMetadata([InputData])[0]
    assert Result["read_blocked"]
    assert "different users or companies" in CastValue(str, Result["error"])
