from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.AssemblyFields import (
    KAssemblyFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ConfigurationFields import (
    KConfigurationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ExternalFields import (
    KExternalFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.MaterialFields import (
    KMaterialFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.PropertyFields import (
    KPropertyFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ReferenceFields import (
    KReferenceFields,
)

# the admitted body registry composes native owner grammars rather than individual document programs
KBodyLayouts = MappingProxyType(
    {
        **KAssemblyFields,
        **KConfigurationFields,
        **KContainerFields,
        **KExternalFields,
        **KFeatureFields,
        **KGeometryFields,
        **KMaterialFields,
        **KPropertyFields,
        **KReferenceFields,
    }
)
