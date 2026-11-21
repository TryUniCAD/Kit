from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# keyed property lists keep the integer owner separate from the concrete archived object
KPropKeyRows = (NativeField("Scalar", "key", "i32"), NativeField("Node", "o"))

# ordinary version 19000 property managers serialize their keyed owners and transitive lists in field order
KManagerFields = MappingProxyType(
    {
        "suObList": KContainerFields["suObList"],
        "moCusPropMgr_c": (
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f08", "i32"),
            NativeField(
                "Array",
                "f20",
                "u32",
                CountValue="n20",
                BodyValue=KPropKeyRows,
            ),
            NativeField("Scalar", "f54", "u8"),
        ),
        "moCusPropContainer_c": (
            NativeField("Node", "f08"),
            NativeField("Node", "f10"),
            NativeField("Node", "f18"),
            NativeField("Scalar", "f20", "i32"),
        ),
        "moFilePropContainer_c": (
            NativeField("Node", "f08"),
            NativeField("Node", "f10"),
        ),
        "moCutListPropContainer_c": (
            NativeField(
                "Array", "f08", "u32", CountValue="n08", BodyValue=KPropKeyRows
            ),
            NativeField(
                "Array", "f38", "u32", CountValue="n38", BodyValue=KPropKeyRows
            ),
        ),
        "moAdvCusPropList_c": KContainerFields["suObList"],
        "moCusPropStringElem_c": (NativeField("Text", "f08"),),
        "moAdvCusProp_c": (
            NativeField("Embed", "f10", "suObList"),
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Text", "f58"),
            NativeField("Scalar", "f7c", "i32"),
            NativeField("Text", "f60"),
            NativeField("Text", "f70"),
            NativeField("Scalar", "f78", "i32"),
            NativeField("Scalar", "f80", "i32"),
            NativeField("Scalar", "f84", "i32"),
        ),
    }
)

# each tagged object in the measured property archive uses its own schema one descriptor
KManagerSchemas = MappingProxyType({ClassName: (1,) for ClassName in KManagerFields})
