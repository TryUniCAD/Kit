from collections.abc import Sequence
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
from interchange import BrepPayload
from interchange.brep.Topology.BrepModel import BrepModel


# the saved world shell must carry the same active body atom as the actual boss
def CheckCircShell(
    ModelValue: BrepModel, Payloads: Sequence[BrepPayload], AtomValue: int
) -> None:
    Sources = tuple(
        Payload
        for Payload in Payloads
        if Payload.source_stream == KPartitionStream and Payload.kind == "partition"
    )
    if len(Sources) != 1 or Sources[0].data is None:
        raise ValueError("saved circle lacks its unique active partition payload")
    if (
        len(ModelValue.bodies) != 1
        or ModelValue.bodies[0].design_body_id
        or ReadShellAtom(Sources[0].data, ModelValue)["body_atom_id"] != AtomValue
    ):
        raise ValueError(
            "saved circle partition shell disagrees with the live body atom"
        )
