from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)


# the fresh periodic part authors one explicit ambient from its writer creation event
def MakeImportLight(WrittenAt: int) -> LightInput:
    return LightInput(
        "ambient",
        "Import ambient",
        "KitImportAmbient",
        0.5,
        0.5,
        0.0,
        0x00FFFFFF,
        True,
        False,
        True,
        1.0,
        True,
        16.0,
        None,
        None,
        FeatureInstant(WrittenAt, 0),
    )
