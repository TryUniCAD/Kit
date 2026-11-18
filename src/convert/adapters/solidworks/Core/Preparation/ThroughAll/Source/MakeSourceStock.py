from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceLine import (
    SourceLine,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceRing import (
    ReadSourceRing,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceScale import (
    ReadSourceScale,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.SourceOps import (
    SourceOps,
)
from interchange.document.Models.DocumentModel import CadDocument


# actual source stock identities and geometry must be preserved while the new output title remains explicitly caller authored
def MakeSourceStock(
    DocumentValue: CadDocument, OwnersValue: SourceOps, OutputName: str
) -> tuple[ThroughStock, tuple[SourceLine, ...]]:
    if not ReadStyleText(OutputName, "explicit generated owner title"):
        raise ValueError("generated owner title must be nonempty authored text")
    Plane = next(
        Value
        for Value in OwnersValue.PlaneValues
        if Value.PlaneId == OwnersValue.StockSketch.support_plane_id
    )
    if OwnersValue.StockProfile.input_feature_ids != (
        Plane.FeatureId,
    ) or OwnersValue.CutProfile.input_feature_ids != (Plane.FeatureId,):
        raise ValueError(
            "source profile parents do not identify their actual common datum"
        )
    Vertices, LinesValue = ReadSourceRing(
        OwnersValue.StockSketch, ReadSourceScale(DocumentValue)
    )
    return (
        ThroughStock(
            ReadStyleText(OutputName, "explicit generated owner title"),
            DocumentValue.configurations[0].name,
            Plane.NameValue,
            OwnersValue.StockSketch.id,
            OwnersValue.StockSketch.name,
            OwnersValue.StockValue.id,
            OwnersValue.StockValue.name,
            OwnersValue.DriverValue.id,
            DocumentValue.bodies[0].id,
            Vertices,
            ReadLength(OwnersValue.DriverValue.value),
            Vertices[2][0] - Vertices[0][0],
            Vertices[2][1] - Vertices[0][1],
            Plane.AxisValue,
        ),
        LinesValue,
    )
