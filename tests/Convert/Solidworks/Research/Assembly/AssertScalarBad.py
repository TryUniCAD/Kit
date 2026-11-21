from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# truncated generated streams must fail at both scalar reader entry points
def AssertScalarBad(ParentPath: FilePath, ChildPath: FilePath) -> None:
    Archive = SldprtArchive.from_bytes(ParentPath.read_bytes())
    for StreamName, Label, Length, Message in (
        (
            "Contents/Config-0-ModelHeader",
            "ShortHeader",
            -1,
            "truncated SOLIDWORKS archive field",
        ),
        ("Contents/Config-0-MatesList", "ShortMatePrefix", 3, "eof reading i32 at 0"),
    ):
        Streams = dict(Archive.streams)
        Streams[StreamName] = Streams[StreamName][:Length]
        BrokenPath = ParentPath.with_stem(Label)
        with BrokenPath.open("xb") as Output:
            _ = Output.write(build_sldprt(Streams))
        ReportPath = BrokenPath.with_suffix(".json")
        Outcome = RunProcess(
            [
                PythonExec,
                str(KRepoRoot / "re/tooling/sw2026/serial/CheckSdkHeaders.py"),
                str(BrokenPath),
                str(ChildPath),
                "--config-handoff",
                "--report",
                str(ReportPath),
            ],
            cwd=KRepoRoot,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert Outcome.returncode != 0 and Message in Outcome.stderr
        assert not ReportPath.exists()
