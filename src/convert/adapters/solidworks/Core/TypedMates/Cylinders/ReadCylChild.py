from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import (
    ReadCylNodes,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import (
    PickCylFace,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import (
    ReadCylAttr,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import (
    ReadCylOwner,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylSide import (
    CheckCylSide,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange import CadDocument


# public endpoints must bind the same immutable child bytes already loaded through normal component resolution
def ReadCylChild(
    SourcePath: FilePath, Document: CadDocument, ConfigName: str
) -> CylChild:
    BufferValue = SourcePath.read_bytes()
    if (
        HashBytes(BufferValue).hexdigest() != Document.source.sha256
        or len(Document.configurations) != 1
        or Document.configurations[0].name != ConfigName
        or Document.assembly is not None
    ):
        raise ValueError("concentric child bytes or actual configuration differ")
    ArchiveValue = SldprtArchive.from_bytes(BufferValue)
    if ArchiveValue.format_version != 4 or ContainerMo(ArchiveValue.streams) != 19000:
        raise ValueError(
            "concentric child requires the measured current archive version"
        )
    LinkValue = ReadNativeLink(ArchiveValue, 0)
    NodesValue = ReadCylNodes(ArchiveValue)
    FaceValue, SurfaceValue, BodyValue = PickCylFace(NodesValue)
    Attributes = {"ATOM_ID_2001": ReadCylAttr(NodesValue, BodyValue, "ATOM_ID_2001")}
    AtomValue = ReadBodyScalar(NodesValue, Attributes, "ATOM_ID_2001", 1)
    FeatureValue, ArcMarker = ReadCylOwner(LinkValue, AtomValue)
    ChildValue = CylChild(
        LinkValue,
        NodesValue,
        FaceValue,
        SurfaceValue,
        FeatureValue,
        ArcMarker,
        AtomValue,
        Document.source.sha256,
    )
    CheckCylSide(ChildValue)
    return ChildValue
