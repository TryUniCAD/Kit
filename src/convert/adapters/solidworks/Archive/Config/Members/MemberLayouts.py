from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConceptFields import (
    KConceptFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Members.FeatColorFields import (
    KFeatColorFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.LightFields import (
    KLightFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.OwnerFields import (
    KOwnerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RecordFields import (
    KRecordFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RelMgrFields import (
    KRelMgrFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Members.ThreadFields import (
    KThreadFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Members.ViewFields import (
    KViewFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import (
    KGeometryFields as KVectorFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ObListFields import (
    KObListFields,
)
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KFeatColorClass,
)

# the bounded member bodies reuse the native object list grammar
KMemberLayouts = MappingProxyType(
    {
        "suObList": KObListFields,
        KFeatColorClass.NameValue: KFeatColorFields,
        **KRelMgrFields,
        **KFeatureFields,
        **KConceptFields,
        **KOwnerFields,
        **KRecordFields,
        **KThreadFields,
        **KLightFields,
        **KVectorFields,
        **KGeometryFields,
        **KViewFields,
    }
)
