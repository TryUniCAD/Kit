from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyTree import BodyTree
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# semantic projection must retain actual native owners until geometry binding is complete
@DataClass(frozen=True, slots=True)
class BodyNameGraph:
    LinkValue: NativeLink
    NodesValue: Mapping[int, XmtNode]
    TreeValue: BodyTree
    AtomValue: ArchiveNode
    FeatureId: int
    NameValue: str
    IsAuthored: bool
    StreamName: str
    StreamLength: int
    LocalStoreKey: str | None = None
    LocalNameOwner: str | None = None
    MarksValue: tuple[int, int] | None = None
