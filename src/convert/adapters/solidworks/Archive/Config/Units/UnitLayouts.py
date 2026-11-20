from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.UnitFields import (
    KUnitFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)

# the unit table shares its stored object array layout with other archive owners
KUnitLayouts = MappingProxyType({**KContainerFields, **KUnitFields})
