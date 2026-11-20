from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import (
    CheckBrepOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep


# labels cannot substitute for the complete independently validated body and its actual final feature ownership
def CheckColdBind(
    Document: CadDocument, GeometryValue: PartGeometry, BossValue: ArchiveNode
) -> FeatureStep:
    ModelValue = Document.brep
    if (
        ModelValue is None
        or ModelValue is not GeometryValue.BrepValue
        or len(Document.bodies) != 1
        or len(ModelValue.bodies) != 1
        or Document.brep_payloads
    ):
        raise ValueError("cold name requires the exact complete cache free solid")
    BodyValue = Document.bodies[0]
    FeatureId = f"sldprt:feature:{NativeNodeId(BossValue)}"
    Producers = tuple(
        Feature for Feature in Document.feature_timeline if Feature.id == FeatureId
    )
    if (
        BodyValue.final_feature_id != FeatureId
        or len(Producers) != 1
        or ModelValue.bodies[0].design_body_id != BodyValue.id
    ):
        raise ValueError("cold name has conflicting neutral body or feature ownership")
    CheckBrepOwners(ModelValue, BodyValue.id)
    return Producers[0]
