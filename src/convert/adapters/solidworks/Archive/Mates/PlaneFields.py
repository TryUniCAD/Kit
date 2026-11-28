from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# detached plane endpoints reuse the independently mapped plane data body without default plane extensions
KPlaneFields = MappingProxyType(
    {
        "moAbsoluteRefPlnData_c": (
            NativeField("Base", "moRefPlnData_c.serializePlaneData"),
        ),
    }
)
