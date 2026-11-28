from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# modern local plane references retain a complete owned datum without accepting alternate attachments
KOffsetPlaneFields = MappingProxyType(
    {
        "moFaceRefPlnData_c": (
            NativeField("Base", "moRefPlnData_c.serializePlaneData"),
            NativeField("Embed", "f90", "moPlaneRef_w"),
            NativeField("Node", "f98", "moDisplayDistanceDim_c"),
            NativeField("Scalar", "fa0", "i32"),
            NativeField("Scalar", "fa4", "i32"),
            NativeField("Scalar", "has_fa8", "i32"),
            NativeField(
                "Branch",
                "has_fa8",
                BodyValue=(NativeField("Fail", "alternate offset plane attachment"),),
                ModeValue="Nonzero",
            ),
            NativeField("Scalar", "fb4", "i32"),
        ),
    }
)
