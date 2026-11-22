from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KComponentTreeStream,
    KConfigStream,
    KeywordsStream,
    KResolvedFeaturesStream,
)

# the measured cold group uses three concrete ordered archive classes
KColdMateClasses = ("moMateParallel", "moMateDistanceDim_c", "moMateCoincident")

# the cold inspection scope stays distinct from the measured pair write inverse
KColdMateScope = "cold_parallel_distance_coincident"

# both cold members need the documented ordinary role inventory without saved companion state
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

# the cold assembly adds its occurrence index and actual selected mate list
KColdParentStreams = KColdBaseStreams | {
    KComponentTreeStream,
    KConfigStream + "-MatesList",
}

# the linked cold child carries its separately rooted active configuration directory
KColdChildStreams = KColdBaseStreams | {"Contents/CMgrHdr2"}


# scope follows actual stream roles and cannot absorb native save state
def HasColdStreams(Archive: SldprtArchive, Expected: frozenset[str]) -> bool:
    NamesValue = tuple(Record.name for Record in Archive.records)
    return len(NamesValue) == len(Expected) and frozenset(NamesValue) == Expected
