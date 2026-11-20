from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtShape import XmtShape

# generic pointer classes require concrete targets for the planar resident profile
KLocalPointerKinds = MappingProxyType(
    {
        1001: (81,),
        1006: (50,),
        1007: (14,),
        1008: (30,),
        1010: (16,),
        1011: (18,),
        1012: (74,),
        1013: (12,),
        1015: (12,),
        1018: (82, 98),
        1019: (81,),
        1029: (12,),
    }
)

# bare bodies still need every mandatory boundary attachment and carrier
KRequiredLinks = MappingProxyType(
    {
        12: (
            "shell",
            "boundary_surface",
            "boundary_curve",
            "boundary_point",
            "region",
            "edge",
            "vertex",
        ),
        13: ("region",),
        14: ("loop", "shell", "surface", "front_shell"),
        15: ("halfedge", "face"),
        16: ("halfedge", "curve", "owner"),
        17: ("loop", "forward", "backward", "vertex", "other", "edge"),
        18: ("halfedge", "point", "owner"),
        19: ("body", "shell"),
        29: ("owner",),
        30: ("owner",),
        50: ("owner",),
        70: ("owner", "finger_block", "list_block"),
        80: ("identifier",),
        81: ("definition", "owner"),
    }
)

# geometry carriers belong to the individual face edge or vertex they represent
KCarrierLinks = MappingProxyType({14: "surface", 16: "curve", 18: "point"})


# stream indices must own correctly typed geometry rather than merely resolve somewhere
def CheckXmtLink(
    NodesValue: Mapping[int, XmtNode], NodeValue: XmtNode, ShapeValue: XmtShape
) -> None:
    if any(
        not NodeValue.Integer(NameValue)
        for NameValue in KRequiredLinks.get(NodeValue.KindValue, ())
    ):
        raise ValueError(
            f"local kernel node is missing a required link: {ShapeValue.NameValue}"
        )
    for FieldValue in ShapeValue.FieldsValue:
        if FieldValue.EncodingValue != "p":
            continue
        TargetKinds = KLocalPointerKinds.get(
            FieldValue.PointerClass, (FieldValue.PointerClass,)
        )
        IndexesValue = (
            NodeValue.Indexes(FieldValue.NameValue)
            if FieldValue.CountValue
            else (NodeValue.Integer(FieldValue.NameValue),)
        )
        for IndexValue in filter(None, IndexesValue):
            TargetValue = NodesValue.get(IndexValue)
            if TargetValue is None or TargetValue.KindValue not in TargetKinds:
                raise ValueError(
                    f"local kernel link is dangling or wrongly typed: {ShapeValue.NameValue}.{FieldValue.NameValue}"
                )
    CarrierField = KCarrierLinks.get(NodeValue.KindValue)
    if CarrierField is not None:
        CarrierValue = NodesValue[NodeValue.Integer(CarrierField)]
        if CarrierValue.Integer("owner") != NodeValue.IndexValue:
            raise ValueError("local kernel geometry carrier has a foreign owner")
