from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    EllipPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import SketchEntity


# the admitted conic replaces heuristic marker geometry without changing the actual neutral feature or parameter identities
def BindEllipDoc(Document: CadDocument, PartValue: EllipPartRead) -> CadDocument:
    (Sketch,) = Document.sketches
    (BodyValue,) = Document.bodies
    FeatureId = f"sldprt:feature:{NativeNodeId(PartValue.BossValue.NodeValue)}"
    ProfileId = NativeNodeId(PartValue.BossValue.ProfileValue)
    BossValue = next(
        Value for Value in Document.feature_timeline if Value.id == FeatureId
    )
    (Driver,) = (Value for Value in Document.parameters if Value.owner_id == FeatureId)
    if (
        Sketch.id != f"sldprt:sketch:{ProfileId}"
        or BossValue.sketch_id != Sketch.id
        or BossValue.name != ReadNativeName(PartValue.BossValue.NodeValue)
        or BossValue.parameter_ids != (Driver.id,)
        or Driver.name != "D1"
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or type(BossValue.definition) is not ExtrudeFeature
        or BossValue.definition.end_condition != ExtrudeEnd.KBlind
        or BossValue.definition.length != Driver.value
        or BodyValue.final_feature_id != FeatureId
    ):
        raise ValueError(
            "ellipse read lacks the same live neutral sketch and boss parameter"
        )
    EntityId = f"{Sketch.id}:ellipse:{PartValue.SegmentId}"
    Entity = SketchEntity(
        EntityId,
        GeometryKind.KEllipse,
        PartValue.GeometryValue,
        provenance=TypedProvenance(
            NativeNodeSpan(PartValue.LinkValue, PartValue.SketchValue), EntityId
        ),
    )
    return ReplaceValue(
        Document,
        sketches=(
            ReplaceValue(
                Sketch,
                entities=(Entity,),
                constraints=(),
                closed_profile_entity_ids=((EntityId,),),
                attributes=FreezeMapping(
                    {
                        **Sketch.attributes,
                        "native_profile_count": 1,
                        "ellipse_entity_id": PartValue.SegmentId,
                        "ellipse_point_ids": PartValue.PointIds,
                    }
                ),
            ),
        ),
        feature_timeline=tuple(
            (
                ReplaceValue(Value, operation=BooleanOp.KCreate)
                if Value is BossValue
                else Value
            )
            for Value in Document.feature_timeline
        ),
        bodies=(
            ReplaceValue(
                BodyValue, name=BossValue.name, provenance=BossValue.provenance
            ),
        ),
    )
