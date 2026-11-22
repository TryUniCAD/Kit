from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.HeaderBodyFields import (
    MakeBodyFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KExtLeadFields,
    KExtTailFields,
    KRefCfgFields,
    KSharedFields,
)

# file identity owners reuse header vocabulary while retaining their native body field names
KExternalFields = MappingProxyType(
    {
        "moCStringHandle_c": (NativeField("Text", "f08"),),
        "moReferencedConfiguration_c": MakeBodyFields(KRefCfgFields),
        "moSharedFileDef_c": MakeBodyFields(KSharedFields),
        "moExtObject_c": (
            NativeField("Embed", "shared", "moSharedFileDef_c"),
            *MakeBodyFields(KExtLeadFields),
            NativeField("Embed", "refcfg", "moReferencedConfiguration_c"),
            *MakeBodyFields(KExtTailFields),
        ),
    }
)
