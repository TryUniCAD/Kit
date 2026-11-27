from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Mates.SurfaceTail import KSurfaceTail
from convert.adapters.solidworks.Archive.Mates.WrapperTail import KWrapperTail

# plane endpoint wrappers retain actual component references and their independent native bookkeeping
KWrapperFields = MappingProxyType(
    {
        "moRefWrapper_c": (
            NativeField("Node", "f58", "moCompRefPlane_c"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail",
                        "ordinary mate endpoint requires a component plane reference",
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("class_of", ("lookup", ("scope",), ("literal", "f58"))),
                    ("literal", "moCompRefPlane_c"),
                ),
            ),
            *KWrapperTail,
        ),
        "moSurfaceRef_w": (
            NativeField("Base", "moRefWrapper_c"),
            *KSurfaceTail,
        ),
        "moPlaneRef_w": (
            NativeField("Base", "moSurfaceRef_w"),
            NativeField("Embed", "fd0", "mgPoint_c.restore"),
            NativeField("Embed", "fe8", "mgVector_c.restore"),
            NativeField("Embed", "f100", "mgXform_c.restore"),
            NativeField("Embed", "f188", "mgPoint_c.restore"),
        ),
    }
)
