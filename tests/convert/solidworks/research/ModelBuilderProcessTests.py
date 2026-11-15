from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.convert.solidworks.research.ModelBuilderProcess import RunBuilders


def AssertPlanes(Report: dict[str, object]) -> None:
    assert Report["plane_ids"] == [0, 1, 2]
    assert Report["next_plane_id"] == 3
    assert Report["plane_normals"] == [
        {"x": 0.0, "y": 0.0, "z": 1.0},
        {"x": 0.0, "y": 1.0, "z": 0.0},
        {"x": 1.0, "y": 0.0, "z": 0.0},
    ]


def AssertSystems(Report: dict[str, object]) -> None:
    Classes = CastValue(list[str], Report["system_classes"])
    Times = CastValue(list[int], Report["folder_times"])
    assert isinstance(Classes, list)
    assert isinstance(Times, list)
    assert Classes[-1] == "moDetailCabinet_c"
    assert {"moEqnFolder_c", "moMaterialFolder_c", "moSolidBodyFolder_c"} <= set(
        Classes
    )
    assert Report["system_ids"] == list(range(3, len(Classes) + 3))
    assert Report["next_persistent_id"] == len(Classes) + 3
    assert Times == [1700000000] * (len(Classes) - 1)


def AssertAudit(Report: dict[str, object]) -> None:
    ModulePaths = CastValue(list[str], Report["module_reads"])
    assert ModulePaths
    assert any(
        "builders" in PathText and "Model" in PathText for PathText in ModulePaths
    )
    assert Report["audit_phase"] == "construction"
    assert Report["runtime_reads"] == []


def TestFreshGraphs(TmpPath: FilePath) -> None:
    Small = RunBuilders(TmpPath, 1, 1234.5, "first-")
    Large = RunBuilders(TmpPath, 7, 7654.25, "independent-構成-")
    assert Small.returncode == 0, Small.stdout + Small.stderr
    assert Large.returncode == 0, Large.stdout + Large.stderr
    First = LoadJson(Small.stdout)
    Second = LoadJson(Large.stdout)
    assert First["configuration_names"] == ["first-0"]
    assert Second["configuration_names"] == [
        f"independent-構成-{Index}" for Index in range(7)
    ]
    assert First["configuration_ids"] == [0]
    assert Second["configuration_ids"] == list(range(7))
    assert First["next_configuration_id"] == 1
    assert Second["next_configuration_id"] == 7
    for Report in (First, Second):
        AssertPlanes(Report)
        AssertSystems(Report)
        AssertAudit(Report)
    assert First["density_kg_m3"] == 1234.5
    assert Second["density_kg_m3"] == 7654.25
    assert First["journal_name"] == "first- journal"
    assert Second["journal_name"] == "independent-構成- journal"
    assert (
        Second["stream_bytes"]["Contents/CMgr"] > First["stream_bytes"]["Contents/CMgr"]
    )
    assert (
        Second["stream_bytes"]["Contents/Definition"]
        > First["stream_bytes"]["Contents/Definition"]
    )
    assert not First["vendor_loadable"] and not Second["vendor_loadable"]
    assert not First["application_usable"] and not Second["application_usable"]
