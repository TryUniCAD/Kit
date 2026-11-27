from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.AssemblyDefTail import (
    KAssemblyDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocHeadFields import (
    KDocHeadFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocTailFields import (
    KDocTailFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefLayouts import (
    KModelDefLayouts,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefSchemas import (
    KModelDefSchemas,
)

# the assembly root extends the same ui layouts with its own inline tail
KAsmDefLayouts = MappingProxyType(
    {
        **KModelDefLayouts,
        **KAssemblyDefTail,
        "uiAssemblyDoc_c": (
            *KDocHeadFields,
            *KDocTailFields,
            NativeField("Base", "uiAssemblyDoc_c.Serialize.own"),
        ),
    }
)

# only the assembly root schema differs from the ordinary part object vocabulary
KAsmDefSchemas = MappingProxyType({**KModelDefSchemas, "uiAssemblyDoc_c": (1,)})
