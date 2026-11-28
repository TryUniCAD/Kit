from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# detail folders own ordered native collections even when the authored drawing contains no annotations
KDetailFields = MappingProxyType(
    {
        "moDetailFolder_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Embed", "f358", "rf.suObList"),
            NativeField("Embed", "f3a0", "rf.suObList"),
            NativeField("Embed", "f3e8", "rf.suObList"),
            NativeField("Embed", "f430", "rf.suObList"),
            NativeField("Embed", "f4c0", "rf.suObList"),
            NativeField("Embed", "f550", "rf.suObList"),
            NativeField("Embed", "f598", "rf.suObList"),
            NativeField("Embed", "f5e0", "rf.suObList"),
            NativeField("Embed", "f628", "rf.suObList"),
            NativeField("Embed", "f670", "rf.suObList"),
            NativeField("Embed", "f700", "rf.suObList"),
            NativeField("Embed", "f748", "rf.suObList"),
            NativeField("Embed", "f7d8", "rf.suObList"),
            NativeField("Embed", "f820", "rf.suObList"),
            NativeField("Embed", "f868", "rf.suObList"),
            NativeField("Embed", "f8b0", "rf.suObList"),
            NativeField("Embed", "f8f8", "rf.suObList"),
            NativeField("Embed", "f478", "rf.suObList"),
            NativeField("Embed", "fd90", "mgXform_c.restore"),
            NativeField("Node", "fd78"),
            NativeField("Embed", "f940", "rf.suObList"),
            NativeField("Embed", "f988", "rf.suObList"),
            NativeField("Embed", "f9d0", "rf.suObList"),
            NativeField("Embed", "fa18", "rf.suObList"),
            NativeField("Embed", "faa8", "rf.suObList"),
            NativeField("Embed", "faf0", "rf.suObList"),
            NativeField("Embed", "fb38", "rf.suObList"),
            NativeField("Embed", "f508", "rf.suObList"),
            NativeField("Embed", "fbc8", "rf.suObList"),
            NativeField("Embed", "f790", "rf.suObList"),
            NativeField("Embed", "fc10", "rf.suObList"),
            NativeField("Embed", "fc58", "rf.suObList"),
            NativeField("Embed", "fca0", "rf.suObList"),
            NativeField("Embed", "fce8", "rf.suObList"),
            NativeField("Scalar", "has_fd98", "i32"),
            NativeField("Embed", "fb80", "rf.suObList"),
            NativeField("Embed", "fd30", "rf.suObList"),
            NativeField("Scalar", "fde8", "i32"),
        ),
    }
)
