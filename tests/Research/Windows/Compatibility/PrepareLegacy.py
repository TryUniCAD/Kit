from pathlib import Path as FilePath


# compatibility rejection needs the actual supervisor source with its older cancellation contract restored
def PrepareLegacy(WorkPath: FilePath, MarkerText: str) -> FilePath:
    RepoRoot = FilePath(__file__).resolve().parents[4]
    SourceText = (RepoRoot / "re/automation/Supervisor.py").read_text(encoding="utf-8")
    SourceText = SourceText.replace("KWindowsCliProtocol = 1", MarkerText)
    if not MarkerText:
        SourceText = SourceText.replace(
            '        if sys.platform == "win32" and KWindowsCliProtocol == 1:\n'
            "            signal.signal(signal.SIGBREAK, self.shutdown)\n",
            "",
        )
    RootPath = WorkPath / "LegacyCheckout"
    (RootPath / ".git").mkdir(parents=True)
    (RootPath / "src/convert").mkdir(parents=True)
    ScriptPath = RootPath / "re/automation/Supervisor.py"
    ScriptPath.parent.mkdir(parents=True)
    _ = ScriptPath.write_text(SourceText, encoding="utf-8")
    return RootPath
