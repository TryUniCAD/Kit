from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import (
    CheckBrepOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.document.Models.DocumentModel import CadDocument


# labels cannot substitute for the complete independently validated body and its actual final feature ownership
def CheckColdBind(
    Document: CadDocument, GeometryValue: PartGeometry, OutputValue: ColdOutput
) -> None:
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
    FeatureId = f"sldprt:feature:{NativeNodeId(OutputValue.BossValue)}"
    if (
        BodyValue.final_feature_id != FeatureId
        or sum(Feature.id == FeatureId for Feature in Document.feature_timeline) != 1
        or ModelValue.bodies[0].design_body_id != BodyValue.id
    ):
        raise ValueError("cold name has conflicting neutral body or feature ownership")
    CheckBrepOwners(ModelValue, BodyValue.id)
