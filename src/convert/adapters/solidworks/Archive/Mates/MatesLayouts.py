from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Assemblies.AsmFileFields import (
    KExternalFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.PlanarRefFields import (
    KPlanarRefFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import (
    KResolvedLayouts,
)
from convert.adapters.solidworks.Archive.Mates.CylinderFields import KCylinderFields
from convert.adapters.solidworks.Archive.Mates.MateFields import KMateFields
from convert.adapters.solidworks.Archive.Mates.PlaneFields import KPlaneFields
from convert.adapters.solidworks.Archive.Mates.WrapperFields import KWrapperFields

# mate streams extend existing body owners without widening ordinary resolved graph admission
KMatesLayouts = MappingProxyType(
    {
        **KResolvedLayouts,
        **KExternalFields,
        **KPlanarRefFields,
        **KMateFields,
        **KPlaneFields,
        **KWrapperFields,
        **KCylinderFields,
    }
)
