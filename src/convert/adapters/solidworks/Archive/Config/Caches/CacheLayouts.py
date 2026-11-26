from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MassCacheFields import (
    KMassCacheFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.MassPropFields import (
    KMassPropFields,
)

# both bounded records and model traversal use the same embedded cache schemas
KCacheLayouts = MappingProxyType(
    {
        "moMassPropCache_c.Serialize": KMassCacheFields,
        "moMassProp_c": KMassPropFields,
        **KGeometryFields,
    }
)
