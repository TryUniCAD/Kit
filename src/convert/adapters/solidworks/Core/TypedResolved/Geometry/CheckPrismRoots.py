from collections import Counter
from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# a single visible extrusion is insufficient unless the complete resolved inventory contains only the ordinary system and its one profile
def CheckPrismRoots(
    Features: Mapping[int, ArchiveNode],
    NodesValue: tuple[ArchiveNode, ...],
    *,
    SolidClass: str = "moExtrusion_c",
    RequiredClasses: tuple[str, ...] = ("moEndSpec_c", "moFromEndSpec_c"),
) -> None:
    CountsValue = Counter(
        NodeValue.ClassValue.NameValue for NodeValue in Features.values()
    )
    Expected = dict.fromkeys(
        KSystemFolders
        | {
            "moDetailCabinet_c",
            "moOriginProfileFeature_c",
            "moProfileFeature_c",
            SolidClass,
        },
        1,
    )
    Expected["moRefPlane_c"] = 3
    if CountsValue != Expected:
        raise ValueError(
            "cache free prism requires the whole ordinary single boss inventory"
        )
    for ClassName in (
        "moPart_c",
        "moProfileFeature_c",
        SolidClass,
        "moOriginProfileFeature_c",
        *RequiredClasses,
    ):
        if (
            sum(NodeValue.ClassValue.NameValue == ClassName for NodeValue in NodesValue)
            != 1
        ):
            raise ValueError(
                "cache free prism has duplicate or detached geometry owners"
            )
    if (
        sum(NodeValue.ClassValue.NameValue == "sgSketch" for NodeValue in NodesValue)
        != 2
    ):
        raise ValueError(
            "cache free prism requires only its profile and origin sketches"
        )
    for ClassName, CountValue in (
        ("moDefaultRefPlnData_c", 3),
        ("moCompRefPlane_c", 2),
    ):
        if (
            sum(NodeValue.ClassValue.NameValue == ClassName for NodeValue in NodesValue)
            != CountValue
        ):
            raise ValueError("cache free prism has extra datum or support owners")
    for NodeValue in Features.values():
        Fields = NodeValue.FieldsValue
        if (
            Fields.get("f0c") not in (0, 1)
            or Fields.get("f2c") != 0
            or Fields.get("f2b0") != 19000
        ):
            raise ValueError("cache free prism has unqualified feature state")
        if Fields.get("has_list68") != 0 or Fields.get("f78") is not None:
            raise ValueError("cache free prism has extra concept ownership")
        if (
            NodeValue.ClassValue.NameValue != SolidClass
            and Fields.get("f28") != 0x40000000
        ):
            raise ValueError("cache free prism has alternate feature flags")
        if NodeValue.ClassValue.NameValue != SolidClass and not IsLineState(
            Fields.get("f60")
        ):
            raise ValueError("cache free prism has additional feature dependencies")
