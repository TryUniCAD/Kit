from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import (
    DIRECTION_AXIS_ROLE as DirectionAxisRole,
)

from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Shells.ShellPartRead import (
    ShellPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.BindShellSketch import (
    BindShellSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureKinds import ShellFeature
from interchange.geometry.Models.Selection import Selection, SelectPathElem


# the portable selection only names the historical stock cap with actual resolved provenance
def ShellSelection(ReadValue: ShellPartRead, StockId: str, ShellId: int) -> Selection:
    SelectionId = f"sldprt:selection:{ShellId}:face:1"
    return Selection(
        SelectionId,
        "Removed stock cap",
        (SelectPathElem("feature", StockId, "face:1"),),
        provenance=TypedProvenance(
            NativeNodeSpan(ReadValue.LinkValue, ReadValue.FaceValue), SelectionId
        ),
    )


# feature shape and topology retain the validated body even when boundary output is omitted
def BindShellDoc(Document: CadDocument, ReadValue: ShellPartRead) -> CadDocument:
    StockId = (
        f"sldprt:feature:{NativeNodeId(ReadValue.StockValue.OwnerValue.NodeValue)}"
    )
    ShellId = NativeNodeId(ReadValue.ShellNode)
    FeatureId = f"sldprt:feature:{ShellId}"
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    StockStep, ShellStep = Steps[StockId], Steps[FeatureId]
    Definition = ShellStep.definition
    (BodyValue,) = Document.bodies
    if (
        not isinstance(Definition, ShellFeature)
        or BodyValue.final_feature_id != FeatureId
        or ShellStep.selection_ids
    ):
        raise ValueError(
            "SOLIDWORKS shell has no unique portable history or active body"
        )
    FacePick = ShellSelection(ReadValue, StockId, ShellId)
    Updates = {
        StockId: ReplaceValue(StockStep, operation=BooleanOp.KCreate),
        FeatureId: ReplaceValue(
            ShellStep,
            selection_ids=(FacePick.id,),
            definition=ReplaceValue(Definition, outward=False),
        ),
    }
    Cache = ReadValue.CacheValue
    AtomNode = ReadValue.AtomValue
    PicksValue = tuple(
        Value
        for Value in Document.selections
        if Value.query.get("topology_role") != DirectionAxisRole
        or Value.query.get("native_owner_id")
        != NativeNodeId(ReadValue.StockValue.OwnerValue.NodeValue)
    )
    return ReplaceValue(
        Document,
        selections=(*PicksValue, FacePick),
        sketches=(
            Document.sketches
            if Cache.DigestValue is None
            and ReadValue.StockValue.LoopValue.DimsValue is None
            else (BindShellSketch(Document.sketches[0], ReadValue.StockValue),)
        ),
        feature_timeline=tuple(
            Updates.get(Value.id, Value) for Value in Document.feature_timeline
        ),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=Cache.NameValue if Cache.NameValue is not None else BodyValue.name,
                topology=Cache.SummaryValue,
                provenance=TypedProvenance(
                    NativeNodeSpan(ReadValue.LinkValue, AtomNode), BodyValue.id
                ),
                attributes=FreezeMapping(
                    {
                        **BodyValue.attributes,
                        "native_object_id": ShellId,
                        "native_atom_id": AtomNode.FieldsValue["f140"],
                        "solidworks.body_centroid_mm": Cache.CentreValue,
                    }
                ),
            ),
        ),
    )
