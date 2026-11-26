from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath

from tests.Research.Archives.BossIntent.BossIntentNeg import VerifyRefusals
from tests.Research.Archives.BossIntent.RunBossIntent import RunIntentStep
from tests.Research.Archives.BossIntent.VerifyBossPlan import VerifyPlan


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
