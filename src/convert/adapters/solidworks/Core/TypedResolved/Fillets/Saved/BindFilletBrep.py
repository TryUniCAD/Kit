from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import (
    CheckBrepOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import (
    ReadCacheFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletTrims import (
    BindFilletTrims,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.Transform import KTransformIdentity


# the native rounded shell and its two real quarter arcs must own the decoded public boundary
def BindFilletBrep(
    History: FilletHistory,
    ModelValue: BrepModel,
    BodyId: str,
) -> BrepModel:
    CheckBrepOwners(ModelValue, BodyId)
    NodesValue = History.StagesValue[0].NodesValue
    KernelBody = RequireXmt(NodesValue, History.BodyIndex, 12)
    Faces = ReadCacheFaces(NodesValue, KernelBody)
    (BodyValue,) = ModelValue.bodies
    if (
        BodyValue.transform != KTransformIdentity
        or len(ModelValue.shells) != 1
        or len(ModelValue.faces) != 7
        or len(ModelValue.edges) != 15
        or len(ModelValue.vertices) != 10
        or {Value.id: Value.surface_id for Value in ModelValue.faces} != Faces
    ):
        raise ValueError(
            "saved fillet public shape differs from its actual native shell"
        )
    Trimmed = BindFilletTrims(NodesValue, ModelValue, History.RadiusValue)
    Bound = ReplaceValue(
        Trimmed, bodies=(ReplaceValue(BodyValue, design_body_id=BodyId),)
    )
    if Bound.validate(frozenset((BodyId,))):
        raise ValueError("saved fillet has invalid oriented trimming topology")
    return Bound
