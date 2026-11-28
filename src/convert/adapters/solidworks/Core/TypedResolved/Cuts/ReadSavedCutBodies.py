from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)


# an ordinary saved cut consumes the actual boss output and creates a distinct solid atom
def ReadCutBodies(
    BossValue: ArchiveNode, CutValue: ArchiveNode, ManagedValues: set[ArchiveNode]
) -> tuple[int, int]:
    BossFields, CutFields = BossValue.FieldsValue, CutValue.FieldsValue
    if (
        BossFields.get("has_f528") != 1
        or BossFields.get("has_f530") != 0
        or CutFields.get("has_f528") != 1
        or CutFields.get("has_f530") != 1
        or BossFields.get("f538") is not None
        or CutFields.get("f538") is not None
    ):
        raise ValueError("ordinary saved cut has an alternate atom collection")
    BossAtom = ReadSingleNode(BossFields.get("f528"), "moAtom_c")
    CutAtom = ReadSingleNode(CutFields.get("f528"), "moAtom_c")
    if (
        ReadSingleNode(CutFields.get("f530"), "moAtom_c") is not BossAtom
        or BossAtom is CutAtom
        or ManagedValues != {BossAtom, CutAtom}
    ):
        raise ValueError("cut body dependency does not alias its managed boss output")
    BossId = ReadCutAtomId(BossAtom, BossValue)
    CutId = ReadCutAtomId(CutAtom, CutValue)
    if BossId == CutId:
        raise ValueError(
            "ordinary cut preserves distinct input and output atom identities"
        )
    return BossId, CutId


# hash pinned through cut readers still import the original saved body helper
ReadSavedCutBodies = ReadCutBodies
