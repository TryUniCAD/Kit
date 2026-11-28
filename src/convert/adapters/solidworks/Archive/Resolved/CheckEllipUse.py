from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.EllipseFields import (
    KEllipseHandle,
    KEllipseLayout,
)


# the explicit replay scope covers one inline ellipse with its one independently mapped handle
def CheckEllipUse(ContextValue: BodyContext) -> None:
    CallsValue = ContextValue.UsageValue.SchemaCalls
    if CallsValue[KEllipseHandle] != 1 or CallsValue[KEllipseLayout] != 1:
        raise BodyUnsupported(
            "SOLIDWORKS ellipse archive requires one ellipse and one handle"
        )
