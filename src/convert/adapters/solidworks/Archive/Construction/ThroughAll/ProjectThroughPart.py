from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import (
    CheckPartLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadBossEnd import (
    ReadBossEnd,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircGeom import (
    ReadCircGeom,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrusion,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    CheckPartScope,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ReadStockRectangle import (
    ReadStockRectangle,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.VectorSpace import SpaceVector


# the through cut consumes its actual stock sketch and sole depth driver independently of its depthless termination
def ProjectThroughPart(DocumentValue: CadDocument) -> ThroughPartSpec:
    CheckPartScope(DocumentValue, (1,), HistoryCount=2)
    Plane = CheckPartLinks(DocumentValue)
    Axis = ReadPrincAxis(Plane.transform)
    Scale = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(DocumentValue.units)
    if Scale is None:
        raise ValueError("through-all stock requires explicit modeled length units")
    Boss, Cut = DocumentValue.feature_timeline
    StockSketch, CutSketch = DocumentValue.sketches
    Driver = DocumentValue.parameters[0]
    BossDef = RequireExtrusion(Boss)
    CutDef = RequireExtrusion(Cut, BooleanOp.KCutOperation, (Boss.id,))
    BossEnd = ReadBossEnd(BossDef, Axis)
    CheckCircDrive(Driver, Boss.id, "D1")
    if (
        BossEnd.ModeValue != "mid_plane"
        or BossEnd.IsReversed
        or Boss.parameter_ids != (Driver.id,)
        or Driver.value != BossDef.length
    ):
        raise ValueError("through-all stock requires its actual total mid-plane depth")
    if (
        CutDef.end_condition != ExtrudeEnd.KThroughAll
        or CutDef.length is not None
        or CutDef.second_length is not None
        or CutDef.second_end_condition not in (None, ExtrudeEnd.KThroughAll)
        or CutDef.symmetric
        or CutDef.direction
        not in (None, SpaceVector(*PrincipalFrame(Axis).NormalValue))
        or Cut.parameter_ids
        or CutSketch.parameter_ids
        or CutSketch.constraints
    ):
        raise ValueError("through-all cut requires depthless ends and one free circle")
    Name = ReadStyleText(DocumentValue.metadata.get("name"), "neutral document name")
    if not Name:
        raise ValueError("through-all construction requires an authored document name")
    Vertices = ReadStockRectangle(StockSketch, Scale)
    Stock = ThroughStock(
        NameValue=Name,
        ConfigName=DocumentValue.configurations[0].name,
        PlaneName=Plane.name,
        SketchId=StockSketch.id,
        SketchName=StockSketch.name,
        FeatureId=Boss.id,
        FeatureName=Boss.name,
        ParameterId=Driver.id,
        BodyId=DocumentValue.bodies[0].id,
        VerticesValue=Vertices,
        DepthValue=BossEnd.DepthValue,
        WidthValue=Vertices[2][0] - Vertices[0][0],
        HeightValue=Vertices[2][1] - Vertices[0][1],
        AxisValue=Axis,
    )
    return ThroughPartSpec(
        Stock,
        ReadCircGeom(CutSketch, Scale),
        CutSketch.name,
        Cut.name,
        ThroughEndInput(
            "through_all_both" if CutDef.second_end_condition else "through_all",
            CutDef.reversed,
            BossEnd.VersionValue,
        ),
    )
