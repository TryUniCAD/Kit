from __future__ import annotations

from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KPrimaryStreams

# complete stream selection keeps field correlation separate from partial parser success
KInventoryCases = (
    *((StreamName, False) for StreamName in KPrimaryStreams),
    ("Contents/Config-0-ResolvedFeatures", True),
)
