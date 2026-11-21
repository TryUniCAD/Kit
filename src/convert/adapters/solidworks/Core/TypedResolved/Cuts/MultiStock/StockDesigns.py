from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.BodyCacheView import (
    BodyCacheView,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockTopCount import (
    StockTopCount,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Payloads.PayloadRecord import BrepPayload


# physical body provenance follows the verified atom producer and its actual active partition
def StockDesigns(
    CacheValue: BodyCacheView,
    StepsValue: tuple[FeatureStep, ...],
    Payloads: tuple[BrepPayload, ...],
) -> tuple[DesignBody, ...]:
    PayloadIds = tuple(
        Payload.id
        for Payload in Payloads
        if Payload.source_stream == CacheValue.StreamName
        and Payload.kind == "partition"
    )
    if len(PayloadIds) != 1:
        raise ValueError("selected two stock bodies lack their active payload")
    Steps = {Value.id: Value for Value in StepsValue}
    TopologyValue = BrepTopology(CacheValue.BrepValue)
    Bodies = []
    for OwnerValue, BodyValue in zip(
        CacheValue.BodyValues, CacheValue.BrepValue.bodies, strict=True
    ):
        NativeId = NativeNodeId(OwnerValue.ProducerValue)
        StepValue = Steps[f"sldprt:feature:{NativeId}"]
        if BodyValue.design_body_id != OwnerValue.DesignId:
            raise ValueError(
                "selected two stock design body differs from its physical owner"
            )
        Bodies.append(
            DesignBody(
                OwnerValue.DesignId,
                OwnerValue.NameValue,
                StepValue.id,
                StockTopCount(TopologyValue, BodyValue),
                provenance=StepValue.provenance,
                attributes=FreezeMapping(
                    {
                        "native_object_id": NativeId,
                        "native_atom_id": OwnerValue.AtomId,
                        "native_kernel_body_index": OwnerValue.KernelValue.IndexValue,
                        "parasolid_payload_ids": PayloadIds,
                    }
                ),
            )
        )
    return tuple(Bodies)
