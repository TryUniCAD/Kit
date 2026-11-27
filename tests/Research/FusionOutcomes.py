import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# inventory coverage needs explicit outcome verification so partial discovery cannot appear complete
def CheckOutcomes(CensusPath: FilePath, TempPath: FilePath) -> None:
    Report = JsonCodec.loads(CensusPath.read_text())
    assert len(Report["assets"]) == 714
    CheckArgs = [
        System.executable,
        str(FilePath(__file__).resolve().parents[2] / "re/automation/FusionCensus.py"),
        "check",
        "--expected",
        str(
            FilePath(__file__).resolve().parents[2]
            / "re/automation/FusionOutcomes.json"
        ),
        "--actual",
    ]
    SameRun = Subprocess.run(
        [*CheckArgs, str(CensusPath)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert SameRun.returncode == 0, (SameRun.stdout, SameRun.stderr)
    Comparison = JsonCodec.loads(SameRun.stdout)
    assert Comparison["manifest_binding"] == "pinned_attribution_metadata_migration"
    assert (
        Comparison["baseline_manifest_sha256"]
        == "4cc8fb707641ecde29a04b5dafa1ecbf7e706a839550a4af3b8807d19b64d4e2"
    )
    assert (
        Comparison["observed_manifest_sha256"]
        == Report["observation"]["manifest_sha256"]
    )
    assert (
        Comparison["observed_manifest_sha256"]
        == "905b547f47e6b649b190bee11964067ce8dfa81ec8d43fd15e1c37f8d6eda05c"
    )
    for CaseName in ("missing", "improved", "duplicate", "source", "corpus"):
        Changed = JsonCodec.loads(CensusPath.read_text())
        if CaseName == "missing":
            Changed["assets"] = Changed["assets"][1:]
        elif CaseName == "improved":
            AssetEntry = next(
                Entry for Entry in Changed["assets"] if Entry["outcome"] == "rejected"
            )
            AssetEntry.pop("reason")
            AssetEntry.update(
                outcome="decoded", reader_mode="strict", strict_rejection=None
            )
        elif CaseName == "duplicate":
            Changed["assets"].append(Changed["assets"][0])
        elif CaseName == "corpus":
            Changed["observation"]["corpus_revision"] = "0" * 40
        else:
            Changed["observation"]["manifest_sha256"] = "0" * 64
        ChangedPath = TempPath / f"{CaseName}.json"
        _ = ChangedPath.write_text(JsonCodec.dumps(Changed))
        ChangedRun = Subprocess.run(
            [*CheckArgs, str(ChangedPath)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert ChangedRun.returncode == (
            3 if CaseName in ("missing", "improved") else 1
        ), ChangedRun.stderr
