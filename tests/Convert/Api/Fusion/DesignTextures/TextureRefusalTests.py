from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.DesignTextures.RunTexture import RunTexture
from tests.Convert.Api.Fusion.DesignTextures.TextureCase import TextureCase
from tests.Convert.Api.Fusion.SavedCuboid.RunParamStage import RunParamStage
from tests.Convert.Api.Fusion.SavedMaterials.GenMappedBody import GenMappedBody


# unsupported request state must fail before producing any archive
def TestPlaceBadReq(TmpPath: FilePath) -> None:
    Request = TextureCase(TmpPath, (1.125, -0.625, -0.0))
    Original = LoadJson(Request.read_text(encoding="utf-8"))
    Output = Request.with_name("Refused.f3d")
    OriginError = "wood_origin_cm requires three finite binary64 coordinates"
    for Value, Reason in (
        ({**Original, "wood_origin_cm": [True, -0.625, 0.0]}, OriginError),
        ({**Original, "wood_origin_cm": [1.125, -0.625]}, OriginError),
        ({**Original, "wood_origin_cm": [1.125, -0.625, 0]}, OriginError),
        (
            {**Original, "previous_prism_mm": [16.4, 27.1, 13.8]},
            "request fields differ: missing [], unsupported ['previous_prism_mm']",
        ),
    ):
        Payload = DumpJson(Value).encode()
        _ = Request.write_bytes(Payload)
        Result = RunTexture("GenerateSavedCuboid.py", Request, Output)
        assert Result.returncode == 1 and not Output.exists()
        assert (
            Result.stderr.strip()
            == f"Design texture placement generation refused: {Reason}"
        )
        assert Request.read_bytes() == Payload


# complete strict readback can accept a mapping that this narrower generator must refuse
def TestPlaceBadMap(TmpPath: FilePath) -> None:
    Request = TextureCase(TmpPath, (1.125, -0.625, -0.0))
    Candidate = Request.with_name("Distinct.f3d")
    Result = RunParamStage(
        "GenerateSavedCuboid.py",
        TmpPath / "Appearance.json",
        Candidate,
        ResearchFolder="DistinctMaterialAppearances",
    )
    assert Result.returncode == 0, Result.stderr
    Payload = GenMappedBody(Candidate.read_bytes())
    Source = Candidate.with_name("Unsupported.f3d")
    _ = Source.write_bytes(Payload)
    Document = OpenDocument(Source)
    Native = ReadDocument(Payload)
    assert Native.Graphics is None and Document.metadata["fusion.read_only"] is True
    assert (
        CheckContract(Document.metadata["fusion.native_state"], "model", Version=2)
        == Native
    )
    Output = Source.with_name("Refused.json")
    Result = RunTexture("PrepareRequest.py", Source, Output)
    assert Result.returncode == 1 and not Output.exists()
    assert Result.stderr.strip() == (
        "Design texture placement request refused: Unsupported Design texture placement axis"
    )
    assert Source.read_bytes() == Payload
    _ = Output.write_bytes(b"existing request\n")
    Result = RunTexture("PrepareRequest.py", Source, Output)
    assert Result.returncode == 1
    assert (
        Result.stderr.strip()
        == "Design texture placement request refused: Request destination already exists"
    )
    assert (
        Output.read_bytes() == b"existing request\n" and Source.read_bytes() == Payload
    )
