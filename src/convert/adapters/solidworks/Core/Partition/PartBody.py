from convert.adapters.solidworks.Core.Partition.PartFeatureId import FeatureId
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.Partition.FinalBodyId import FinalBodyId
from convert.adapters.solidworks.Core.Partition.PartBodyIdentity import KPartBodyId
from convert.adapters.solidworks.Core.Partition.PartTopology import ActivePartMass
from convert.adapters.solidworks.Core.Partition.PartTopology import PartTopology
from convert.adapters.solidworks.Core.Partition.SolidBody import SolidBody
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.LinkLocalBody import (
    LinkLocalBody,
)
from interchange import Body as BodyValue
from interchange import BoundingBox
from interchange import BrepModel
from interchange import BrepPayload
from interchange import FeatureStep
from interchange import Provenance
from interchange import TopologySummary
from interchange import frozen_mapping as FrozenMapping


# preserve body ownership and mass evidence when adapting the selected geometry
def PartBody(
    Model: NativeModel,
    TimeValues: tuple[FeatureStep, ...],
    Payloads: tuple[BrepPayload, ...],
    BrepValue: BrepModel | None,
    LocalOwner: NativeFeature | None,
    ActivePart: ActivePartition | None,
    ColdBrep: BrepModel | None,
    FallbackBounds: BoundingBox | None,
    SourceFeature: Provenance | None,
) -> tuple[tuple[BodyValue, ...], BrepModel | None]:
    SolidOpIds = frozenset(
        (
            FeatureId(Operation.object_id)
            for Operation in Model.operations
            if Operation.kind != "surface"
        )
    )
    FinalFeature = (
        FeatureId(LocalOwner.object_id)
        if LocalOwner is not None
        else FinalBodyId(TimeValues, SolidOpIds)
    )
    BodyFeature = LocalOwner or SolidBody(Model.features)
    MassBody = ActivePart.ModelValue if ActivePart is not None else ColdBrep
    Fallback = TopologySummary(
        solid_count=1 if SolidOpIds else 0, bounding_box=FallbackBounds
    )
    if LocalOwner is not None and BrepValue is not None:
        BrepValue, Fallback = LinkLocalBody(BrepValue, KPartBodyId, Fallback)
    Summary, Measures = ActivePartMass(
        MassBody, PartTopology(MassBody, KPartBodyId, Fallback), KPartBodyId
    )
    Bodies = (
        BodyValue(
            id=KPartBodyId,
            name=BodyFeature.name if BodyFeature is not None else "Body 1",
            final_feature_id=FinalFeature,
            topology=Summary,
            provenance=SourceFeature,
            attributes=FrozenMapping(
                {
                    "native_object_id": (
                        BodyFeature.object_id if BodyFeature is not None else None
                    ),
                    "parasolid_payload_ids": tuple(
                        (Payload.id for Payload in Payloads)
                    ),
                    **(
                        {"parasolid_active_payload_id": ActivePart.PayloadId}
                        if ActivePart is not None and ActivePart.ModelValue is not None
                        else {}
                    ),
                    **(
                        {"solidworks.body_centroid_mm": Measures.Centroid}
                        if Measures is not None
                        else {}
                    ),
                }
            ),
        ),
    )
    return Bodies, BrepValue
