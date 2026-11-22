from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from typing import cast as CastValue


# the process report binds the actual registry result and the independent geometric witness
def VerifyPatCase(SlotValue: str, FacesValue: int) -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/CheckMeasuredPattern.py"
    Result = RunProcess(
        [
            Interpreter,
            "-I",
            "-B",
            str(Worker),
            "--root",
            str(RootValue),
            "--case",
            f"ColdRaisedPattern{SlotValue}",
            "--verify-runtime-boundary",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=RootValue,
        timeout=30,
    )
    assert Result.returncode == 0, Result.stderr
    Report = CastValue(dict[str, object], LoadJson(Result.stdout))
    Shape = CastValue(dict[str, object], Report["semantics"])
    assert Report["case"] == f"ColdRaisedPattern{SlotValue}"
    if Report["status"] == "native_hash_reproduced":
        assert Report["publication_count"] == 7 and Report["refusal_count"] == 21
    else:
        assert Report["status"] == "unmeasured_binary_envelope_refused"
        assert "zlib-ng" in CastValue(str, Report["compression_runtime"])
        assert Report["publication_count"] == 0 and Report["refusal_count"] == 2
    assert Report["runtime_input_file_reads"] == Report["native_launches"] == 0
    assert Report["design_only_history_equal"] is True
    assert Report["strict_history_refusal_count"] == 2
    assert Report["permissive_history_unqualified"] is True
    assert Shape["faces"] == FacesValue


# each unrelated authored request verifies its ordinary native boundary in a new process
def TestMeasuredPat() -> None:
    VerifyPatCase("A", 21)
    VerifyPatCase("B", 26)
