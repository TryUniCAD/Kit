from __future__ import annotations

from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest

# native discovery distinguishes sixteen serialized roots from additional visible assembly nodes
KAssemblyRoots = [
    "moCommentsFolder_c",
    "moFavoriteFolder_c",
    "moHistoryFolder_c",
    "moSelectionSetFolder_c",
    "moSensorFolder_c",
    "moLiveSectionFolder_c",
    "moDocsFolder_c",
    "moDetailCabinet_c",
    "moEnvFolder_c",
    "moInkMarkupFolder_c",
    "moEqnFolder_c",
    "moRefPlane_c",
    "moRefPlane_c",
    "moRefPlane_c",
    "moOriginProfileFeature_c",
    "moMateGroup_c",
]


# normalized assembly input must build its own root bytes in a separate guarded process
def TestRootBuild() -> None:
    Lengths: list[int] = []
    for NameValue, FractionPreference, ExpectedValue in (
        ("Initial unit", -0.2, 0.0),
        ("Longer assembly title for measured construction", 1.2, 0.9),
    ):
        Request = RootRequest(NameValue, FractionPreference)
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
        assert Report["component_total"] == 0 and Report["stream_count"] == 6
        assert Report["configuration_class"] == "moConfiguration_c"
        assert Report["configuration_name"] == "Named assembly configuration"
        assert Report["resolved_types"] == KAssemblyRoots
        assert Report["live_section_flag"] == 1
        assert (
            Report["manager_bytes_identical"]
            is Report["resolved_bytes_identical"]
            is True
        )
        assert Report["empty_mates_linked"] is True
        assert Report["definition_bytes_identity"] is True
        assert Report["definition_class"] == "uiAssemblyDoc_c"
        assert Report["definition_journal"] == NameValue
        assert Report["save_as_part_fraction"] == ExpectedValue
        assert Report["denied_reads"] == [] and Report["model_code_reads"]
        assert (
            Report["complete_assembly_emitted"] is Report["native_acceptance"] is False
        )
        Lengths.append(CastValue(int, Report["root_bytes"]))
    assert Lengths[1] > Lengths[0] > 0
