from __future__ import annotations

from tests.Convert.Solidworks.Research.Polygon.PolygonPaths import KPaths
from tests.Convert.Solidworks.Research.Polygon.PolygonLoad import KLoad
from tests.Convert.Solidworks.Research.Polygon.PolygonInput import KInput
from tests.Convert.Solidworks.Research.Polygon.PolygonSketch import KSketch
from tests.Convert.Solidworks.Research.Polygon.PolygonOrigin import KOrigin
from tests.Convert.Solidworks.Research.Polygon.PolygonOriginCodec import KOriginCodec
from tests.Convert.Solidworks.Research.Polygon.PolygonOriginReport import KOriginReport
from tests.Convert.Solidworks.Research.Polygon.PolygonFeature import KFeature
from tests.Convert.Solidworks.Research.Polygon.PolygonEncode import KEncode
from tests.Convert.Solidworks.Research.Polygon.PolygonDecode import KDecode
from tests.Convert.Solidworks.Research.Polygon.PolygonReferences import KRefs
from tests.Convert.Solidworks.Research.Polygon.PolygonEdit import KEdit
from tests.Convert.Solidworks.Research.Polygon.PolygonReport import KReport
from tests.Convert.Solidworks.Research.Polygon.PolygonWidths import KWidths

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
