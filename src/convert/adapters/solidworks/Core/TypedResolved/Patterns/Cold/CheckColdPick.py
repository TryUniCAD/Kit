from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# an unapplied pattern selects the live seed result and keeps the underlying plate lineage
def CheckColdPick(
    LinkValue: NativeLink,
    OwnersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    AtomIds: tuple[int, ...],
    AtomsValue: tuple[ArchiveNode, ...],
) -> None:
    PlateValue, SeedValue, Pattern = OwnersValue
    ModelValue = LinkValue.ConfigValue.RootValue
    CheckCutWrapper(ModelValue, PlateValue, SeedValue, AtomIds[0], IsCold=True)
    SeedFields = SeedValue.FieldsValue
    PatternFields = Pattern.FieldsValue
    SeedRef = ReadSingleNode(SeedFields.get("f548"), "moCompSolidBody_c")
    PatternRef = ReadSingleNode(PatternFields.get("f548"), "moCompSolidBody_c")
    Fields = PatternRef.FieldsValue
    SeedComp = RequireNative(SeedRef.FieldsValue.get("f58"), "moUnitComponent_c")
    PatternComp = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    CheckTreeAlias(LinkValue, (SeedRef, PatternRef, SeedComp, PatternComp, *AtomsValue))
    if (
        any(
            FieldsValue.get("f544") != 1 or FieldsValue.get("has_f548") != 1
            for FieldsValue in (SeedFields, PatternFields)
        )
        or SeedComp is PatternComp
        or PatternComp.FieldsValue.get("owner") is not ModelValue
        or PatternComp.FieldsValue.get("has_ext") != 0
        or Fields.get("f108") != NativeNodeId(PlateValue)
        or Fields.get("f18") != AtomIds[1]
        or Fields.get("f1c") != AtomIds[1]
        or Fields.get("n110") != 2
        or tuple(RowValue.get("v") for RowValue in NativeRows(Fields.get("f110")))
        != (AtomIds[1], AtomIds[0])
        or Fields.get("ff0") is not None
        or Fields.get("f100") != 0
        or Fields.get("f104") != 0
        or any(
            AtomValue.FieldsValue.get(NameValue) != 0
            for AtomValue in AtomsValue
            for NameValue in ("f180", "f188", "f1b0")
        )
    ):
        raise ValueError("cache free pattern scope contradicts its consumed local seed")
