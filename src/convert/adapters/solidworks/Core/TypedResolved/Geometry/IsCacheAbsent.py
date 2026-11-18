from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import HasPayload
from convert.adapters.solidworks.Container.Format import (
    KResolvedFeaturesStream,
    KeywordsStream,
)

# reconstruction must never replace a present geometry stream or an unrecognized source role
KPrismStreams = frozenset(
    (
        "Header2",
        "Contents/Config-0-ModelHeader",
        "Contents/Config-0",
        "Contents/CMgr",
        "Contents/CMgrHdr2",
        KResolvedFeaturesStream,
        "Contents/Definition",
        "_MO_VERSION_19000/Biography",
        "_MO_VERSION_19000/History",
        KeywordsStream,
        "docProps/core.xml",
        "docProps/custom.xml",
        "docProps/ISolidWorksInformation.xml",
    )
)


# only physical absence permits analytic reconstruction without hiding corrupt or unsupported cached geometry
def IsCacheAbsent(Archive: SldprtArchive) -> bool:
    NamesValue = tuple(Record.name for Record in Archive.records)
    return (
        Archive.format_version == 4
        and len(set(NamesValue)) == len(NamesValue)
        and set(NamesValue).issubset(KPrismStreams)
        and not any(HasPayload(Record.data) for Record in Archive.records)
    )
