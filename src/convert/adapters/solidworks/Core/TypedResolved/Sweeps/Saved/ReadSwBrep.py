from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.BindSwTrims import (
    BindSwTrims,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.CheckSwModel import (
    CheckSwModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwTrim import (
    SwRimTrim,
)
from interchange.brep.Topology.BrepModel import BrepModel


# neutral geometry is materialized only when the caller requested the validated saved boundary
def ReadSwBrep(
    Active: bytes,
    BodyValue: XmtNode,
    FacesValue: tuple[XmtNode, ...],
    FirstTrim: SwRimTrim,
    SecondTrim: SwRimTrim,
) -> BrepModel:
    ModelValue = DecodeBrep(Active)
    if ModelValue is None:
        raise ValueError("SOLIDWORKS saved sweep lacks its complete analytic result")
    CheckSwModel(Active, ModelValue, BodyValue, FacesValue)
    return BindSwTrims(ModelValue, FirstTrim, SecondTrim)
