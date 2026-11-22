from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.Partition.PartTopology import (
    ActivePartMass,
    PartTopology,
)
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureBody import DesignBody
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Records.RecordProvenance import Provenance
from interchange.Records.RecordTopology import TopologyCounts


# part history needs a stable body projection regardless of how the active partition was selected
def BuildPartBody(
    BodyId: str,
    BodyFeature: NativeFeature | None,
    FinalFeature: str,
    TopologyValue: TopologyCounts,
    ActivePart: ActivePartition | None,
    Payloads: tuple[BrepPayload, ...],
    ProvenanceValue: Provenance | None,
) -> DesignBody:
    SavedPart = ActivePart.ModelValue if ActivePart is not None else None
    Summary, Measures = ActivePartMass(
        SavedPart, PartTopology(SavedPart, BodyId, TopologyValue), BodyId
    )
    return DesignBody(
        id=BodyId,
        name=BodyFeature.name if BodyFeature is not None else "Body 1",
        final_feature_id=FinalFeature,
        topology=Summary,
        provenance=ProvenanceValue,
        attributes=FreezeMapping(
            {
                "native_object_id": (
                    BodyFeature.object_id if BodyFeature is not None else None
                ),
                "parasolid_payload_ids": tuple(Payload.id for Payload in Payloads),
                **(
                    {"parasolid_active_payload_id": ActivePart.PayloadId}
                    if ActivePart is not None
                    and SavedPart is not None
                    and ActivePart.PayloadId is not None
                    else {}
                ),
                **(
                    {"solidworks.body_centroid_mm": Measures.Centroid}
                    if Measures is not None
                    else {}
                ),
            }
        ),
    )
