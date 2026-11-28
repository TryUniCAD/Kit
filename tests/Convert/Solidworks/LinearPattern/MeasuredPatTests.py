from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from sys import platform as PlatformName
from sys import version as PythonVersion
from typing import cast as CastValue


# the process report binds the actual registry result and the independent geometric witness
def VerifyPatCase(
    RootValue: FilePath,
    Command: list[str],
    FacesValue: int,
    AlternateSha: str,
) -> dict[str, object]:
    Result = RunProcess(
        [*Command, "--verify-runtime-boundary"],
        check=False,
        capture_output=True,
        text=True,
        cwd=RootValue,
        timeout=30,
    )
    assert Result.returncode == 0, Result.stderr
    Report = CastValue(dict[str, object], LoadJson(Result.stdout))
    Shape = CastValue(dict[str, object], Report["semantics"])
    assert Report["case"] == Command[-1]
    if Report["status"] == "native_hash_reproduced":
        assert Report["publication_count"] == 7 and Report["refusal_count"] == 21
        assert Report["published_lf_receipt_count"] == 2
        assert Report["mixed_newline_receipt_refusal_count"] == 2
    else:
        assert Report["status"] == "unmeasured_binary_envelope_refused"
        assert "zlib-ng" in CastValue(str, Report["compression_runtime"])
        assert Report["publication_count"] == 0 and Report["refusal_count"] == 2
    assert Report["runtime_input_file_reads"] == Report["native_launches"] == 0
    assert Report["design_only_history_equal"] is True
    assert Report["strict_history_refusal_count"] == 2
    assert (
        Report["strict_keyword_refusal_count"]
        == Report["permissive_keyword_fallback_count"]
        == 2
    )
    assert Report["permissive_history_unqualified"] is True
    assert Shape["faces"] == FacesValue
    if (
        PlatformName == "win32"
        and PythonVersion
        == "3.14.10 (tags/v3.14.10:b703b2c, Oct 25 2026, 17:36:52) [MSC v.1944 64 bit (AMD64)]"
        and Report["compression_runtime"] == "1.3.1.zlib-ng"
    ):
        assert Report["generated_sha256"] == AlternateSha
    return Report


# each unrelated authored request verifies its ordinary native boundary in a new process
def TestMeasuredPat() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/CheckMeasuredPattern.py"
    Cases = (
        ("A", 21, "60f2289933b6fa60bf601521d616c0616e6b56581eda95333e27f0d5092646a5"),
        ("B", 26, "d47491db20319c0851c2960b3f9ae0f733ffd7ecf0de5c99ab715a881e375c2b"),
    )
    for SlotValue, FacesValue, AlternateSha in Cases:
        Command = [
            Interpreter,
            "-I",
            "-B",
            str(Worker),
            "--root",
            str(RootValue),
            "--case",
            f"ColdRaisedPattern{SlotValue}",
        ]
        Report = VerifyPatCase(RootValue, Command, FacesValue, AlternateSha)
        if Report["generated_sha256"] != AlternateSha:
            continue
        Result = RunProcess(
            [*Command, "--alternate-receipt"],
            check=False,
            capture_output=True,
            text=True,
            cwd=RootValue,
            timeout=30,
        )
        assert Result.returncode == 0, Result.stderr
        Alternate = CastValue(dict[str, object], LoadJson(Result.stdout))
        assert Alternate["status"] == "native_hash_reproduced"
        assert Alternate["generated_sha256"] == AlternateSha
        assert Alternate["publication_count"] == 7 and Alternate["refusal_count"] == 21
        assert Alternate["compression_receipt_refusal_count"] == 6
        assert (
            Alternate["strict_keyword_refusal_count"]
            == Alternate["permissive_keyword_fallback_count"]
            == 2
        )
        assert Alternate["published_lf_receipt_count"] == 2
        assert Alternate["mixed_newline_receipt_refusal_count"] == 2
        assert Alternate["streams"] == Report["streams"]
        assert (
            Alternate["runtime_input_file_reads"] == Alternate["native_launches"] == 0
        )
