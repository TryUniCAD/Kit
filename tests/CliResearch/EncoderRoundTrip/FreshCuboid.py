from pathlib import Path as FilePath

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.api.ApiWrite import WriteDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


# independently authored native sources prevent process coverage from depending on captured vendor fixture values
def FreshCuboid(SourcePath: FilePath, Dimensions: tuple[float, float, float]) -> bytes:
    WidthMm, DepthMm, HeightMm = Dimensions
    SourceDoc = MakeFusionDoc(
        DocumentSpec(
            "Fresh Encoder Cuboid",
            "kitHeight",
            HeightMm,
            ProfileKind="cuboid",
            SketchName="Encoder Rectangle",
            ExtrusionName="Encoder Extrusion",
            BodyName="Encoder Cuboid",
            WidthMm=WidthMm,
            DepthMm=DepthMm,
            ConstrainRectangle=True,
            WidthParamName="kitWidth",
            DepthParamName="kitDepth",
        )
    )
    SourceResult = WriteDocument(
        SourceDoc, SourcePath, DestFormat="fusion.f3d", AllowCarrier=False
    )
    assert not SourceResult.dropped and not SourceResult.carrier_capabilities
    return SourcePath.read_bytes()
