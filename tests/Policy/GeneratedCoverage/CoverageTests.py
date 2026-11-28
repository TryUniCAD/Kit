import json as JsonTools
import subprocess as ProcessTools
import sys as SysTools
from pathlib import Path

import pytest as Pytest

from tests.Policy.GeneratedCoverage.CreatePlan import CreatePlan


# complete context must depend on real git sources and exact rebuilds while rejecting altered output code and unsupported inputs
@Pytest.mark.parametrize(
    "CaseName", ("valid", "tampered", "generator", "added", "input", "symlink", "stale")
)
def CheckPlanReview(TmpPath: Path, CaseName: str) -> None:
    Revision, HeadSha, EnvState = CreatePlan(TmpPath, CaseName)
    RootPath = Path(__file__).resolve().parents[3]
    FileNames = ProcessTools.run(
        ["git", "diff", "--name-only", Revision, HeadSha],
        cwd=TmpPath,
        env=EnvState,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    Settings = JsonTools.loads(
        (RootPath / ".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
    )["AccountReview"]
    Settings["PolicyRevision"] = Revision
    RequestPath = TmpPath / "Request.json"
    WriteCount = RequestPath.write_text(
        JsonTools.dumps(
            {
                "Evidence": {
                    "head_sha": HeadSha,
                    "base_sha": HeadSha if CaseName == "stale" else Revision,
                    "merge_base_sha": Revision,
                },
                "PullData": {
                    "title": "Planning coverage process",
                    "body": "Real source reconstruction verification",
                    "changed_files": len(FileNames),
                },
                "FileList": [
                    {"filename": FileName, "status": "modified"}
                    for FileName in FileNames
                ],
                "Settings": Settings,
            }
        )
    )
    assert WriteCount > 0
    Result = ProcessTools.run(
        [
            SysTools.executable,
            str(RootPath / ".github/scripts/Review/BuildContext.py"),
            str(RequestPath),
        ],
        cwd=TmpPath,
        env=EnvState,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert Result.returncode == 0, Result.stderr
    Context = JsonTools.loads(Result.stdout)
    assert Context["input_complete"] == (CaseName == "valid")
    Verified = [Source for Source in Context["files"] if "verified_generated" in Source]
    assert len(Verified) == (2 if CaseName == "valid" else 0)
    if CaseName == "valid":
        assert Context["generated_verification"]["generator_revision"] == Revision
        assert Context["generated_verification"]["reviewed_inputs"] == [
            "Documentation/Planning/Links.json"
        ]
        assert all(
            Source["verified_generated"]["after"]["bytes"] > 160000
            for Source in Verified
        )
