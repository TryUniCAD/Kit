from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the part hatch is a concrete lightweight owner with no child bodies
KHatchClass = RuntimeClass("gcXhatch_c", 1)

# the optional part material record owns a separate density parameter
KMaterialClass = RuntimeClass("moMaterial_c", 1)

# density values belong to this concrete parameter rather than to appearance data
KDensityClass = RuntimeClass("moDensityParameter_c", 1)

# model data keeps a separately scoped scene link
KModelDataClass = RuntimeClass("uoModelData_c", 1)

# every reachable tagged body must have its exact current descriptor
KPartMatSchemas = MappingProxyType(
    {
        OwnerValue.NameValue: (OwnerValue.SchemaValue,)
        for OwnerValue in (KHatchClass, KMaterialClass, KDensityClass, KModelDataClass)
    }
)
