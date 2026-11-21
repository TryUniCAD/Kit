from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the two physical cache intervals belong to distinct fields on the native part
KPartCacheRules = MappingProxyType(
    {
        "mass": (NativeField("MassCaches", "f1628", OtherName="f1638"),),
        "bounds": (NativeField("BBoxCache", "f1640"),),
    }
)
