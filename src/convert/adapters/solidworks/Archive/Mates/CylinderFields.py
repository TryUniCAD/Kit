from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Mates.FacetFields import KFacetFields
from convert.adapters.solidworks.Archive.Mates.SurfaceTail import KSurfaceTail
from convert.adapters.solidworks.Archive.Mates.WrapperTail import KWrapperTail

# support cylinders and selected faces follow distinct native component reference owners
KCylinderFields = MappingProxyType(
    {
        "moCylinderRef_w": (
            NativeField("Node", "f58"),
            *KWrapperTail,
            *KSurfaceTail,
            NativeField("Embed", "fd0", "mgPoint_c.restore"),
            NativeField("Embed", "fe8", "mgVector_c.restore"),
            NativeField("Scalar", "f100", "f64"),
            NativeField(
                "Present",
                "has_f108",
                "u16",
                BodyValue=(NativeField("Embed", "f108", "mgVector_c.restore"),),
            ),
        ),
        "moCompRefCylinder_c": (
            NativeField("Base", "moCompFeature_c"),
            NativeField("Node", "ff8", "moRefGeom_c"),
        ),
        "moCompFace_c": (
            NativeField("Base", "moCompRef_c"),
            NativeField("Scalar", "alias", "u8"),
            NativeField(
                "Branch",
                "alias",
                BodyValue=(NativeField("Text", "f08"),),
                ModeValue="Nonzero",
            ),
            NativeField("Node", "fe8"),
            NativeField("Node", "ff0"),
        ),
        "moRefCylinder_c": (
            NativeField("Base", "moRefGeom_c"),
            NativeField("Embed", "f6f8", "mgPoint_c.restore"),
            NativeField("Embed", "f710", "mgVector_c.restore"),
            NativeField("Scalar", "f728", "f64"),
        ),
        "moFacetedData_c": KFacetFields,
    }
)
