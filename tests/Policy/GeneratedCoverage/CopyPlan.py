import json as JsonTools
import subprocess as ProcessTools
import sys as SysTools
from pathlib import Path
from shutil import copyfile

from tests.Policy.GeneratedCoverage.AlterPlanMut import AlterPlanMut


# actual catalogue and register data expose reconstruction failures that tiny policy fixtures cannot establish
def CopyPlan(
    RootPath: Path, TempPath: Path, CaseName: str, EnvState: dict[str, str]
) -> list[str]:
    Manifest = JsonTools.loads(
        (RootPath / "Documentation/Planning/Generated/Manifest.json").read_text()
    )
    InputNames = [str(FileName) for FileName in Manifest["SourceHashes"]]
    CodeNames = [
        str(SourcePath.relative_to(RootPath))
        for SourcePath in (RootPath / "re/automation/Planning").rglob("*.py")
        if "__pycache__" not in SourcePath.parts
    ]
    for FileName in [*InputNames, *CodeNames]:
        TargetPath = TempPath / FileName
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        CopiedPath = copyfile(RootPath / FileName, TargetPath)
        assert Path(CopiedPath).is_file()
    LinkPath = TempPath / "Documentation/Planning/Links.json"
    LinkData = JsonTools.loads(LinkPath.read_text())
    LinkData["ExtraTasks"][0]["Blocker"] += " Coverage process boundary verification"
    WriteCount = LinkPath.write_text(JsonTools.dumps(LinkData, indent=2) + "\n")
    assert WriteCount > 0
    ProcessInfo = ProcessTools.run(
        [
            SysTools.executable,
            str(RootPath / "re/automation/Planning/Build.py"),
            "--root",
            str(TempPath),
        ],
        env=EnvState,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stderr
    AlterPlanMut(TempPath, CaseName, CodeNames)
    FileNames = [
        *InputNames,
        *CodeNames,
        *[
            str(SourcePath.relative_to(TempPath))
            for SourcePath in (TempPath / "Documentation/Planning/Generated").iterdir()
        ],
    ]
    return FileNames
