from __future__ import annotations

from types import MappingProxyType

from convert.adapters.base.AdapterInfo import AdapterInfo
from interchange.enums.EnumDocument import Capability

# the registry keys adapters by this stable identifier
KFormatId = "creo.prt"


# only prt files reach this adapter
KSuffixes = (".prt",)


# callers say proe as often as creo so both resolve
KAliases = ("prt", "creo", "proe")


# the loader needs these section names to validate a part
KSectionNames = (
    "AllFeatur",
    "BasicData",
    "BasicText",
    "BasBasData",
    "BasFullData",
    "DEPDB_DATA",
    "FeatDefs",
    "FeatDefsDtm",
    "FeatDefsIndex",
    "FullMData",
    "GeomDepen",
    "Geomlists",
    "MdlRefInfo",
    "MdlStatus",
    "NovisGeom",
    "SolidPersistTable",
    "SolidPrimdata",
    "THMB_IMG_MAIN",
    "UnitSystemDef",
    "VisibGeom",
)


# the registry compares adapter info so it must be stable
KInfoValue = AdapterInfo(
    format_id=KFormatId,
    name="PTC Creo Parametric",
    version="PSB",
    aliases=KAliases,
    extensions=KSuffixes,
    capabilities=frozenset(
        {
            Capability.KConfigurations,
            Capability.KNativePayloads,
            Capability.KProvenance,
            Capability.KRoundtripMeta,
        }
    ),
    native_capabilities=frozenset({Capability.KRoundtripMeta}),
    media_types=("application/x-ptc-creo-part",),
    part_extensions=KSuffixes,
)


# the format record is shared so it is frozen at import
KFormatInfo = MappingProxyType({"info": KInfoValue, "format_id": KFormatId})
