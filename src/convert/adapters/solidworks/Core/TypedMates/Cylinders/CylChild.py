from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# actual saved child ownership must travel with its independent analytic kernel identities
@DataClass(frozen=True, slots=True)
class CylChild:
    LinkValue: NativeLink
    NodesValue: Mapping[int, XmtNode]
    FaceValue: XmtNode
    SurfaceValue: XmtNode
    FeatureValue: ArchiveNode
    ArcMarker: int
    AtomValue: int
    SourceHash: str
