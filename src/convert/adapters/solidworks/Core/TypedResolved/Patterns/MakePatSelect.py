from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# the neutral selection resolves directly to the existing verified datum frame
def MakePatSelect(
    Document: CadDocument, LinkValue: NativeLink, OwnerValue: PatternOwner
) -> Selection:
    Datum = OwnerValue.DatumValue
    PlaneId = NativeNodeId(Datum.PlaneValue)
    PatternId = NativeNodeId(OwnerValue.NodeValue)
    PlaneKey = f"sldprt:plane:{PlaneId}"
    FrameValue = Datum.FrameValue
    Planes = tuple(Value for Value in Document.support_planes if Value.id == PlaneKey)
    Expected = Transform(
        SpaceVector(*(Value * 1000.0 for Value in FrameValue.OriginValue)),
        SpaceVector(*FrameValue.AxisU),
        SpaceVector(*FrameValue.AxisV),
        SpaceVector(*FrameValue.NormalValue),
    )
    if (
        len(Planes) != 1
        or Planes[0].transform != Expected
        or Planes[0].name != ReadNativeName(Datum.PlaneValue)
    ):
        raise ValueError("pattern datum has no corresponding neutral support plane")
    return Selection(
        f"sldprt:selection:{PatternId}:pattern-direction",
        Planes[0].name,
        (SelectPathElem("support_plane", PlaneKey),),
        query=FreezeMapping(
            {
                "native_owner_id": PatternId,
                "native_target_id": PlaneId,
                "topology_role": "linear_pattern_direction",
            }
        ),
        provenance=TypedProvenance(
            NativeNodeSpan(LinkValue, Datum.LineValue), f"{PatternId}:direction"
        ),
    )
