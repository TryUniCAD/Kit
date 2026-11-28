from json import loads as LoadJson
from math import degrees as ToDegrees, isclose as IsClose
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue


# each tracked fixture must pass the public strict reader from a fresh process
def VerifySwSaved(RoleName: str) -> dict[str, object]:
    Repository = FilePath(__file__).resolve().parents[4]
    Worker = Repository / "re/tooling/sw2026/sweep_source/CheckTrackedSweepSdk.py"
    Result = RunProcess(
        (PythonExe, "-I", "-B", str(Worker), "--role", RoleName),
        cwd=Repository,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Result.returncode == 0, Result.stderr
    Report = CastValue(dict[str, object], LoadJson(Result.stdout))
    assert Report["role"] == RoleName
    assert Report["strict_reader_routes"] == 3
    assert Report["runtime_accesses"] == Report["native_launches"] == 0
    assert Report["native_source_sha256"] != Report["fixture_sha256"]
    assert Report["matched_direct_registry_explicit_default_and_design_only"] is True
    assert Report["typed_result_atom"] == "101"
    RimValues = CastValue(list[dict[str, object]], Report["oriented_rims"])
    assert [RimValue["oriented_dv"] for RimValue in RimValues] == [-1, 1]
    assert [RimValue["oriented_cap_angle"] for RimValue in RimValues] == [-1, 1]
    assert [RimValue["verified_quarter_points"] for RimValue in RimValues] == [4, 4]
    Topology = CastValue(dict[str, object], Report["current_geometry"])
    assert Topology["native_counts"] == [1, 1, 3, 2, 0]
    VerifySwReview(Report)
    return Report


# both read modes must check the physical owners while optional xml stays on its explicit refusal path
def VerifySwReview(Report: dict[str, object]) -> None:
    Boundaries = CastValue(dict[str, object], Report["review_boundaries"])
    Counts = CastValue(dict[str, dict[str, int]], Boundaries["geometry_call_counts"])
    assert Counts["full"]["ReadSwBrep"] == 1
    assert Counts["design"]["ReadSwBrep"] == Counts["design"]["DecodeBrep"] == 0
    assert Counts["design"]["ReadSwFrames"] == Counts["design"]["CheckSwTorus"] == 1
    assert Counts["design"]["CheckSwTrims"] == 1
    assert Boundaries["cyclic_shell_refused"] == ["full", "design"]
    Malformed = CastValue(dict[str, object], Boundaries["malformed_optional_xml"])
    assert len(Malformed) == 3
    assert Report["permissive_legacy_layout_reads"] == 3
    Grammar = CastValue(dict[str, object], Boundaries["saved_grammar_scope"])
    assert Grammar["isolated_new_classes"] == 4
    assert Grammar["isolated_alternate_layouts"] == 4


# an actual section edit changes the driving diameter and sketch seam while the signed physical trims keep their owners
def TestSavedSweep() -> None:
    Before = VerifySwSaved("original")
    After = VerifySwSaved("section")
    assert Before["independent_drivers_mm"] == [11.426, 41.297]
    assert After["independent_drivers_mm"] == [14.186, 41.297]
    Original = CastValue(dict[str, object], Before["sketches"])
    Updated = CastValue(dict[str, object], After["sketches"])
    assert Original["periodic_seam_mm"] != Updated["periodic_seam_mm"]
    assert Original["point_marks"] == Updated["point_marks"] == [2, 1]
    assert Original["start_end_index"] == Updated["start_end_index"] == 1
    assert Original["local_seam_angle_rad"] == 0.0
    assert IsClose(ToDegrees(CastValue(float, Updated["local_seam_angle_rad"])), 17.0)
    assert Before["oriented_rims"] == After["oriented_rims"]
