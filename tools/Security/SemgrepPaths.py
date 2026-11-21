from json import dumps as DumpJson
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from tempfile import TemporaryDirectory as TempDirectory


# the installed scanner must preserve positive and negative path selection after a dependency override
def VerifyPaths() -> None:
    with TempDirectory(prefix="KitSemgrep") as TempName:
        RootPath = FilePath(TempName)
        SourcePath = RootPath / "Sources"
        SourcePath.mkdir()
        for FileName in ("keep_guard.py", "skip_guard.py", "plain.py"):
            _ = (SourcePath / FileName).write_text("print(17)\n", encoding="utf-8")
        _ = (RootPath / "outside_guard.py").write_text("print(17)\n", encoding="utf-8")
        RulePath = RootPath / "Rule.json"
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
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        Process = RunProcess(
            [
                PythonExe,
                "-m",
                "semgrep",
                "scan",
                "--config",
                str(RulePath),
                "--json",
                "--error",
                "--metrics=off",
                "--disable-version-check",
                "--no-git-ignore",
                "--include=Sources/*_guard.py",
                "--exclude=Sources/skip_guard.py",
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
        Findings = [FilePath(Entry["path"]).as_posix() for Entry in Report["results"]]
        if (
            Report["errors"]
            or Scanned != ["Sources/keep_guard.py"]
            or Findings != Scanned
        ):
            raise ValueError("Semgrep changed the include or exclude control selection")


if __name__ == "__main__":
    VerifyPaths()
