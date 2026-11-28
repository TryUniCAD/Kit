from __future__ import annotations

from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import (
    KCurveCorpus,
    KPrimaryStreams,
)


# child argument values are rebuilt from known source families and fixed fixture leaves
def FieldArguments(TmpPath: FilePath, Pattern: str, StreamName: str) -> tuple[str, str]:
    CorpusPattern = KCurveCorpus / "*.SLDPRT"
    if Pattern == str(CorpusPattern):
        PatternPath = CorpusPattern
    elif Pattern == str(TmpPath / "Unmatched" / "*.SLDPRT"):
        PatternPath = ArtifactFile(TmpPath, "Unmatched") / "*.SLDPRT"
    elif Pattern == str(TmpPath / "Truncated.SLDPRT"):
        PatternPath = ArtifactFile(TmpPath, "Truncated.SLDPRT")
    else:
        raise ValueError("unknown field inventory source pattern")
    for NameValue in (*KPrimaryStreams, "Contents/FieldInventoryMissing"):
        if NameValue == StreamName:
            return str(PatternPath), NameValue
    raise ValueError("unknown field inventory stream")
