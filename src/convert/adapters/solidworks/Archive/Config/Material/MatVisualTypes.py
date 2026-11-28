from types import MappingProxyType

from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import KNodeNameClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the currently observed visual owner has its own concrete schema
KMatVisualClass = RuntimeClass("moVisualProperties_c", 1)

# the lightweight prefix owns only the part and its two measured children
KMatVisualSchemas = MappingProxyType(
    {
        ClassValue.NameValue: (ClassValue.SchemaValue,)
        for ClassValue in (KPartRoot, KNodeNameClass, KMatVisualClass)
    }
)
