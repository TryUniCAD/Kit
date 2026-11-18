from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the real owning manager and feature must identify the named kernel body without ordinal guesses
def ReadBodyAtom(
    LinkValue: NativeLink,
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    LabelValue: str,
    ExplicitLabel: str | None,
) -> tuple[ArchiveNode, int]:
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Manager = NativeRecord(ModelValue.FieldsValue.get("fd88"))
    ItemsValue = Manager.get("atoms")
    if not isinstance(ItemsValue, list):
        raise ValueError("named body has no unique actual atom manager member")
    ItemsValue = CastValue(list[object], ItemsValue)
    if len(ItemsValue) != 1 or Manager.get("n6c") != 1:
        raise ValueError("named body has no unique actual atom manager member")
    AtomValue = RequireNative(NativeRecord(ItemsValue[0]).get("o"), "moAtom_c")
    AtomsValue = {
        id(EntryValue.EntryValue)
        for EntryValue in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(EntryValue.EntryValue, ArchiveNode)
        and EntryValue.EntryValue.ClassValue.NameValue == "moAtom_c"
    }
    if AtomsValue != {id(AtomValue)} or AtomValue.FieldsValue.get("body_kind") != 0:
        raise ValueError("named body has alternate archive atom ownership")
    BossValues = tuple(
        RequireNative(NodeValue, "moExtrusion_c")
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None and NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    if len(BossValues) != 1:
        raise ValueError("named body has no unique witnessed extrusion owner")
    if ReadOutputAtom(BossValues[0]) is not AtomValue:
        raise ValueError("native output atom differs from the actual manager member")
    FeatureId = NativeNodeId(BossValues[0])
    Expected = {
        "f140": ReadBodyScalar(NodesValue, Attributes, "ATOM_ID_2001", 1),
        "f180": ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0),
        "f1b0": ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0),
        "f12c": FeatureId,
        "f130": FeatureId,
    }
    if (
        ReadBodyScalar(NodesValue, Attributes, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
        != FeatureId
        or any(
            type(AtomValue.FieldsValue.get(NameValue)) is not int
            or AtomValue.FieldsValue[NameValue] != ValueData
            for NameValue, ValueData in Expected.items()
        )
        or Expected["f140"] <= 0
        or Expected["f180"] <= 0
    ):
        raise ValueError("native body atom and feature identity domains disagree")
    if ExplicitLabel is None:
        if (
            AtomValue.FieldsValue.get("f18") is not None
            or AtomValue.FieldsValue.get("f18c") != 1
        ):
            raise ValueError("derived body has an unqualified authored atom name")
    elif (
        AtomValue.FieldsValue.get("f18c") != 0
        or ReadNativeName(AtomValue) != LabelValue
    ):
        raise ValueError("authored atom and kernel body names disagree")
    return AtomValue, FeatureId
