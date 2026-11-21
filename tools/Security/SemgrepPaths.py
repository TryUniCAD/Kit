from json import dumps as DumpJson
from json import loads as LoadJson
from pathlib import Path as FilePath
from shutil import which as FindProgram
from subprocess import run as RunProcess
from tempfile import TemporaryDirectory as TempDirectory


# the installed scanner must preserve positive and negative path selection after a dependency override
def VerifyPaths() -> None:
    ProgramPath = FindProgram("semgrep")
    if ProgramPath is None:
        raise RuntimeError("The locked Semgrep console command is unavailable")
    with TempDirectory(prefix="KitSemgrep") as TempName:
        RootPath = FilePath(TempName)
        SourcePath = RootPath / "Sources"
        SourcePath.mkdir()
        for FileName in ("keep_guard.py", "skip_guard.py", "plain.py"):
            _ = (SourcePath / FileName).write_text("print(17)\n", encoding="utf-8")
        _ = (RootPath / "outside_guard.py").write_text("print(17)\n", encoding="utf-8")
        RulePath = RootPath / "Rule.json"
        for RuleFilter in (False, True):
            _ = RulePath.write_text(
                DumpJson(
                    {
                        "rules": [
                            {
                                "id": "path-filter-smoke",
                                "languages": ["python"],
                                "message": "path filter control",
                                "severity": "INFO",
                                "pattern": "print($VALUE)",
                                **(
                                    {
                                        "paths": {
                                            "include": ["Sources/*_guard.py"],
                                            "exclude": ["Sources/skip_guard.py"],
                                        }
                                    }
                                    if RuleFilter
                                    else {}
                                ),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            Process = RunProcess(
                [
                    ProgramPath,
                    "scan",
                    "--config",
                    str(RulePath),
                    "--json",
                    "--error",
                    "--metrics=off",
                    "--disable-version-check",
                    "--no-git-ignore",
                    *(
                        ["--legacy"]
                        if RuleFilter
                        else [
                            "--include=Sources/*_guard.py",
                            "--exclude=Sources/skip_guard.py",
                        ]
                    ),
                    ".",
                ],
                cwd=RootPath,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if Process.returncode != 1:
                raise ValueError(f"Semgrep smoke returned {Process.returncode}")
            Report = LoadJson(Process.stdout)
            Scanned = [
                FilePath(NameText).as_posix() for NameText in Report["paths"]["scanned"]
            ]
            Findings = [
                FilePath(Entry["path"]).as_posix() for Entry in Report["results"]
            ]
            if (
                Report["errors"]
                or Findings != ["Sources/keep_guard.py"]
                or (not RuleFilter and Scanned != Findings)
            ):
                raise ValueError(
                    "Semgrep changed the include or exclude control selection"
                )


if __name__ == "__main__":
    VerifyPaths()
