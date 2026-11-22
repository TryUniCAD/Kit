from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# ordinary cold chamfers use local historical edge and surface identities from the inherited stock
KChmfRefFields = MappingProxyType(
    {
        "er.FUN_4bba41f0.FUN_4bbabca0": (
            NativeField("Base", "er.FUN_4bba8790"),
            NativeField("Base", "er.FUN_4bbabca0"),
        ),
        "er.FUN_4bba8790": (
            NativeField("Embed", "f10", "moEntityIdRep_c.FUN_4bba8de0"),
        ),
        "er.FUN_4bbaa6a0": (
            NativeField("Base", "er.FUN_4bba8790"),
            NativeField("Scalar", "f38", "i32"),
        ),
        "er.FUN_4bbabca0": (
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f3c", "i32"),
        ),
        "moBEntRef_c": (
            NativeField("Scalar", "f60", "u32"),
            NativeField("Scalar", "f64", "u32"),
            NativeField("Scalar", "f08", "u32"),
            NativeField("Scalar", "fe8", "i32"),
            NativeField("Scalar", "f70", "u32"),
            NativeField("Scalar", "f28", "f64"),
            NativeField("Scalar", "f30", "f64"),
            NativeField("Node", "f40", "moVertexRef_c"),
            NativeField(
                "Repeat",
                "f10",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(
                            NativeField(
                                "Fail",
                                "FUN_4bbac610 entity id restore with archive helper +0x48",
                            ),
                        ),
                        OtherValue=(NativeField("Base", "moEntityId_c"),),
                        ModeValue="Expression",
                        ExpressionValue=(
                            "bool",
                            (
                                "lookup_or",
                                ("context",),
                                ("literal", "ctx48"),
                                ("literal", 0),
                            ),
                        ),
                    ),
                ),
                CountValue="f08",
                ModeValue="SignedPositive",
            ),
            NativeField("Scalar", "f48", "u32"),
            NativeField(
                "Array",
                "fd0",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "t0", "u32"),
                    NativeField("Scalar", "t1", "u32"),
                ),
                CountValue="nd0",
                ModeValue="Positive",
            ),
            NativeField("Scalar", "fec", "i32"),
            NativeField("Scalar", "has_f18", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "chamfer alternate downstream edge owner"),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("lookup", ("scope",), ("literal", "has_f18")),
                    ("literal", 0),
                ),
            ),
        ),
        "moEndFaceSurfIdRep_c": (NativeField("Base", "er.FUN_4bba41f0.FUN_4bbabca0"),),
        "moEntityIdRep_c.FUN_4bba8de0": (
            NativeField("Node", "f08"),
            NativeField("Node", "f10", "moFR_c"),
        ),
        "moFromSktEntSurfIdRep_c": (NativeField("Base", "er.FUN_4bbaa6a0"),),
        "moEntityId_c": (NativeField("Node", "f08"),),
        "moFR_c": (
            NativeField("Node", "f08", "moExtObject_c"),
            NativeField("Embed", "f10", "moFRData_c"),
        ),
        "su_CDWordArray": KContainerFields["su_CDWordArray"],
    }
)
