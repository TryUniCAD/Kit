from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the saved box stock keeps its chooser records and resolved contour wire
KStockSaveFields = MappingProxyType(
    {
        "moSketchRegion_c": (NativeField("Node", "f08", "suObList"),),
        "moBodyChooser_c": (
            NativeField("Embed", "f48", "rf.suObArray"),
            NativeField("Node", "f68", "moAtomFeature_c"),
        ),
        "moPerBodyChooserData_c": (
            NativeField("Embed", "f08", "rf.suObArray"),
            NativeField("Embed", "f28", "rf.suObArray"),
            NativeField("Embed", "f48", "rf.suObArray"),
            NativeField("Scalar", "f68", "i32"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Embed", "f78", "su_CDWordArray"),
            NativeField("Scalar", "f70", "i32"),
        ),
        "moBBoxCenterData_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Embed", "f10", "mgPoint_c.restore"),
            NativeField("Scalar", "f28", "f64"),
        ),
        "moSketchChain_c": (
            NativeField("Embed", "f08", "su_CDWordArray"),
            NativeField("Embed", "f60", "su_CDWordArray"),
            NativeField("Scalar", "f28", "u32"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f50", "i32"),
            NativeField("Scalar", "f54", "i32"),
            NativeField("Scalar", "f58", "u32"),
            NativeField("Scalar", "f5c", "u32"),
            NativeField("Text", "f80"),
            NativeField("Scalar", "flags", "u16"),
            NativeField(
                "Branch",
                "flags",
                BodyValue=(NativeField("Fail", "alternate saved stock sketch wire"),),
                ModeValue="Nonzero",
            ),
            NativeField("Scalar", "fd0", "u32"),
            NativeField(
                "Array",
                "end_map",
                "i32",
                BodyValue=(NativeField("Fail", "alternate saved stock end map"),),
                CountValue="nmap",
                ModeValue="Positive",
            ),
            NativeField("Node", "fc0", "contourTrimData_c"),
            NativeField("Node", "fc8", "contourTrimData_c"),
            NativeField("Scalar", "f90", "i32"),
            NativeField("Scalar", "fa0", "i32"),
            NativeField("Scalar", "fa4", "i32"),
        ),
    }
)
