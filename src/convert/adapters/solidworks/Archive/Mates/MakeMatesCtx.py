from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Mates.MatesLayouts import KMatesLayouts
from convert.adapters.solidworks.Archive.Mates.MatesSchemas import KMatesSchemas
from convert.adapters.solidworks.Archive.Mates.MatesVirtuals import KMatesVirtuals
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
from convert.adapters.solidworks.Archive.Resolved.MakeAsmResCtx import MakeAsmResCtx
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# a stored counter cannot replace the actual assembly objects inherited from resolved data
def MakeMatesCtx(
    ResolvedValue: ResolvedGraph, UsageValue: BodyUsage | None
) -> BodyContext:
    if not isinstance(CastValue(object, ResolvedValue), ResolvedGraph):
        raise TypeError("mate list requires its actual typed resolved graph")
    OwnerValue = FindModelRoot(ResolvedValue.MapValue)
    if OwnerValue.ClassValue.NameValue != "moAssembly_c":
        raise BodyUnsupported("ordinary mate list requires an inherited assembly model")
    ContextValue = MakeAsmResCtx(
        ResolvedValue.VersionValue,
        ResolvedValue.MapValue,
        ResolvedValue.ContextValue,
        UsageValue,
    )
    ContextValue.LayoutsValue = KMatesLayouts
    ContextValue.SchemasValue = KMatesSchemas
    ContextValue.VirtualValue = KMatesVirtuals
    return ContextValue
