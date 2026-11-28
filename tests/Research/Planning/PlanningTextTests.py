from json import dumps as EncodeJson, loads as DecodeJson
from os import environ as OsEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.Planning.PlanningTests import PreparePlan


# utf eight records must survive generation and verification under legacy process locales
def CheckPlanText(TmpPath: FilePath) -> None:
    Command = PreparePlan(TmpPath)
    LinkPath = TmpPath / "Documentation/Planning/Links.json"
    LinkData = DecodeJson(LinkPath.read_text(encoding="utf-8"))
    UnicodeName = "\u00c9ditable \u2192 esquisse"
    LinkData["ExtraTasks"][0]["Name"] = UnicodeName
    _ = LinkPath.write_text(EncodeJson(LinkData, ensure_ascii=False), encoding="utf-8")
    ProcessEnv = dict(OsEnv)
    ProcessEnv.update(PYTHONUTF8="0", PYTHONCOERCECLOCALE="0", LC_ALL="C")
    for Arguments in (Command, [*Command, "--check"]):
        Process = RunProcess(
            Arguments,
            env=ProcessEnv,
            capture_output=True,
            text=True,
            check=False,
        )
        assert Process.returncode == 0, Process.stderr
    TaskPath = TmpPath / "Documentation/Planning/Generated/Tasks.md"
    assert UnicodeName in TaskPath.read_text(encoding="utf-8")
