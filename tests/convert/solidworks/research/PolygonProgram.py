from __future__ import annotations

from tests.convert.solidworks.research.PolygonPaths import KPaths
from tests.convert.solidworks.research.PolygonLoad import KLoad
from tests.convert.solidworks.research.PolygonInput import KInput
from tests.convert.solidworks.research.PolygonSketch import KSketch
from tests.convert.solidworks.research.PolygonFeature import KFeature
from tests.convert.solidworks.research.PolygonEncode import KEncode
from tests.convert.solidworks.research.PolygonDecode import KDecode
from tests.convert.solidworks.research.PolygonReferences import KRefs
from tests.convert.solidworks.research.PolygonEdit import KEdit
from tests.convert.solidworks.research.PolygonReport import KReport

KProgram = (
    KPaths
    + KLoad
    + KInput
    + KSketch
    + KFeature
    + KEncode
    + KDecode
    + KRefs
    + KEdit
    + KReport
)
