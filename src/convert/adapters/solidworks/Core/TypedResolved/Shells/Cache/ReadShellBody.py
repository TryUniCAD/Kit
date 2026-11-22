from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ReadShellAttrs import (
    ReadShellAttrs,
)


# the native body label is present as a dedicated utf sixteen code unit array
def ShellBodyName(Nodes: Mapping[int, XmtNode], NameSlots: tuple[int, ...]) -> str:
    NodeId, Other = NameSlots
    Units = RequireXmt(Nodes, NodeId, 98).Indexes("values")
    if Other or not Units or any(not 0 < WordValue < 65536 for WordValue in Units):
        raise ValueError("SOLIDWORKS shell has an unqualified active body name")
    return b"".join(WordValue.to_bytes(2, "little") for WordValue in Units).decode(
        "utf-16le"
    )


# active world body and mark confirm the same selected feature and result atom
def ReadShellBody(
    Nodes: Mapping[int, XmtNode],
    AtomValue: ArchiveNode,
    FeatureId: int,
    SelectedMark: int,
) -> str:
    WorldValue = RequireXmt(Nodes, 1, 101)
    BodyValue = RequireXmt(Nodes, WorldValue.Integer("body"), 12)
    if (
        WorldValue.Integer("current_id") != SelectedMark
        or WorldValue.Integer("assembly") != 0
        or BodyValue.Integer("owner") != WorldValue.IndexValue
        or BodyValue.Integer("next") != 0
        or BodyValue.Integer("previous") != 0
        or tuple(Value for Value in Nodes.values() if Value.KindValue == 12)
        != (BodyValue,)
    ):
        raise ValueError(
            "SOLIDWORKS shell partition does not own its active single body"
        )
    Fields = AtomValue.FieldsValue
    Attributes = ReadShellAttrs(Nodes, BodyValue)
    for NameValue, Expected in (
        ("BODY_MATCH", Fields.get("f180")),
        ("ATOM_ID_2001", Fields.get("f140")),
        ("LAST_BODY_MODIFYING_FEATURE_ID", FeatureId),
    ):
        Slots = Attributes[NameValue]
        if (
            (NameValue == "BODY_MATCH" and len(Slots) != 1)
            or (NameValue != "BODY_MATCH" and (len(Slots) != 2 or Slots[0] != 0))
            or RequireXmt(Nodes, Slots[-1], 82).Indexes("values") != (Expected,)
        ):
            raise ValueError(
                "SOLIDWORKS shell partition uses a different result identity"
            )
    return ShellBodyName(Nodes, Attributes["SWIMPLICITBODYNAME_ID_U"])
