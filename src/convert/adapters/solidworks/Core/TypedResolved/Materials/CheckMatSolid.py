from collections.abc import Sequence

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep, DecodePartition
from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
from interchange import BrepPayload


# the physical assignment joins the actual active solid even in a design only sdk read
def CheckMatSolid(
    ArchiveValue: SldprtArchive,
    AtomId: int,
    Payloads: Sequence[BrepPayload] = (),
    Active: ActivePartition | None = None,
) -> None:
    if Active is None or Active.PayloadId is None:
        Partitions = DecodePartition(
            ArchiveValue.require(KPartitionStream), KPartitionStream
        )
        Frames = tuple(
            RowValue.data for RowValue in Partitions if RowValue.kind == "partition"
        )
    else:
        Frames = tuple(
            RowValue.data
            for RowValue in Payloads
            if RowValue.id == Active.PayloadId
            and RowValue.kind == "partition"
            and RowValue.source_stream == KPartitionStream
            and RowValue.data is not None
        )
    if len(Frames) != 1:
        raise BodyUnsupported("SOLIDWORKS material needs one active physical partition")
    (BodyData,) = Frames
    ModelValue = (
        Active.ModelValue
        if Active is not None and Active.PayloadId is not None
        else DecodeBrep(BodyData)
    )
    if (
        ModelValue is None
        or len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or not ModelValue.regions[0].solid
    ):
        raise BodyUnsupported("SOLIDWORKS material needs one actual active solid")
    if ReadShellAtom(BodyData, ModelValue)["body_atom_id"] != AtomId:
        raise BodyUnsupported(
            "SOLIDWORKS material partition atom disagrees with its manager"
        )
