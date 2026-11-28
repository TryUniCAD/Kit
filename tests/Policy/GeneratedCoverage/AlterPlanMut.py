import json as JsonTools
from pathlib import Path


# corrupted real artifacts and generator changes must stay unapproved without executing proposed code
def AlterPlanMut(TempPath: Path, CaseName: str, CodeNames: list[str]) -> None:
    if CaseName == "tampered":
        TargetPath = TempPath / "Documentation/Planning/Generated/BoardData.js"
        WriteCount = TargetPath.write_bytes(
            TargetPath.read_bytes() + b"window.Unverified = true;\n"
        )
        assert WriteCount > 0
    if CaseName == "generator":
        TargetPath = TempPath / "re/automation/Planning/Build.py"
        WriteCount = TargetPath.write_bytes(
            TargetPath.read_bytes()
            + b'\nraise SystemExit("proposed generator executed")\n'
        )
        assert WriteCount > 0
    if CaseName == "input":
        TargetPath = TempPath / "Documentation/Planning/SdkScopes.json"
        InputData = JsonTools.loads(TargetPath.read_text())
        InputData["CoverageProcess"] = True
        WriteCount = TargetPath.write_text(JsonTools.dumps(InputData))
        assert WriteCount > 0
    if CaseName == "added":
        TargetPath = TempPath / "re/automation/Planning/hashlib.py"
        WriteCount = TargetPath.write_text(
            'raise SystemExit("proposed module executed")\n'
        )
        assert WriteCount > 0
        CodeNames.append(str(TargetPath.relative_to(TempPath)))
