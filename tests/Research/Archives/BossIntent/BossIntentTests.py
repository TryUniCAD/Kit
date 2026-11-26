from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe

from tests.Research.Archives.BossIntent.BossIntentNeg import VerifyRefusals


# the paired source proof and replay must cross the actual tool process boundary
def RunIntentStep(WorkPath: FilePath, *Arguments: str) -> CompletedProcess[str]:
    RootPath = FilePath(__file__).resolve().parents[4]
    ScriptPath = RootPath / "re/automation/P03ConstraintIntent.py"
    return RunProcess(
        [PythonExe, "-I", "-B", str(ScriptPath), *Arguments],
        cwd=WorkPath,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


# the checked source and prepared artifact must preserve the direction of each driver
def VerifyPlan(Evidence: dict[str, object], Prepared: bytes) -> None:
    assert Evidence["source_sha256"] == (
        "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357"
    )
    assert Evidence["owner_span"] == ["Contents/Config-0-ResolvedFeatures", 5578, 6437]
    assert Evidence["prepared_sha256"] == HashBytes(Prepared).hexdigest()
    assert Evidence["source_operation"] == "join"
    NativeOwners = Evidence["original_native_features_outside_projection"]
    assert isinstance(NativeOwners, list) and len(NativeOwners) == 25
    Logical = Evidence["logical"]
    assert isinstance(Logical, dict)
    assert Logical["width"][-2:] == [[0, 3], 40.0]
    assert Logical["height"][-2:] == [[0, 2], 20.0]
    assert Logical["depth_mm"] == 10.0
    assert Logical["origin"] == "sldprt:sketch:26:native:6451"
    Relations = Logical["ordered_solver_relations"]
    assert len(Relations) == 7
    Prefix = "sldprt:sketch:26:profile:0:edge:"
    assert Relations[4][2] == [[Prefix + "3", "end"], [Prefix + "3", "start"]]
    assert Relations[5][2] == [[Prefix + "0", "start"], [Prefix + "0", "end"]]
    assert Relations[6][2] == [[Logical["origin"], ""], [Prefix + "0", "start"]]
    assert b"$bytes" not in Prepared and b"NativeFeatureDefinition" not in Prepared


# capture and logical writer replay prove the preserved solver constraints and refuse changed evidence
def CheckIntentFlow(TmpPath: FilePath) -> None:
    Source = TmpPath / "Source.json"
    Output = TmpPath / "Logical.json"
    Captured = RunIntentStep(TmpPath, "capture", "--output", str(Source))
    assert Captured.returncode == 0, Captured.stdout + Captured.stderr
    SourceBytes = Source.read_bytes()
    Prepped = RunIntentStep(
        TmpPath, "prepare", "--input", str(Source), "--output", str(Output)
    )
    assert Prepped.returncode == 0, Prepped.stdout + Prepped.stderr
    Evidence = ReadJson(Prepped.stdout)
    Prepared = Output.read_bytes()
    VerifyPlan(Evidence, Prepared)
    assert Evidence["input_sha256"] == HashBytes(SourceBytes).hexdigest()
    _ = Source.rename(TmpPath / "RetainedSource.json")
    Replayed = RunIntentStep(TmpPath, "replay", "--input", str(Output))
    assert Replayed.returncode == 0, Replayed.stdout + Replayed.stderr
    assert ReadJson(Replayed.stdout) == Evidence["logical"]
    assert not Source.exists() and Output.read_bytes() == Prepared
    VerifyRefusals(RunIntentStep, TmpPath, SourceBytes, Output)
