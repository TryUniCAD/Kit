from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import (
    KAnchorFields,
)

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigLayouts import (
    KConfigLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AssemblyFields import (
    KAssemblyFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.BodyFields import (
    KBodyFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ComponentFields import (
    KComponentFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.CoreFields import (
    KCoreFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.DimensionFields import (
    KDimensionFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.FolderFields import (
    KFolderFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.MaterialFields import (
    KMaterialFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ProfileFields import (
    KProfileFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ReferenceFields import (
    KReferenceFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.RevolveFields import (
    KRevolveFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.SketchFields import (
    KSketchFields,
)

# resolved field owners share the same typed serialization kernel and existing configuration definitions
KResolvedLayouts = MappingProxyType(
    {
        **KConfigLayouts,
        **KAnchorFields,
        **KAssemblyFields,
        **KBodyFields,
        **KComponentFields,
        **KCoreFields,
        **KDimensionFields,
        **KFeatureFields,
        **KFolderFields,
        **KGeometryFields,
        **KMaterialFields,
        **KProfileFields,
        **KReferenceFields,
        **KRevolveFields,
        **KSketchFields,
    }
)
