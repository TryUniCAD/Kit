from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.AssemblyDefTail import (
    KAssemblyDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocHeadFields import (
    KDocHeadPrefix,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocTailFields import (
    KDocTailFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ModelDefSchemas import (
    KOrdDefSchemas,
)
from convert.adapters.solidworks.Archive.Definition.Fields.OrdDefLayouts import (
    KOrdDefLayouts,
    KOrdDefRenderer,
)

# the assembly root extends the same ui layouts with its own inline tail
KAsmDefLayouts = MappingProxyType(
    {
        **KOrdDefLayouts,
        **KAssemblyDefTail,
        "uiAssemblyDoc_c": (
            *KDocHeadPrefix,
            KOrdDefRenderer,
            *KDocTailFields,
            NativeField("Base", "uiAssemblyDoc_c.Serialize.own"),
        ),
    }
)

# only the assembly root schema differs from the ordinary part object vocabulary
KAsmDefSchemas = MappingProxyType({**KOrdDefSchemas, "uiAssemblyDoc_c": (1,)})
