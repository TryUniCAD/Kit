from types import MappingProxyType
from typing import TypeAlias

from convert.adapters.solidworks.Archive.Scalars.ScalarWords import KScalarWords

# header field rules provide the same wire order to both archive directions
KHeaderLayout: TypeAlias = tuple[tuple[str, str], ...]

# the current header graph has a single qualified model archive version
KHeaderVersion = 19000

# header layout names retain their original scalar signedness in the shared vocabulary
KHeaderScalars = MappingProxyType({"B": "u8", "H": "u16", "I": "u32", "i": "i32"})

# header bounds and fields share the same scalar widths as every native archive owner
KHeaderWords = MappingProxyType(
    {WireName: KScalarWords[KindName] for WireName, KindName in KHeaderScalars.items()}
)

# native metadata separates external identities and bounds from scalar words
KHeaderFields: KHeaderLayout = (
    ("fec", "i"),
    ("f10", "su_CStringArray"),
    ("f18", "su_CStringArray"),
    ("f20", "suObList"),
    ("f50", "I"),
    ("f08", "i"),
    ("f30", "moExtObjectList_c"),
    ("f40", "I"),
    ("f38", "moExtObject_c"),
    ("f44", "I"),
    ("f58", "i"),
    ("f68", "i"),
    ("f70", "I"),
    ("f60", "i"),
    ("f78", "i"),
    ("fc0", "i"),
    ("f28", "null"),
    ("fc4", "i"),
    ("f7c", "I"),
    ("f48", "I"),
    ("f88", "suObList"),
    ("fc8", "i"),
    ("f64", "i"),
    ("bbox", "bounds"),
    ("fcc", "i"),
    ("fd0", "i"),
    ("fd4", "i"),
    ("f80", "I"),
    ("f9c", "i"),
    ("fa0", "i"),
    ("fa4", "i"),
    ("fa8", "i"),
    ("fac", "i"),
    ("fb0", "i"),
    ("fe8", "i"),
    ("ff0", "i"),
    ("ff4", "i"),
    ("ff8", "i"),
    ("ffc", "i"),
    ("f100", "i"),
    ("f104", "i"),
    ("f108", "i"),
    ("f10c", "i"),
    ("f98", "i"),
)

# external identities share handles before their placement specific fields
KSharedFields: KHeaderLayout = (
    ("h18", "moCStringHandle_c"),
    ("h10", "moCStringHandle_c"),
    ("f20", "H"),
    ("f08", "B"),
    ("f28", "I"),
    ("f38", "text"),
    ("f40", "text"),
    ("f50", "text"),
    ("f35", "B"),
)

# file provenance precedes the selected configuration body
KExtLeadFields: KHeaderLayout = (
    ("f58", "B"),
    ("f60", "I"),
    ("f48", "i"),
    ("f4c", "i"),
    ("f78", "i"),
)

# the selected configuration preserves its own name and identifier
KRefCfgFields: KHeaderLayout = (("f08", "text"), ("f10", "i"))

# the native external file suffix keeps both time and state values
KExtTailFields: KHeaderLayout = (("f54", "i"), ("f70", "I"), ("f50", "i"))

# the feature log owns an identifier and a name after its stamp list
KLogFields: KHeaderLayout = (("f48", "i"), ("f50", "text"))

# revision stamps retain separate operation and provenance values
KStampFields: KHeaderLayout = (
    ("f08", "H"),
    ("f0c", "H"),
    ("f10", "H"),
    ("f18", "I"),
    ("f20", "text"),
)
