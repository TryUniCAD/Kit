from types import MappingProxyType

from convert.adapters.solidworks.Archive.Cmgr.Layouts.BaseConfigFields import (
    KBaseConfigFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.ConfigMgrFields import (
    KConfigMgrFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.CustomPropListFields import (
    KCustomPropListFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.PartCfgObjectFields import (
    KPartCfgObjectFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.PartConfigFields import (
    KPartConfigFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.StringIntFields import (
    KStringIntFields,
)

# manager class layouts must share one registry across read and write contexts
KManagerRecordRules = MappingProxyType(
    {
        "moBaseConfiguration_c": KBaseConfigFields,
        "moConfigurationMgr_c": KConfigMgrFields,
        "moCustomPropertyList": KCustomPropListFields,
        "moPartConfigObject_c": KPartCfgObjectFields,
        "moPartConfiguration_c": KPartConfigFields,
        "su_CMapStringToInt": KStringIntFields,
    }
)
