from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from sys import platform as PlatformName
from typing import cast as CastValue


# two disclosed independent thin families exercise the measured writer and strict readers in fresh processes
def TestThinProof() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/revolve/ThinArchive/VerifyFreshThin.py"
    WindowsArgs = ("--windows-path",) if PlatformName == "win32" else ()
    for CaseValue, DriverCount, DigestValue in (
        (
            "ThinUnequal",
            3,
            "871b920ad7f1ce34a25aaffb21d5fbf4cb8c79b1e67a1c486a235fb29f2c4207",
        ),
        (
            "ThinRightCenterControl",
            2,
            "c5d8880148f4ff4cd40298020e9d6cf54904cec23c12f45ea87ffa6c325710aa",
        ),
    ):
        Result = RunProcess(
            (Interpreter, "-I", "-B", str(Worker), "--case", CaseValue, *WindowsArgs),
            check=False,
            capture_output=True,
            text=True,
            cwd=RootValue,
            timeout=45,
        )
        assert Result.returncode == 0 and not Result.stderr, Result.stderr
        Report = CastValue(dict[str, object], LoadJson(Result.stdout))
        assert Report["case"] == CaseValue and Report["expected_sha256"] == DigestValue
        assert Report["streams"] == 10 and Report["native_processes"] == 0
        assert Report["runtime_input_reads"] == Report["read_runtime_input_reads"] == 0
        Readback = CastValue(dict[str, dict[str, object]], Report["readback"])
        FullValue = Readback["full"]
        assert (FullValue["faces"], FullValue["edges"], FullValue["vertices"]) == (
            6,
            12,
            8,
        )
        assert len(CastValue(list[str], Readback["design"]["drivers"])) == DriverCount
        if Report["status"] == "unmeasured_compressor_refused":
            assert "zlib-ng" in CastValue(str, Report["runtime"])
            assert Report["generated_sha256"] != DigestValue
            assert Report["publications"] == Report["path_publications"] == 0
            assert Report["refusals"] == 12
        else:
            assert Report["status"] == "exact"
            assert Report["generated_sha256"] == DigestValue
            assert Report["publications"] == 6 and Report["refusals"] == 30
            assert Report["path_publications"] == (3 if WindowsArgs else 0)
