from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from sys import platform as PlatformName
from sys import version as PythonVersion
from typing import cast as CastValue


# fresh processes must compare both selected compressor receipts at the real ordered writer boundary
def TestMeasuredPat() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = (
        RootValue / "re/tooling/sw2026/linear_pattern/neutral/VerifyMeasuredPattern.py"
    )
    for SlotValue, FacesValue, AlternateSha in (
        ("A", 21, "60f2289933b6fa60bf601521d616c0616e6b56581eda95333e27f0d5092646a5"),
        ("B", 26, "d47491db20319c0851c2960b3f9ae0f733ffd7ecf0de5c99ab715a881e375c2b"),
    ):
        CaseValue = "ColdRaisedPattern" + SlotValue
        Result = RunProcess(
            (Interpreter, "-I", "-B", str(Worker), "--case", CaseValue),
            check=False,
            capture_output=True,
            text=True,
            cwd=RootValue,
            timeout=60,
        )
        assert Result.returncode == 0 and not Result.stderr, Result.stderr
        Report = CastValue(dict[str, object], LoadJson(Result.stdout))
        Runtime = CastValue(str, Report["runtime"])
        assert Report["case"] == CaseValue and Report["runtime_reads"] == 0
        if (
            PlatformName == "win32"
            and PythonVersion
            == "3.14.10 (tags/v3.14.10:b703b2c, Oct 25 2026, 17:36:52) [MSC v.1944 64 bit (AMD64)]"
            and Runtime == "1.3.1.zlib-ng"
        ):
            assert Report["generated_sha256"] == AlternateSha
        if Report["status"] == "unmeasured_compressor_refused":
            assert "zlib-ng" in Runtime
            assert Report["publications"] == 0 and Report["refusals"] == 6
            assert Report["readback_publications"] == Report["readback_refusals"] == 0
        else:
            assert Report["status"] == "native_hash_reproduced"
            Geometry = CastValue(dict[str, object], Report["strict_geometry"])
            assert Geometry["faces"] == FacesValue and Report["streams"] == 10
            assert Report["publications"] == 6 and Report["refusals"] == 20
            assert Report["readback_publications"] == 14
            assert Report["readback_refusals"] == 28
            assert Report["native_processes"] == 0
