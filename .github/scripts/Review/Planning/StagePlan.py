import json as JsonTools
import subprocess as ProcessTools
from pathlib import Path

from ObjectMap import ObjectMap
from Planning.ReadBlob import ReadBlob


# reconstruction must use accepted code and data while every permitted changed input stays bound to supplied source
def StagePlan(
    RootPath: Path,
    Revision: str,
    HeadSha: str,
    ChangedInputs: dict[str, dict[str, object]],
) -> None:
    Manifest = ObjectMap(
        JsonTools.loads(
            ReadBlob(Revision, "Documentation/Planning/Generated/Manifest.json")
        )
    )
    ProcessTools.run(
        [
            "git",
            "diff",
            "--quiet",
            "--no-ext-diff",
            "--no-textconv",
            Revision,
            HeadSha,
            "--",
            "re/automation/Planning",
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    CodeNames = ProcessTools.run(
        ["git", "ls-tree", "-r", "--name-only", Revision, "re/automation/Planning"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.splitlines()
    for FileName in [
        *ObjectMap(Manifest["SourceHashes"]),
        *[FileName for FileName in CodeNames if FileName.endswith(".py")],
    ]:
        Content = ReadBlob(Revision, FileName)
        Proposed = ReadBlob(HeadSha, FileName)
        if FileName not in ChangedInputs and Proposed != Content:
            raise ValueError("Planning generator or unsupported input changed")
        if FileName in ChangedInputs and (
            not isinstance(ChangedInputs[FileName].get("after"), str)
            or str(ChangedInputs[FileName]["after"]).encode() != Proposed
        ):
            raise ValueError("Planning input differs from reviewed source")
        TargetPath = RootPath / FileName
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        TargetPath.write_bytes(Content)
