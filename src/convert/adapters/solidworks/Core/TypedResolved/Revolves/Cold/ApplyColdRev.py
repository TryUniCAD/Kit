from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Cold.ColdRevolve import (
    ColdRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.ApplyRevDoc import (
    ApplyRevDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BindThinDoc import (
    BindThinDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.document.Models.DocumentModel import CadDocument


# the single derived body carries the same owner in both geometry and design only reads
def ApplyColdRev(Document: CadDocument, ColdValue: ColdRevolve) -> CadDocument:
    OwnerValue = ColdValue.OwnerValue
    if isinstance(OwnerValue, ThinRevOwner):
        return BindThinDoc(
            Document, ColdValue.LinkValue, OwnerValue, ColdValue.ShapeValue
        )
    FeatureValue = OwnerValue.NodeValue
    NativeId = NativeNodeId(FeatureValue)
    (BodyValue,) = Document.bodies
    if BodyValue.final_feature_id != f"sldprt:feature:{NativeId}":
        raise ValueError("cache-free revolve body differs from its actual creator")
    Bound = ReplaceValue(
        BodyValue,
        name=ReadNativeName(FeatureValue),
        topology=ColdValue.ShapeValue.TopologyValue,
        provenance=TypedProvenance(
            NativeNodeSpan(ColdValue.LinkValue, FeatureValue), str(NativeId)
        ),
    )
    return ApplyRevDoc(
        ReplaceValue(Document, bodies=(Bound,)),
        ColdValue.LinkValue,
        OwnerValue,
    )
