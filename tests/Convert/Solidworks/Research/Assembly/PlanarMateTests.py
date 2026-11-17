from __future__ import annotations

from json import loads as LoadJson
from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Assembly.AssertHeadLink import AssertHeadLink
from tests.Convert.Solidworks.Research.Assembly.AssertScalarBad import AssertScalarBad
from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import (
    KMateLength,
    KMovingOrigin,
    MakeMateInput,
)
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle


# the command boundary must preserve the typed projection through a fresh interpreter
def RunProjection(ParentPath: FilePath, ChildPath: FilePath) -> CompletedProcess[str]:
    Program = KRepoRoot / "re/tooling/sw2026/serial/ProjectPlanarMates.py"
    return RunProcess(
        [PythonExec, "-B", str(Program), str(ParentPath), str(ChildPath)],
        cwd=KRepoRoot,
        env={**Environment, "PYTHONPATH": str(KRepoRoot / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


# child plane identifiers must agree with the part reader independent of mate projection
def AssertMate(
    Report: dict[str, object], ChildPath: FilePath, FeatureIds: tuple[int, int]
) -> None:
    assert Report["version"] == 19000 and Report["mate_list_round_trip"] is True
    (MateValue,) = CastValue(list[dict[str, object]], Report["mates"])
    assert MateValue["name"] == "ProjectedDistance"
    assert MateValue["class"] == "moMateDistanceDim_c"
    assert MateValue["kind"] == "distance" and MateValue["alignment"] == "aligned"
    assert MateValue["driving_distance_m"] == KMateLength
    First, Second = CastValue(list[dict[str, object]], MateValue["entities"])
    assert (First["order"], Second["order"]) == (0, 1)
    assert First["stored_origin_m"] == [0.0, 0.0, 0.0]
    assert Second["stored_origin_m"] == list(KMovingOrigin)
    assert (
        First["occurrence_feature_id"],
        Second["occurrence_feature_id"],
    ) == FeatureIds
    assert First["instance_path"] != Second["instance_path"]
    assert First["child_definition_id"] == Second["child_definition_id"]
    assert First["child_configuration_id"] == Second["child_configuration_id"] == 0
    Child = OpenDocument(ChildPath, include_brep=False, include_tessellation=False)
    (Datum,) = (Plane for Plane in Child.support_planes if Plane.name == "Right Plane")
    assert First["source_entity_id"] == Second["source_entity_id"] == Datum.id
    assert First["datum_name"] == Second["datum_name"] == Datum.name


# valid generated mates must retain their endpoints even when saved selection strings supply none
def TestPlanarMate(TmpPath: FilePath) -> None:
    ParentPath, ChildPath = RunMateBundle(MakeMateInput("original"), TmpPath / "pair")
    AssertHeadLink(ParentPath, ChildPath)
    AssertScalarBad(ParentPath, ChildPath)
    Archive = SldprtArchive.from_bytes(ParentPath.read_bytes())
    NativeAssembly = DecodeNativeAsm(Archive)
    (MateList,) = NativeAssembly.mate_lists
    (Legacy,) = MateList.mates
    assert not Legacy.entities
    FeatureIds = {
        Occurrence.reference_number: Occurrence.feature_id
        for Occurrence in NativeAssembly.occurrences
    }
    assert set(FeatureIds) == {1, 2} and FeatureIds[1] != FeatureIds[2]
    Outcome = RunProjection(ParentPath, ChildPath)
    assert Outcome.returncode == 0, Outcome.stderr
    AssertMate(
        CastValue(dict[str, object], LoadJson(Outcome.stdout)),
        ChildPath,
        (FeatureIds[2], FeatureIds[1]),
    )
    _, WrongChild = RunMateBundle(MakeMateInput("different"), TmpPath / "other")
    Rejected = RunProjection(ParentPath, WrongChild)
    assert Rejected.returncode != 0
    assert "mate wrapper targets a different part identity" in Rejected.stderr
