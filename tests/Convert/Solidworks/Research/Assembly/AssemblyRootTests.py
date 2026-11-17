from __future__ import annotations

from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


# normalized assembly input must build its own root bytes in a separate guarded process
def TestRootBuild() -> None:
    Lengths: list[int] = []
    for NameValue in (
        "Initial unit",
        "Longer assembly title for measured construction",
    ):
        Shared = MakePartInput([], 0.0, NameValue)
        Request = {
            "name": NameValue,
            **{Key: Shared[Key] for Key in ("presentation", "provenance")},
        }
        Outcome = RunProcess(
            [
                PythonExec,
                "-I",
                "-B",
                str(KRepoRoot / "re/tooling/sw2026/AssemblyRootProcess.py"),
                str(KRepoRoot),
            ],
            cwd=KRepoRoot,
            input=DumpJson(Request),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
        assert Report["name"] == NameValue and Report["model_class"] == "moAssembly_c"
        assert (
            Report["reconstructed_bytes_identical"] is Report["maps_consistent"] is True
        )
        assert (
            Report["component_model_binding"]
            is Report["analysis_units_missing"]
            is True
        )
        assert (
            Report["unit_class"] == "moUnitsTable_c"
            and Report["relation_class"] == "moRelMgr_c"
        )
        assert Report["component_total"] == 0 and Report["stream_count"] == 2
        assert Report["denied_reads"] == [] and Report["model_code_reads"]
        assert (
            Report["complete_assembly_emitted"] is Report["native_acceptance"] is False
        )
        Lengths.append(CastValue(int, Report["root_bytes"]))
    assert Lengths[1] > Lengths[0] > 0
