from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Sheet.FeatureVisible import (
    FeatureVisible,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.FeatureZeros import (
    KFeatureZeros,
)
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild


# sheet support features need fresh constructor state tied to authored names and target provenance
def MakeDrawFeature(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    Identifier: int,
    BuildValue: SheetBuild,
) -> ArchiveNode:
    if ClassName not in (
        "moDrSheet",
        "moRefPlane_c",
        "moProfileFeature_c",
        "moDetailFolder_c",
    ):
        raise ValueError(
            "drawing feature seed requires a qualified sheet support class"
        )
    FieldsValue: dict[str, object] = {FieldName: 0 for FieldName in KFeatureZeros}
    FieldsValue.update(
        {
            "owner": OwnerValue,
            "f18": ArchiveNode(RuntimeClass("moNodeName_c", 1), {"f08": NameValue}),
            "f0c": 1,
            "f28": 1073741824,
            "f08": Identifier,
            "f2c": 0,
            "f20": "",
            "has_list68": 0,
            "f78": None,
            "f60": {"list": {"n": 0, "items": ()}, "tail": 0},
            "f29c": 101,
            "f2b0": BuildValue.ArchiveVersion,
            "f1e0": 0.0,
            "f2b4": BuildValue.DateCodeValue,
            "f258": None,
            "f1f8": "",
            "f1f4": 0,
            "f2c8": FeatureVisible(),
            "f2f0": None,
            "f300": BuildValue.ServicePack,
            "f301": BuildValue.SubservicePack,
            "f30c": -1,
            "f98": 2,
            "f2ac": BuildValue.KernelVersion,
            "f344": 1,
            "f200": "",
        }
    )
    return ArchiveNode(RuntimeClass(ClassName, 1), FieldsValue)
