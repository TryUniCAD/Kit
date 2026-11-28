from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current saved shell fields separate the removed caps and the auxiliary edge
KShellFields = MappingProxyType(
    {
        "moShell_c": (
            NativeField("Base", "moBodyFeature_c"),
            NativeField("Node", "f828", "suObList"),
            NativeField("Node", "f818", "moDisplayDim_c"),
            NativeField("Scalar", "f820", "u8"),
            NativeField("Node", "f830", "suObList"),
            NativeField("Node", "f838", "suObList"),
            NativeField("Node", "f848", "moCompEdge_c"),
            NativeField("Node", "f850", "moCompSolidBody_c"),
        ),
    }
)
