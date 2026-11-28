from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdSolid import (
    ColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureBody import DesignBody
from interchange.Records.RecordTopology import TopologyCounts


# a reconstructed design body belongs to its actual producing feature and analytic solid
def ColdStockBody(Producer: ArchiveNode, SolidValue: ColdSolid) -> DesignBody:
    NativeId = NativeNodeId(Producer)
    BodyId = f"sldprt:body:{NativeId}"
    BrepValue = SolidValue.BrepValue
    if BrepValue.bodies[0].design_body_id != BodyId:
        raise ValueError("cold solid does not retain its actual result producer")
    Center = SolidValue.CenterValue
    return DesignBody(
        BodyId,
        ReadNodeName(Producer),
        f"sldprt:feature:{NativeId}",
        TopologyCounts(
            solid_count=1,
            shell_count=1,
            face_count=len(BrepValue.faces),
            edge_count=len(BrepValue.edges),
            vertex_count=len(BrepValue.vertices),
            volume=SolidValue.VolumeValue,
            surface_area=SolidValue.AreaValue,
            bounding_box=SolidValue.BoundsValue,
            valid=True,
        ),
        attributes=FreezeMapping(
            {
                "native_object_id": NativeId,
                "solidworks.body_centroid_mm": (Center.x, Center.y, Center.z),
            }
        ),
    )
