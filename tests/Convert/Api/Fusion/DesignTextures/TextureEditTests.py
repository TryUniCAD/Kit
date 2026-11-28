from copy import deepcopy as CopyValue
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import approx as NearValue

from tests.Convert.Api.Fusion.DesignTextures.GenTexture import GenTexture
from tests.Convert.Api.Fusion.DesignTextures.ReadTexture import ReadTexture
from tests.Convert.Api.Fusion.DesignTextures.RunTexture import RunTexture
from tests.Convert.Api.Fusion.DesignTextures.TextureCase import TextureCase
from tests.Convert.Api.Fusion.SavedCuboid.ReadParamRoles import ReadParamRoles


# explicit origin edits and independent height edits have different dependencies
def TestPlaceEdit(TmpPath: FilePath) -> None:
    Origin = (1.125, -0.625, -0.0)
    Request = TextureCase(TmpPath, Origin)
    Values = LoadJson(Request.read_text(encoding="utf-8"))
    Candidate = Request.with_name("Candidate.f3d")
    GenTexture(Request, Candidate)
    Initial = ReadTexture(Candidate, Origin)
    EditOrigin = (-0.0, 0.125, 1.75)
    Position = CopyValue(Values)
    Position["wood_origin_cm"] = EditOrigin
    _ = Request.write_text(DumpJson(Position), encoding="utf-8")
    PlacedPath = Candidate.with_name("Placed.f3d")
    GenTexture(Request, PlacedPath)
    Placed = ReadTexture(PlacedPath, EditOrigin)
    assert Initial.bodies[0].topology == Placed.bodies[0].topology
    assert ReadParamRoles(Initial) == ReadParamRoles(Placed)
    ChangeHeight(Values)
    _ = Request.write_text(DumpJson(Values), encoding="utf-8")
    TallerPath = Candidate.with_name("Taller.f3d")
    GenTexture(Request, TallerPath)
    Taller = ReadTexture(TallerPath, Origin)
    assert ReadParamRoles(Taller) == ReadParamRoles(Initial)
    assert Initial.bodies[0].topology.volume == NearValue(6133.272)
    assert Taller.bodies[0].topology.volume == NearValue(10888.78)
    Readback = Request.with_name("Taller.json")
    Result = RunTexture("PrepareRequest.py", TallerPath, Readback)
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Readback.read_text(encoding="utf-8")) == Values


# change both stored height values and its literal expression while retaining the driver link
def ChangeHeight(Values: dict[str, object]) -> None:
    Appearance = CastValue(dict[str, object], Values["appearance_request"])
    Material = CastValue(dict[str, object], Appearance["material_request"])
    Config = CastValue(dict[str, object], Material["configuration_request"])
    Camera = CastValue(dict[str, object], Config["camera_request"])
    Cuboid = CastValue(dict[str, object], Camera["cuboid"])
    Binding = CastValue(dict[str, dict[str, object]], Cuboid["parameters"])
    Binding["height"]["value"] = 2.45
    Binding["height_driver"]["value"] = 2.45
    Binding["height_driver"]["expression"] = "24.5 mm"
