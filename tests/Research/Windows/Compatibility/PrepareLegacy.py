from pathlib import Path as FilePath
from shutil import copyfile as CopyFile

from tests.Research.Windows.Compatibility.CopyAutomation import CopyAutomation


# compatibility rejection needs the actual supervisor source with its older cancellation contract restored
def PrepareLegacy(WorkPath: FilePath, MarkerText: str) -> FilePath:
    RepoRoot = FilePath(__file__).resolve().parents[4]
    SourceText = (RepoRoot / "re/automation/Supervisor.py").read_text(encoding="utf-8")
    SourceText = SourceText.replace("KWindowsCliProtocol = 1", MarkerText)
    if not MarkerText:
        SourceText = SourceText.replace(
            '        if sys.platform == "win32" and KWindowsCliProtocol == 1:\n'
            + "            signal.signal(signal.SIGBREAK, self.shutdown)\n",
            "",
        )
    RootPath = WorkPath / "LegacyCheckout"
    (RootPath / ".git").mkdir(parents=True)
    (RootPath / "src/convert").mkdir(parents=True)
    CopyAutomation(RepoRoot, RootPath)
    for RepoName in (
        "tests/__init__.py",
        "tests/Research/SessionRunner.py",
        "tests/Research/Supervisor/SessionRoot.py",
    ):
        TargetPath = RootPath / RepoName
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        _ = CopyFile(RepoRoot / RepoName, TargetPath)
    ScriptPath = RootPath / "re/automation/Supervisor.py"
    _ = ScriptPath.write_text(SourceText, encoding="utf-8")
    return RootPath
