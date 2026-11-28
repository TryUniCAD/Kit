import json as JsonTools
import subprocess as ProcessTools
import sys as SysTools
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast as CastValue

from pytest import mark as MarkTests

from tests.Policy.ContextBudget.MakeBudgetRepo import MakeBudgetRepo
from tests.Policy.ContextBudget.MakeInput import MakeInput
from tests.Policy.ContextBudget.VerifyBudget import VerifyBudget, VerifySnapshots


# the shared suite exercises the actual collector in a fresh process against three real git revisions
@MarkTests.parametrize(
    "CaseName", ("small", "redundant", "oversized", "binary", "count", "policy")
)
def CheckBudget(CaseName: str) -> None:
    RootPath = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(prefix="KitContextBudget-") as TempName:
        WorkPath = Path(TempName)
        RepoPath = WorkPath / "Repository"
        BeforeSha, HeadValue, TargetSha, FileNames = MakeBudgetRepo(RepoPath, CaseName)
        InputData = MakeInput(RepoPath, BeforeSha, HeadValue, TargetSha, FileNames)
        InputPath = WorkPath / "Input.json"
        WriteCount = InputPath.write_text(JsonTools.dumps(InputData), encoding="utf-8")
        assert WriteCount > 0
        Result = RunCollector(RootPath, RepoPath, InputPath)
        if CaseName == "policy":
            assert Result.returncode != 0 and "encoded input budget" in Result.stderr
            assert not Result.stdout
            return
        assert Result.returncode == 0, Result.stderr
        Content = Result.stdout.encode("utf-8")
        Context = CastValue(dict[str, object], JsonTools.loads(Content))
        VerifyBudget(CaseName, Context, len(Content))
        VerifySnapshots(RepoPath, Context, BeforeSha, HeadValue, TargetSha)


# no account authentication or model execution enters this real git backed context process
def RunCollector(
    RootPath: Path, RepoPath: Path, InputPath: Path
) -> ProcessTools.CompletedProcess[str]:
    return ProcessTools.run(
        [
            SysTools.executable,
            "-B",
            str(RootPath / ".github/scripts/Review/BuildContext.py"),
            str(InputPath),
        ],
        cwd=RepoPath,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=90,
    )
