from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontRefs import (
    CheckFrontRefs,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileMap import (
    NeedProfileMap,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileDisplay import (
    ProfileDisplay,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadProfileSet import (
    ReadProfileSet,
)


def CheckOriginComponent(DisplayValue: ProfileDisplay) -> ArchiveNode:
    ItemsValue = ReadProfileSet(DisplayValue.FolderValue, 19000).ItemsValue
    Matches = tuple(
        Value for Value in ItemsValue if Value.DisplayValue is DisplayValue.DisplayValue
    )
    if (
        len(Matches) != 1
        or Matches[0].ViewValue is not DisplayValue.ViewValue
        or Matches[0].ReferenceValue is not DisplayValue.ReferenceValue
    ):
        raise ValueError(
            "drawing origin display is not published once in its actual view"
        )
    Fields = DisplayValue.ReferenceValue.FieldsValue
    if (
        any(
            Fields.get(Name) != 0
            for Name in (
                "f18",
                "f1c",
                "f20",
                "f30",
                "f34",
                "f48",
                "f68",
                "f70",
                "f84",
                "fa0",
                "has_fb0",
                "has_fb8",
                "has_fc0",
                "has_fc8",
                "has_fd0",
            )
        )
        or any(Fields.get(Name) != -1 for Name in ("f90", "f94", "f98", "f9c"))
        or Fields.get("f4c") != 19000
    ):
        raise ValueError(
            "drawing origin component has unsupported alias or transform state"
        )
    Component = NeedProfileNode(Fields.get("f58"), "moChainComponent_c")
    ModelValue = NeedProfileNode(Component.FieldsValue.get("owner"), "moDrawing_c")
    Reference = NeedProfileNode(
        DisplayValue.ViewValue.FieldsValue.get("f5d8"), "moReferenceInternal_c"
    )
    CheckFrontRefs(DisplayValue.ViewValue, ModelValue)
    ChainValue = NeedProfileNode(Component.FieldsValue.get("f20"), "moReferenceChain_c")
    ChainFields = ChainValue.FieldsValue
    ListValue = NeedProfileNode(ChainFields.get("f08"), "moExtFeatureList_c")
    RowsValue = ListValue.FieldsValue.get("f08")
    if (
        ChainFields.get("f24") != 0
        or ChainFields.get("f40") != {"f08": "", "f10": -1}
        or ListValue.FieldsValue.get("n") != 1
        or not isinstance(RowsValue, list)
        or len(CastValue(list[object], RowsValue)) != 1
    ):
        raise ValueError(
            "drawing origin requires one ordinary external reference chain"
        )
    External = NeedProfileNode(
        NeedProfileMap(CastValue(list[object], RowsValue)[0]).get("o"), "moExtFeature_c"
    )
    if (
        External is not Reference.FieldsValue.get("f4f8")
        or External.FieldsValue.get("f50") is not Reference
    ):
        raise ValueError("drawing origin chain targets another actual view reference")
    return Reference
