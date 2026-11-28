from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.BindSwTrims import (
    SwNativeId,
)
from interchange.brep.Topology.BrepModel import BrepModel


# shared analytic decoding must return exactly the solid and faces verified in the physical graph
def CheckSwModel(
    Active: bytes,
    ModelValue: BrepModel,
    BodyValue: XmtNode,
    FacesValue: tuple[XmtNode, ...],
) -> None:
    OwnerValue = ReadShellAtom(Active, ModelValue)
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or len(ModelValue.shells) != 1
        or len(ModelValue.vertices) != 2
        or not ModelValue.regions[0].solid
        or not ModelValue.shells[0].closed
        or OwnerValue.get("native_owner") != BodyValue.IndexValue + 1
        or OwnerValue.get("native_shell") != BodyValue.Integer("shell") + 1
        or tuple(Value.id for Value in ModelValue.faces)
        != tuple(SwNativeId("face", Value) for Value in FacesValue)
        or ModelValue.validate()
    ):
        raise ValueError("SOLIDWORKS saved sweep analytic result has foreign topology")
