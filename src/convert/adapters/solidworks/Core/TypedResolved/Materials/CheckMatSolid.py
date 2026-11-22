from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep, DecodePartition
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom


# the physical assignment joins the actual active solid even in a design only sdk read
def CheckMatSolid(ArchiveValue: SldprtArchive, AtomId: int) -> None:
    Payloads = DecodePartition(ArchiveValue.require(KPartitionStream), KPartitionStream)
    ActiveRows = tuple(
        RowValue for RowValue in Payloads if RowValue.kind == "partition"
    )
    if len(ActiveRows) != 1:
        raise BodyUnsupported("SOLIDWORKS material needs one active physical partition")
    (ActiveBody,) = ActiveRows
    ModelValue = DecodeBrep(ActiveBody.data)
    if (
        ModelValue is None
        or len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or not ModelValue.regions[0].solid
    ):
        raise BodyUnsupported("SOLIDWORKS material needs one actual active solid")
    if ReadShellAtom(ActiveBody.data, ModelValue)["body_atom_id"] != AtomId:
        raise BodyUnsupported(
            "SOLIDWORKS material partition atom disagrees with its manager"
        )
