from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckNamedAtom import (
    CheckNamedAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyOwner import (
    ReadBodyOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the real owning manager and feature must identify the named kernel body without ordinal guesses
def ReadBodyAtom(
    LinkValue: NativeLink,
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    LabelValue: str,
    ExplicitLabel: str | None,
    *,
    RevolveValue: ArchiveNode | None = None,
) -> tuple[ArchiveNode, int]:
    BossValue = ReadBodyOwner(LinkValue, RevolveValue)
    return CheckNamedAtom(
        LinkValue, BossValue, NodesValue, Attributes, LabelValue, ExplicitLabel
    )
