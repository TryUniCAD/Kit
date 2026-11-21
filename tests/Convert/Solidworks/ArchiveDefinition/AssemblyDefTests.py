from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the queued verifier starts from a checkout controlled by the runner
KRepoRoot = FilePath(__file__).resolve().parents[4]


# distinct processes must recover both options records without borrowing the source corpus
def TestAsmDef(TmpPath: FilePath) -> None:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/definition/ProveAssemblyDef.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ScriptPath), "--generated"),
        cwd=TmpPath,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode("utf-8", errors="replace")
    assert list(TmpPath.iterdir()) == []
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    Cases = CastValue(list[dict[str, object]], Report["generated"])
    assert Report["guarded_processes"] == 7
    assert Report["runtime_external_attempts"] == 0
    assert [ReportValue["root"] for ReportValue in Cases] == [
        ["uiAssemblyDoc_c", 1]
    ] * 2
    assert [ReportValue["next_map_index"] for ReportValue in Cases] == [7, 7]
    assert [ReportValue["bytes"] for ReportValue in Cases] == [549, 548]
    PrefValues = [
        CastValue(dict[str, object], ReportValue["preferences"])
        for ReportValue in Cases
    ]
    assert [(Value["f10"], Value["f3c"]) for Value in PrefValues] == [
        (0.0, -11),
        (0.9, -12),
    ]
    assert len(CastValue(dict[str, str], Report["refusals"])) == 14
    RenderCase = CastValue(dict[str, object], Report["authored_renderer"])
    RenderDef = CastValue(dict[str, object], RenderCase["definition"])
    assert RenderDef["bytes"] == 559 and RenderDef["next_map_index"] == 7
    assert RenderDef["renderer"] == {"f08": 1, "f0c": 0, "list": {"n": 0, "items": []}}
    assert RenderCase["offset"] == 288
    assert RenderCase["wrapper_frame"] == "0101000000000000000000"
    assert (
        RenderCase["part_word_rejection"]
        == RenderCase["second_word_rejection"]
        == ("SOLIDWORKS assembly Definition has an alternate renderer profile")
    )
