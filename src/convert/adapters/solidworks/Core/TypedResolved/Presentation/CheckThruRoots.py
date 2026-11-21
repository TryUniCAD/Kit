from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckThruShape import (
    CheckThruShape,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruOwners import (
    ReadThruOwners,
)


# a second profile and cut may extend the ordinary prefix only through the independently qualified source semantics
def CheckThruRoots(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    RootsValue: tuple[ArchiveNode, ...],
    BaseKinds: tuple[str, ...],
) -> None:
    Expected = (*BaseKinds, "moProfileFeature_c", "moICE_c")
    if (
        LinkValue.ConfigValue.VersionValue != 19000
        or LinkValue.ResolvedValue.VersionValue != 19000
        or tuple(Value.ClassValue.NameValue for Value in RootsValue) != Expected
        or tuple(Features.values()) != LinkValue.ResolvedValue.RootsValue
    ):
        raise ValueError("part presentation has an unqualified root layout")
    CheckTreeAlias(LinkValue, tuple(Features.values()))
    StockValue, CutValue = ReadThruOwners(LinkValue, Features, RootsValue)
    CheckThruShape(LinkValue, Features, StockValue, CutValue)
