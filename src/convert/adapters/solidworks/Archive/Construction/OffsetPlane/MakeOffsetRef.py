from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# the local compatibility wrapper retains the selected datum and derives its cached frame
def MakeOffsetRef(
    Reference: ArchiveNode, DatumValue: ArchiveNode, FrameValue: PlaneFrame
) -> dict[str, object]:
    Fields = RequireRecord(
        ArchiveNode.RequireNode(DatumValue.FieldsValue["f6f8"]).FieldsValue
    )
    return {
        "f58": Reference,
        "f68": 1,
        "f60": None,
        "f6c": 0,
        "f08": 101,
        "has_f10": 0,
        "has_f18": 0,
        "f0c": -1,
        "f20": 0,
        "f74": -12345,
        "f78": -12345,
        "f7c": -12345,
        "f50": 0,
        "f70": 19000,
        "f34": 0,
        "f30": 0,
        "f98": 0,
        "f38": -1,
        "fd0": MakePoint(
            XValue=FrameValue.OriginValue[0],
            YValue=FrameValue.OriginValue[1],
            ZValue=FrameValue.OriginValue[2],
        ),
        "fe8": MakePoint(
            XValue=FrameValue.NormalValue[0],
            YValue=FrameValue.NormalValue[1],
            ZValue=FrameValue.NormalValue[2],
        ),
        "f100": FrameXform(FrameValue),
        "f188": MakePoint(),
        **{
            FieldName: Fields[BorderName]
            for FieldName, BorderName in zip(
                ("fb0", "fb8", "fc0", "fc8"), ("b0", "b1", "b2", "b3"), strict=True
            )
        },
    }
