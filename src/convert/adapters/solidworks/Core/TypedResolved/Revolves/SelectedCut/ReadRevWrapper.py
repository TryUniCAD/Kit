from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutAtoms import (
    StockCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSaveScope import (
    ReadSaveScope,
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


# a revolve selector couples the consumed body history to the result, which may omit its paired cache words even with a live face
def ReadRevWrapper(
    LinkValue: NativeLink,
    Selected: ArchiveNode,
    CutNode: ArchiveNode,
    AtomsValue: StockCutAtoms,
) -> ArchiveNode:
    if ReadSaveScope(Selected, CutNode, 1) != 1:
        raise ValueError("selected revolve cut needs one explicit body")
    Wrapper = ReadSingleNode(CutNode.FieldsValue.get("f548"), "moCompSolidBody_c")
    Fields = Wrapper.FieldsValue
    AtomId = AtomsValue.ConsumedAtom.FieldsValue["f140"]
    ResultId = AtomsValue.ResultAtom.FieldsValue["f140"]
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    CacheWords = (Fields.get("f108"), Fields.get("f104"), Fields.get("f100"))
    ExpectedWords = (
        ((-1, 0, 0), (NativeNodeId(Selected), 0, 0))
        if Fields.get("ff0") is None
        else ((-1, ResultId, 58), (-1, 0, 0))
    )
    if (
        Component.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        or Component.FieldsValue.get("has_ext") != 0
        or Fields.get("f18") != AtomId
        or Fields.get("f1c") != AtomId
        or Fields.get("n110") != 1
        or tuple(RowValue.get("v") for RowValue in NativeRows(Fields.get("f110")))
        != (AtomId,)
        or CacheWords not in ExpectedWords
        or any(
            Fields.get(NameValue) != 0
            for NameValue in ("has_fb0", "has_fb8", "has_fc0", "has_fc8", "has_fd0")
        )
    ):
        raise ValueError(
            "selected revolve wrapper does not alias its consumed and result bodies"
        )
    CheckTreeAlias(
        LinkValue,
        (
            Wrapper,
            Component,
            AtomsValue.ConsumedAtom,
            AtomsValue.UntouchedAtom,
            AtomsValue.ResultAtom,
        ),
    )
    return Wrapper
