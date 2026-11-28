from dataclasses import replace as ReplaceValue

from convert.adapters.base.NativeEvidence import KRefSupportSource
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector


# centered rectangles have two owned construction lines and one shared local point
def CenterMatRules(
    SketchValue: Sketch, Points: tuple[tuple[float, float], ...]
) -> tuple[tuple[SketchEntity, ...], tuple[SketchRelation, ...]]:
    RootId = SketchValue.id
    Center = SketchEntity(
        f"{RootId}/center",
        GeometryKind.KPoint,
        PointGeometry(PlaneVector(0.0, 0.0)),
        construction=True,
    )
    Diagonals = tuple(
        SketchEntity(
            f"{RootId}/diagonal/{IndexValue}",
            GeometryKind.KLine,
            LineGeometry(
                PlaneVector(*Points[IndexValue]), PlaneVector(*Points[IndexValue + 2])
            ),
            construction=True,
        )
        for IndexValue in range(2)
    )
    Rules = tuple(
        SketchRelation(
            f"{Value.id}/relation",
            "coincident",
            (ConstraintRef(Center.id), ConstraintRef(Value.id)),
        )
        for Value in Diagonals
    )
    return (Center, *Diagonals), Rules


# expand the verified native corner or center into its portable geometry and origin relations
def ExpandMatSketch(SketchValue: Sketch, KindValue: str) -> Sketch:
    Points = ReadRectSketch(
        ReplaceValue(SketchValue, constraints=(), parameter_ids=()), 1.0
    )
    RootId = SketchValue.id
    Origin = SketchEntity(
        f"{RootId}/origin",
        GeometryKind.KPoint,
        PointGeometry(PlaneVector(0.0, 0.0)),
        construction=True,
        fixed=True,
    )
    ExtraEntities: tuple[SketchEntity, ...]
    ExtraRules: tuple[SketchRelation, ...]
    if KindValue == "center":
        ExtraEntities, ExtraRules = CenterMatRules(SketchValue, Points)
        LocalRef = ConstraintRef(ExtraEntities[0].id)
    elif KindValue == "corner":
        ExtraEntities, ExtraRules = (), ()
        LocalRef = ConstraintRef(SketchValue.closed_profile_entity_ids[0][0], "start")
    else:
        raise ValueError("cold material requires a known origin anchor")
    OriginRule = SketchRelation(
        f"{RootId}/origin/relation",
        "coincident",
        (ConstraintRef(Origin.id), LocalRef),
    )
    return ReplaceValue(
        SketchValue,
        entities=(*SketchValue.entities, *ExtraEntities, Origin),
        constraints=(*SketchValue.constraints, *ExtraRules, OriginRule),
        attributes={"support_plane_source": KRefSupportSource},
    )


# a republication may simplify the anchor only after proving its complete expanded identity
def StripMatSketch(SketchValue: Sketch, KindValue: str) -> Sketch:
    BaseValue = ReplaceValue(
        SketchValue,
        entities=SketchValue.entities[:4],
        constraints=SketchValue.constraints[:6],
        attributes={},
    )
    if ExpandMatSketch(BaseValue, KindValue) != SketchValue:
        raise ValueError(
            "cold material source changed the anchor or its owned construction"
        )
    return BaseValue
