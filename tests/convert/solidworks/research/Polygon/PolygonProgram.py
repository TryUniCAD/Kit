from __future__ import annotations

from tests.convert.solidworks.research.Polygon.PolygonPaths import KPaths
from tests.convert.solidworks.research.Polygon.PolygonLoad import KLoad
from tests.convert.solidworks.research.Polygon.PolygonInput import KInput
from tests.convert.solidworks.research.Polygon.PolygonSketch import KSketch
from tests.convert.solidworks.research.Polygon.PolygonOrigin import KOrigin
from tests.convert.solidworks.research.Polygon.PolygonOriginCodec import KOriginCodec
from tests.convert.solidworks.research.Polygon.PolygonOriginReport import KOriginReport
from tests.convert.solidworks.research.Polygon.PolygonFeature import KFeature
from tests.convert.solidworks.research.Polygon.PolygonEncode import KEncode
from tests.convert.solidworks.research.Polygon.PolygonDecode import KDecode
from tests.convert.solidworks.research.Polygon.PolygonReferences import KRefs
from tests.convert.solidworks.research.Polygon.PolygonEdit import KEdit
from tests.convert.solidworks.research.Polygon.PolygonReport import KReport
from tests.convert.solidworks.research.Polygon.PolygonWidths import KWidths

# focused stages need one interpreter without obscuring their boundary order
KProgram = (
    KPaths
    + KLoad
    + KInput
    + KSketch
    + KOrigin
    + KOriginCodec
    + KOriginReport
    + KFeature
    + KEncode
    + KDecode
    + KRefs
    + KEdit
    + KReport
    + KWidths
)
