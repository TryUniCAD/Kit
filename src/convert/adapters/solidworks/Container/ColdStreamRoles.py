from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KComponentTreeStream,
    KConfigStream,
    KeywordsStream,
    KResolvedFeaturesStream,
)

# the measured cold graph has the same typed archive roles on both members
KColdBaseStreams = frozenset(
    {
        "Header2",
        "Contents/CMgr",
        KConfigStream + "-ModelHeader",
        KConfigStream,
        KResolvedFeaturesStream,
        "Contents/Definition",
        "_MO_VERSION_19000/Biography",
        "_MO_VERSION_19000/History",
        KeywordsStream,
    }
)

# the physical parent owns the occurrence index and separate ordered mate list
KColdParentStreams = KColdBaseStreams | {
    KComponentTreeStream,
    KConfigStream + "-MatesList",
}

# the independently linked part has its own separately rooted configuration directory
KColdChildStreams = KColdBaseStreams | {"Contents/CMgrHdr2"}


# duplicate directory names must never impersonate a complete cold stream inventory
def HasColdStreams(Archive: SldprtArchive, Expected: frozenset[str]) -> bool:
    NamesValue = tuple(Record.name for Record in Archive.records)
    return len(NamesValue) == len(Expected) and frozenset(NamesValue) == Expected
