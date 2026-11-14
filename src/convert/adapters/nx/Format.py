from __future__ import annotations as Annotations
from types import MappingProxyType

from convert.adapters.base.AdapterInfo import AdapterInfo
from interchange.enums.EnumDocument import Capability

# the nx format id names the native siemens part dialect
KFormatId = "siemens.nx"

# the nx part suffix is shared by native parts and assemblies
KPartSuffix = ".prt"

# the adapter advertises only capabilities the native reader actually retains
KCapabilities = frozenset(
    {
        Capability.KBrep,
        Capability.KConfigurations,
        Capability.KBodyStructure,
        Capability.KNativePayloads,
        Capability.KRoundtripMeta,
        Capability.KExternalRefs,
    }
)

# the adapter metadata drives registry discovery and destination selection
KInfoValue = AdapterInfo(
    format_id=KFormatId,
    name="Siemens NX",
    version="2506",
    extensions=(KPartSuffix,),
    aliases=("nx", "ug"),
    capabilities=KCapabilities,
    media_types=("application/x-siemens-nx-part",),
    part_extensions=(KPartSuffix,),
    assembly_extensions=(KPartSuffix,),
)

# the suffix map keeps destination validation independent from adapter state
KDocTypeBySuffix = MappingProxyType({KPartSuffix: KFormatId})

# the public info binding keeps the established adapter metadata name
INFO = KInfoValue

# the public suffix binding keeps the established adapter metadata name
DOCUMENT_TYPE_BY_SUFFIX = KDocTypeBySuffix

# the public annotations binding keeps the established adapter metadata name
annotations = Annotations
