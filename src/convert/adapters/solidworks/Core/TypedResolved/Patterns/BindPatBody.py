from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Partition.PartTopology import (
    ActivePartMass,
    PartTopology,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureBody import DesignBody


# the verified physical body keeps its identities and supplies bounds and mass from the saved faces
def BindPatBody(
    ModelValue: BrepModel,
    BodyValue: DesignBody,
    NameValue: str,
    Evidence: Mapping[str, object],
) -> tuple[BrepModel, DesignBody]:
    KernelBody = ReplaceValue(ModelValue.bodies[0], design_body_id=BodyValue.id)
    BoundModel = ReplaceValue(ModelValue, bodies=(KernelBody,))
    Summary = PartTopology(BoundModel, BodyValue.id, BodyValue.topology)
    Counts, Measures = ActivePartMass(BoundModel, Summary, BodyValue.id)
    if Measures is None:
        raise ValueError("saved pattern has no measurable closed planar body")
    return BoundModel, ReplaceValue(
        BodyValue,
        name=NameValue,
        topology=Counts,
        attributes=FreezeMapping(
            {
                **BodyValue.attributes,
                "solidworks.native_body": Evidence,
                "solidworks.body_centroid_mm": Measures.Centroid,
            }
        ),
    )
