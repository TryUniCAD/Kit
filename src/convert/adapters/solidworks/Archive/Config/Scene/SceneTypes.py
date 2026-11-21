from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the part environment field must open its own concrete schema one folder
KEnvFolderClass = RuntimeClass("moEnvFolder_c", 1)

# both scene roots inherit a real named object from the ordinary feature base
KNodeNameClass = RuntimeClass("moNodeName_c", 1)

# the ambient record has a concrete owner independent of the directional suffix
KAmbientClass = RuntimeClass("moAmbientLight_c", 1)

# a directional light owns the separate vector and final scalar fields
KDirectionClass = RuntimeClass("moDirectionLight_c", 1)

# the body executor needs the concrete scene children without exposing them as member roots
KSceneSchemas = MappingProxyType(
    {KAmbientClass.NameValue: (1,), KDirectionClass.NameValue: (1,)}
)

# scene traversal opens light children once and extends only to their name objects
KSceneChildTypes = MappingProxyType(
    {
        2: frozenset((KNodeNameClass, KAmbientClass, KDirectionClass)),
        3: frozenset((KNodeNameClass,)),
    }
)
