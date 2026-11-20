from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# an ordinary unit component needs the exact enclosing part for its owner backlink
KReferenceFields = MappingProxyType(
    {"moComponent_c": (NativeField("Node", "owner", ModeValue="FrameOwner"),)}
)
