from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the unit component base resolves its actual owning object through the archive map
KReferenceFields = MappingProxyType({"moComponent_c": (NativeField("Node", "owner"),)})
