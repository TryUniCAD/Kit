from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConceptFields import (
    KConceptFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FeatColorFields import (
    KFeatColorFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.OwnerFields import (
    KOwnerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RelMgrFields import (
    KRelMgrFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
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
    }
)
