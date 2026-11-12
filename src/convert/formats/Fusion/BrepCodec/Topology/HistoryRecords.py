from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Attributes.HistoryAttributes import (
    MakeHistoryTags,
)
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Topology.AssignHeads import AssignHeads
from convert.formats.Fusion.BrepCodec.Topology.HistoryLinks import KHistoryHeads
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.CylinderRecords import BuildRecords
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def BuildHistory(
    Model: CylinderBody, Identity: BodyIdentity, TagSet: TopologyTags
) -> tuple[GeometryRecord, ...]:
    Records = list(AssignHeads(BuildRecords(Model), KHistoryHeads))
    BodyRoot = Records[1]
    Records[1] = Replace(
        BodyRoot, Fields=(BodyRoot.Fields[0], Identity.BodyKey, *BodyRoot.Fields[2:])
    )
    return (*Records, *MakeHistoryTags(Identity, TagSet))
