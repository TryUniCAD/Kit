from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.BindPrismAxes import (
    BindPrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdNameSource import (
    ColdNameSource,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature


# derived geometry and source attribution retain the same stock owner in both public read modes
def BindBoxDoc(DocumentValue: CadDocument, GeometryValue: PartGeometry) -> CadDocument:
    OutputValue = GeometryValue.ColdValue
    if OutputValue is None or GeometryValue.AxesValue is None:
        raise ValueError("cache free box lacks actual name or axis ownership")
    BossId = f"sldprt:feature:{NativeNodeId(OutputValue.BossValue)}"
    (BodyValue,) = DocumentValue.bodies
    (Creator,) = (
        Feature for Feature in DocumentValue.feature_timeline if Feature.id == BossId
    )
    if BodyValue.final_feature_id != BossId or not isinstance(
        Creator.definition, ExtrudeFeature
    ):
        raise ValueError(
            "cache free box neutral body differs from its own signed creator"
        )
    Provenance = ColdNameSource(OutputValue)
    BoundBody = ReplaceValue(
        BodyValue,
        name=OutputValue.NameValue,
        topology=GeometryValue.TopologyValue,
        provenance=Provenance,
    )
    BoundValue = ReplaceValue(
        DocumentValue,
        bodies=(BoundBody,),
        metadata=FreezeMapping(
            {
                **DocumentValue.metadata,
                "solidworks.cachefree_axis_box": GeometryValue.EvidenceValue,
            }
        ),
    )
    return BindPrismAxes(BoundValue, GeometryValue.AxesValue)
