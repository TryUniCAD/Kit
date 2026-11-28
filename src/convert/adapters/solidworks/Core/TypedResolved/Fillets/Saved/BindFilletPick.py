from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.FilletEdge import (
    FilletEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureStep import FeatureStep
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.VectorSpace import SpaceVector


# a typed prior edge can supply a portable pick when legacy descriptors carry no selection token
def ReadFilletPick(
    Document: CadDocument,
    StepValue: FeatureStep,
    StockValue: FeatureStep,
    EdgeValue: FilletEdge,
) -> Selection:
    if StepValue.selection_ids:
        (PickId,) = StepValue.selection_ids
        (PickValue,) = (Value for Value in Document.selections if Value.id == PickId)
        return PickValue
    PickId = StepValue.id + ":edge"
    if any(Value.id == PickId for Value in Document.selections):
        raise ValueError("physical fillet edge identity collides with a public selection")
    return Selection(
        PickId,
        StockValue.name + " edge",
        (SelectPathElem("feature", StockValue.id, f"edge:{EdgeValue.NativeIndex}"),),
    )


# the live selection retains its portable feature path and the actual preceding edge witness
def BindFilletPick(
    PickValue: Selection,
    StockId: str,
    EdgeValue: FilletEdge,
    History: FilletHistory,
) -> Selection:
    if (
        len(PickValue.path) != 1
        or PickValue.path[0].entity_kind != "feature"
        or PickValue.path[0].entity_id != StockId
        or not PickValue.path[0].subelement.startswith("edge:")
    ):
        raise ValueError("saved fillet has a foreign public edge target")
    return ReplaceValue(
        PickValue,
        point=SpaceVector(
            *(
                (First + Final) * 500.0
                for First, Final in zip(*EdgeValue.Endpoints, strict=True)
            )
        ),
        provenance=TypedProvenance(
            NativeNodeSpan(History.LinkValue, EdgeValue.RefValue), PickValue.id
        ),
        attributes=FreezeMapping(
            {
                **PickValue.attributes,
                "native_previous_edge": EdgeValue.NativeIndex,
                "native_previous_faces": EdgeValue.FaceIds,
                "native_edge_endpoints_mm": tuple(
                    tuple(Coord * 1000.0 for Coord in PointValue)
                    for PointValue in EdgeValue.Endpoints
                ),
            }
        ),
    )
