from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadBossEnd import (
    ReadBossEnd,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrude,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ReadStockRectangle import (
    ReadStockRect,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# each independent producer requires its actual planar rectangle and sole editable blind end
def ReadStockInput(
    NameValue: str,
    FeatureValue: FeatureStep,
    SketchValue: Sketch,
    PlaneValue: SupportPlane,
    DriverValue: Parameter,
    AxisValue: str,
    BodyId: str,
) -> ThroughStock:
    Definition = RequireExtrude(FeatureValue)
    if (
        ReadPrincAxis(PlaneValue.transform) != AxisValue
        or PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
        or PlaneValue.attributes
    ):
        raise ValueError(
            "independent stocks require their fixed canonical Front and Right supports"
        )
    CheckCircDrive(DriverValue, FeatureValue.id, "D1")
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.reversed is not False
        or Definition.symmetric is not False
        or DriverValue.value != Definition.length
        or DriverValue.value.unit != "mm"
    ):
        raise ValueError(
            "two-stock boss requires its actual forward blind millimetre D1"
        )
    EndValue = ReadBossEnd(Definition, AxisValue)
    Vertices = ReadStockRect(SketchValue, 0.001)
    return ThroughStock(
        NameValue,
        "Default",
        PlaneValue.name,
        SketchValue.id,
        SketchValue.name,
        FeatureValue.id,
        FeatureValue.name,
        DriverValue.id,
        BodyId,
        Vertices,
        EndValue.DepthValue,
        Vertices[2][0] - Vertices[0][0],
        Vertices[2][1] - Vertices[0][1],
        AxisValue,
    )
