from dataclasses import replace as ReplaceValue
from json import loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackValues

from tests.Convert.Api.Fusion.DesignTextures.ReadTexture import ReadTexture
from tests.Convert.Api.Fusion.DesignTextures.RunTexture import RunTexture
from tests.Convert.Api.Fusion.DesignTextures.TextureCase import TextureCase
from tests.Convert.Api.Fusion.DistinctFinishes.ReadFinishPair import ReadFinishPair


# exact reruns must preserve the authored placement and both finishes and strict document state
def TestPlaceReplay(TmpPath: FilePath) -> None:
    Origin = (1.125, -0.625, -0.0)
    Request = TextureCase(TmpPath, Origin)
    Candidate = Request.with_name("Candidate.f3d")
    Result = RunTexture("GenerateSavedCuboid.py", Request, Candidate)
    assert Result.returncode == 0, Result.stderr
    Document = ReadTexture(Candidate, Origin)
    assert Document.materials[0].ColorValue == (0.25, 0.5, 0.75, 1.0)
    Physical, BodyFace = ReadFinishPair(Candidate.read_bytes())
    assert Physical.Finish.Metallic and Physical.Finish.Roughness == 0.35
    assert BodyFace.SchemaName == "PrismOpaqueSchema"
    Readback = Request.with_name("Readback.json")
    Prepare = RunTexture("PrepareRequest.py", Candidate, Readback)
    assert Prepare.returncode == 0, Prepare.stderr
    Adopted = LoadJson(Readback.read_text(encoding="utf-8"))
    assert Adopted == LoadJson(Request.read_text(encoding="utf-8"))
    assert PackValues(">ddd", *Adopted["wood_origin_cm"]) == PackValues(">ddd", *Origin)
    Repeat = TmpPath / "Repeat"
    Repeat.mkdir()
    ReplayRequest = Repeat / "Placement.json"
    _ = Readback.replace(ReplayRequest)
    _ = Candidate.replace(TmpPath / "Original.archive")
    assert not Candidate.exists() and tuple(Repeat.iterdir()) == (ReplayRequest,)
    Output = Repeat / "Candidate.f3d"
    Result = RunTexture("GenerateSavedCuboid.py", ReplayRequest, Output)
    assert Result.returncode == 0, Result.stderr
    assert Output.read_bytes() == (TmpPath / "Original.archive").read_bytes()
    Replayed = ReadTexture(Output, Origin)
    assert Replayed.source.path == str(Output.resolve())
    assert (
        ReplaceValue(
            Replayed, source=ReplaceValue(Replayed.source, path=Document.source.path)
        )
        == Document
    )
