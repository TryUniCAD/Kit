import json as JsonTools
import subprocess as ProcessTools
import sys as SysTools
from pathlib import Path
from shutil import copyfile


# actual catalogue and register data expose reconstruction failures that tiny policy fixtures cannot establish
def CopyPlan(
    RootPath: Path, TempPath: Path, CaseName: str, EnvState: dict[str, str]
) -> list[str]:
    Manifest = JsonTools.loads(
        (RootPath / "Documentation/Planning/Generated/Manifest.json").read_text()
    )
    CodeNames = [
        str(SourcePath.relative_to(RootPath))
        for SourcePath in (RootPath / "re/automation/Planning").rglob("*.py")
        if "__pycache__" not in SourcePath.parts
    ]
    for FileName in [*Manifest["SourceHashes"], *CodeNames]:
        TargetPath = TempPath / FileName
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        copyfile(RootPath / FileName, TargetPath)
    LinkPath = TempPath / "Documentation/Planning/Links.json"
    LinkData = JsonTools.loads(LinkPath.read_text())
    LinkData["ExtraTasks"][0]["Blocker"] += " Coverage process boundary verification"
    LinkPath.write_text(JsonTools.dumps(LinkData, indent=2) + "\n")
    ProcessTools.run(
        [
            SysTools.executable,
            str(RootPath / "re/automation/Planning/Build.py"),
            "--root",
            str(TempPath),
        ],
        env=EnvState,
        capture_output=True,
        check=True,
        timeout=60,
    )
    if CaseName == "tampered":
        TargetPath = TempPath / "Documentation/Planning/Generated/BoardData.js"
        TargetPath.write_bytes(TargetPath.read_bytes() + b"window.Unverified = true;\n")
    if CaseName == "generator":
        TargetPath = TempPath / "re/automation/Planning/Build.py"
        TargetPath.write_bytes(
            TargetPath.read_bytes()
            + b'\nraise SystemExit("proposed generator executed")\n'
        )
    if CaseName == "input":
        TargetPath = TempPath / "Documentation/Planning/SdkScopes.json"
        InputData = JsonTools.loads(TargetPath.read_text())
        InputData["CoverageProcess"] = True
        TargetPath.write_text(JsonTools.dumps(InputData))
    if CaseName == "added":
        TargetPath = TempPath / "re/automation/Planning/hashlib.py"
        TargetPath.write_text('raise SystemExit("proposed module executed")\n')
        CodeNames.append(str(TargetPath.relative_to(TempPath)))
    FileNames = [
        *Manifest["SourceHashes"],
        *CodeNames,
        *[
            str(SourcePath.relative_to(TempPath))
            for SourcePath in (TempPath / "Documentation/Planning/Generated").iterdir()
        ],
    ]
    return FileNames
