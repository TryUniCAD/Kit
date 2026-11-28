from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatPart import (
    ColdPatPart,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Selection import Selection, SelectPathElem


# the validated chooser retains its real prior stock and its native wrapper span
def MakeStockPick(
    LinkValue: NativeLink, OwnerValue: ArchiveNode, TargetValue: ArchiveNode
) -> Selection:
    OwnerId, TargetId = NativeNodeId(OwnerValue), NativeNodeId(TargetValue)
    Wrapper = ReadSingleNode(OwnerValue.FieldsValue.get("f548"), "moCompSolidBody_c")
    Identity = f"sldprt:selection:{OwnerId}:stock-body"
    return Selection(
        Identity,
        ReadNativeName(TargetValue),
        (SelectPathElem("feature", f"sldprt:feature:{TargetId}", "body"),),
        query=FreezeMapping(
            {
                "native_owner_id": OwnerId,
                "native_target_id": TargetId,
                "topology_role": "selected_stock",
            }
        ),
        provenance=TypedProvenance(NativeNodeSpan(LinkValue, Wrapper), Identity),
    )


# replace only synthetic legacy axis picks belonging to the two ordinary blind stocks
def ApplyPatStock(Document: CadDocument, PatternValue: ColdPatPart) -> CadDocument:
    PlateValue, SeedValue = PatternValue.StocksValue
    PlateNode, SeedNode = (
        PlateValue.OwnerValue.NodeValue,
        SeedValue.OwnerValue.NodeValue,
    )
    PlateId, SeedId = NativeNodeId(PlateNode), NativeNodeId(SeedNode)
    SeedPick = MakeStockPick(PatternValue.LinkValue, SeedNode, PlateNode)
    PatternPick = MakeStockPick(
        PatternValue.LinkValue, PatternValue.OwnerValue.NodeValue, SeedNode
    )
    Steps = {Value.id: Value for Value in Document.feature_timeline}
    PlateKey, SeedKey = f"sldprt:feature:{PlateId}", f"sldprt:feature:{SeedId}"
    PatternKey = f"sldprt:feature:{NativeNodeId(PatternValue.OwnerValue.NodeValue)}"
    Plate, SeedOwner, Pattern = Steps[PlateKey], Steps[SeedKey], Steps[PatternKey]
    if (
        type(Plate.definition) is not ExtrudeFeature
        or type(SeedOwner.definition) is not ExtrudeFeature
        or Plate.operation is not BooleanOp.KCreate
        or SeedOwner.operation is not BooleanOp.KJoin
        or Plate.selection_ids
        or SeedOwner.selection_ids
        or len(Pattern.selection_ids) != 1
    ):
        raise ValueError(
            "cold pattern cannot identify the actual body-producing timeline"
        )
    Replacements = {
        PlateKey: ReplaceValue(
            Plate,
            definition=ReplaceValue(
                Plate.definition, direction=PlateValue.PlanValue.FrameValue.z_axis
            ),
        ),
        SeedKey: ReplaceValue(
            SeedOwner,
            input_feature_ids=(PlateKey, *SeedOwner.input_feature_ids),
            selection_ids=(SeedPick.id,),
            definition=ReplaceValue(
                SeedOwner.definition, direction=SeedValue.PlanValue.FrameValue.z_axis
            ),
        ),
        PatternKey: ReplaceValue(
            Pattern,
            operation=BooleanOp.KJoin,
            selection_ids=(*Pattern.selection_ids, PatternPick.id),
        ),
    }
    Retained = tuple(
        Value
        for Value in Document.selections
        if not (
            Value.query.get("topology_role") == "direction_axis"
            and Value.query.get("native_owner_id") in (PlateId, SeedId)
            and len(Value.path) == 1
            and (Value.path[0].entity_kind, Value.path[0].subelement)
            == ("native", "N_Axis")
        )
    )
    return ReplaceValue(
        Document,
        selections=(*Retained, SeedPick, PatternPick),
        feature_timeline=tuple(
            Replacements.get(Value.id, Value) for Value in Document.feature_timeline
        ),
    )
