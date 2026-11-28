from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import (
    KRefWrapperTailFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# finite intersection axes need their actual curve interval and two independent plane wrappers
KAxisFields = MappingProxyType(
    {
        "moRefAxis_c": (
            NativeField("Base", "moRefGeom_c"),
            NativeField("Node", "f700", "moPlaneInterAxisData_c"),
        ),
        "moPlaneInterAxisData_c": (
            NativeField("Embed", "f18", "mgPoint_c.restore"),
            NativeField("Embed", "f30", "mgPoint_c.restore"),
            NativeField("Scalar", "f08", "f64"),
            NativeField("Scalar", "f10", "f64"),
            NativeField("Embed", "f50", "mgVector_c.restore"),
            NativeField("Embed", "f68", "mgPoint_c.restore"),
            NativeField("Node", "f80", "moPlaneRef_w"),
            NativeField("Node", "f88", "moPlaneRef_w"),
        ),
        "moPlaneRef_w": (
            NativeField("Node", "f58", "moCompRefPlane_c"),
            *KRefWrapperTailFields,
            *(
                NativeField("Scalar", FieldName, "f64")
                for FieldName in ("fb0", "fb8", "fc0", "fc8")
            ),
            NativeField("Embed", "fd0", "mgPoint_c.restore"),
            NativeField("Embed", "fe8", "mgVector_c.restore"),
            NativeField("Embed", "f100", "mgXform_c.restore"),
            NativeField("Embed", "f188", "mgPoint_c.restore"),
        ),
    }
)
