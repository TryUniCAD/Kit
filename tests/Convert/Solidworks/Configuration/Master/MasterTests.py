from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each archive proof runs in a fresh process before reporting typed fields and bytes
KMasterProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgMaster.py"
)


# preserve guarded process failures while reading the bounded proof
def RunMasterCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KMasterProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["case"] == CaseName
    assert ReportValue["runtime_external_accesses"] == 0
    return ReportValue


# the physical master must preserve every field and leave the inherited map untouched
def TestMasterSlice() -> None:
    Result = RunMasterCase("native")
    assert Result["interval"] == [25324, 25473]
    Proof = CastValue(dict[str, object], Result["proof"])
    assert Proof["class"] == ["moSheetMetalMaster_c", 1]
    assert (Proof["slot"], Proof["body_count"]) == (None, 0)
    assert Proof["extent"] == [0, 149]
    assert Proof["counter"] == [119, 119]
    assert Proof["mapped_slots"] == [1, 2, 3]
    assert Proof["fields_sha256"] == (
        "dadef17e06869eaf27508a7e37d04ea55662aa004fcfcdb124f8a31a73827a19"
    )
    assert (
        Proof["wire_sha256"]
        == Proof["emitted_sha256"]
        == ("f75ffe9d1742b2d0c44ce72b3c39a0b59954ccbfbb2865ae05e4fa0851a47869")
    )


# independent wire and model forms must agree without publishing a refused body
def TestMasterWire() -> None:
    Result = RunMasterCase("wire")
    assert Result["prefixed_extent"] == [7, 162]
    assert Result["virtual_flags"] == [4, 0, "nonboolean_refused"]
    Proof = CastValue(dict[str, object], Result["proof"])
    assert Proof["extent"] == [0, 155]
    assert Proof["class"] == ["moSheetMetalMaster_c", 1]
    assert (Proof["slot"], Proof["body_count"]) == (None, 0)
    assert Proof["counter"] == [4, 4]
    assert Proof["mapped_slots"] == [1, 2, 3]
    assert (
        Proof["wire_sha256"]
        == Proof["emitted_sha256"]
        == ("2a1536c54d55a425602ec103b9f887b109f8091fde58c1b4b0d45265a461992b")
    )
    Refusals = CastValue(list[str], Result["refusals"])
    assert Refusals == [
        "foreign_node",
        "mapped_node",
        "truncated",
        "new_mapped_child",
        "nonempty",
        "negative",
        "trailing",
        "inherited_link",
        "mapped_child",
        "foreign_part",
        "archive_version",
        "store_foreign_node",
        "store_mapped_node",
        "store_nonempty",
        "store_inherited_link",
        "store_alternate_context",
        "wide_null_f18",
        "wide_null_f78",
        "wide_null_f258",
        "wide_null_f2f0",
        "wide_empty_count",
        "store_wide_empty_count",
    ]


# a complete authored inherited map must keep every class and object identity
def TestMasterMap() -> None:
    Result = RunMasterCase("full_map")
    assert Result["map"] == {
        "base": 4,
        "entries": 118,
        "slot_span": [1, 118],
        "classes": 30,
        "objects": 88,
        "after_each_operation": "same_entries_and_inverse_lookups",
    }
    Proof = CastValue(dict[str, object], Result["proof"])
    assert Proof["extent"] == [0, 155]
    assert Proof["counter"] == [119, 119]
    assert (Proof["slot"], Proof["body_count"]) == (None, 0)
    assert (
        Proof["wire_sha256"]
        == Proof["emitted_sha256"]
        == ("2a1536c54d55a425602ec103b9f887b109f8091fde58c1b4b0d45265a461992b")
    )
