from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import KDirectionAxisRole
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevParams import (
    BindRevParams,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevStep import (
    BindRevStep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.CheckRevSupport import (
    CheckRevSupport,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevSelect import (
    MakeRevSelect,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevSketch import (
    MakeRevSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp


# every projected angular operation keeps its own profile and drivers and selected axis together
def BindRevDoc(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    OwnerValue: RevolveOwner,
    Operation: BooleanOp = BooleanOp.KJoin,
    StockId: str | None = None,
    *,
    CheckFront: bool = False,
) -> CadDocument:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    FeatureId = f"sldprt:feature:{NativeId}"
    SketchId = f"sldprt:sketch:{NativeNodeId(OwnerValue.ProfileValue)}"
    Steps = tuple(
        Value for Value in DocumentValue.feature_timeline if Value.id == FeatureId
    )
    Sketches = tuple(Value for Value in DocumentValue.sketches if Value.id == SketchId)
    if len(Steps) != 1 or len(Sketches) != 1:
        raise ValueError(
            "ordinary revolve lacks its real public feature or consumed sketch"
        )
    if Steps[0].suppressed or Steps[0].configuration_states:
        raise ValueError(
            "ordinary revolve neutral suppression state is outside measured semantics"
        )
    CheckRevSupport(DocumentValue, Sketches[0], OwnerValue, CheckFront=CheckFront)
    Sketch = MakeRevSketch(Sketches[0], OwnerValue)
    Params, ParamIds = BindRevParams(DocumentValue.parameters, OwnerValue)
    Selection = MakeRevSelect(LinkValue, OwnerValue)
    BoundStep = BindRevStep(
        Steps[0], OwnerValue, LinkValue, Selection, ParamIds, Operation, StockId
    )
    Selections = tuple(
        Value
        for Value in DocumentValue.selections
        if not (
            Value.query.get("native_owner_id") == NativeId
            and Value.query.get("topology_role") == KDirectionAxisRole
        )
    )
    if any(Value.id == Selection.id for Value in Selections):
        raise ValueError(
            "ordinary revolve selected axis identity conflicts with an existing neutral selection"
        )
    return ReplaceValue(
        DocumentValue,
        sketches=tuple(
            Sketch if Value.id == SketchId else Value
            for Value in DocumentValue.sketches
        ),
        parameters=Params,
        selections=(*Selections, Selection),
        feature_timeline=tuple(
            BoundStep if Value.id == FeatureId else Value
            for Value in DocumentValue.feature_timeline
        ),
    )
