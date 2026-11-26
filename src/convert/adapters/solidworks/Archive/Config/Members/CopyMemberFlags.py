from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KViewClass,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the observed view windows read these caller flags and preserve their unrelated bits
KViewFlagNames = frozenset(("conditions", "ctx3d0", "ctx87c"))


# bounded members must copy the supported caller context before any archive state is read
def CopyMemberFlags(
    MemberClass: RuntimeClass, FlagSeed: Mapping[str, int] | None
) -> dict[str, int]:
    FlagsValue = dict(FlagSeed or {})
    if FlagsValue and (
        MemberClass != KViewClass
        or not FlagsValue.keys() <= KViewFlagNames
        or any(type(WordValue) is not int for WordValue in FlagsValue.values())
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS configuration member context")
    return FlagsValue
