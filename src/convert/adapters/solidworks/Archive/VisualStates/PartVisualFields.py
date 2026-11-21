from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.ConfigurationFields import (
    KConfigurationFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.VisualStates.VisualFields import (
    KVisualFields,
    KVisualSchemas,
)

# the part self scope admits only the inherited holder and constructor material bodies
KPartVisualFields = MappingProxyType(
    {
        **KVisualFields,
        "moCompHolder_c": (NativeField("Base", "moCompRef_c"),),
        **{
            NameValue: KConfigurationFields[NameValue]
            for NameValue in (
                "moVisualProperties_c",
                "moVisualProperties_c.restore",
                "uoMaterialProperties.restore",
                "moUserProperty_c.restore",
            )
        },
    }
)

# the additional allocation roles are specific to the standalone part state
KPartVisualSchemas = MappingProxyType(
    {**KVisualSchemas, "moCompHolder_c": (1,), "moVisualProperties_c": (1,)}
)
