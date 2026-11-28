from convert.Formats.Fusion.BrepCodec.Journal.Attributes.MaterialAttrib import (
    KMaterialFamily,
    MaterialAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the material tag must retain its face ownership and exact UUID text on the wire
def MakeMaterialAttrib(Value: MaterialAttrib) -> AsmRecord:
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (*MakeAttribHead(Value.Links, KMaterialFamily), (4, 1), (7, Value.Tag)),
    )
