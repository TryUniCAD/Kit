from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)


# ordinary revolve presentation must retain its complete measured root sequence and actual independently qualified profile axis and angle ownership
def CheckRevRoots(
    LinkValue: NativeLink,
    OrdinaryValue: tuple[ArchiveNode, ...],
    BaseValue: tuple[str, ...],
) -> None:
    if tuple(NodeValue.ClassValue.NameValue for NodeValue in OrdinaryValue) != (
        *BaseValue[:-1],
        "moRevolution_c",
    ):
        raise ValueError("ordinary revolve presentation has an unqualified root layout")
    (OwnerValue,) = ReadRevOwners(LinkValue)
    if (
        OwnerValue.NodeValue is not OrdinaryValue[-1]
        or OwnerValue.ProfileValue is not OrdinaryValue[-2]
    ):
        raise ValueError("ordinary revolve presentation lacks its actual final owners")
