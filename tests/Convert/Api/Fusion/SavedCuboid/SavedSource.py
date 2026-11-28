from pathlib import Path as FilePath

from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase


# explicit fixture resolution keeps the complete suite independent of local research scratch paths
def SavedSource(CaseValue: SavedCase) -> FilePath:
    return (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/SavedCuboidRoundTrip/Corpus"
        / CaseValue.FileName
    )
