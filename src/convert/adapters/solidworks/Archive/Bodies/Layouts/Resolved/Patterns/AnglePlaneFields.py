from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# both bound plane constraints retain their actual selected point and local coordinates
KAngleCoordinates = (
    NativeField("Scalar", "u", "f64"),
    NativeField("Scalar", "v", "f64"),
    NativeField("Embed", "f20", "mgPoint_c.restore"),
)


# an angled plane must preserve its actual hinge and angular dimension alongside the ordinary plane data
KAnglePlaneFields = MappingProxyType(
    {
        "moConstraintCoincLineAtAnglePlaneRefplaneData_c": (
            NativeField("Base", "moRefPlnData_c.serializePlaneData"),
            NativeField("Node", "f88", "moConstraintRefplaneInterfaceData_c"),
            NativeField("Scalar", "f148", "i32"),
            NativeField("Node", "f150", "moDisplayAngularDim_c"),
        ),
        "moConstraintRefplaneInterfaceData_c": (
            NativeField("Node", "f08", "moRefPlaneAngleGeom_c"),
            NativeField("Node", "f10", "moRefPlaneCoincidentGeom_c"),
            NativeField("Node", "f18", "moRefPlaneCoincidentGeom_c"),
        ),
        "moRefPlaneAngleGeom_c": (
            NativeField("Node", "f08", "moPlaneRef_w"),
            *KAngleCoordinates,
            NativeField("Scalar", "f38", "f64"),
            NativeField("Scalar", "f40", "u8"),
        ),
        "moRefPlaneCoincidentGeom_c": (
            NativeField(
                "Mask",
                "constraint_hinge",
                BodyValue=(NativeField("Node", "f08", "moLineRef_w"),),
                MaskValue=1,
            ),
            *KAngleCoordinates,
        ),
        "moCompRefAxis_c": (
            NativeField("Base", "moCompFeature_c"),
            NativeField("Node", "ff8", "moRefGeom_c"),
        ),
    }
)
