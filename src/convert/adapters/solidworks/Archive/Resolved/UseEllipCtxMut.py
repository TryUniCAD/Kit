from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.EllipseFields import (
    KEllipseFields,
    KEllipseHandle,
    KEllipseLayout,
)


# the measured ellipse lane needs the ordinary linked part manager and archive context
def UseEllipCtxMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000 or ContextValue.FlagsValue != {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": 1,
    }:
        raise BodyUnsupported("unsupported ordinary SOLIDWORKS ellipse archive context")
    CallsValue = ContextValue.UsageValue.SchemaCalls
    if KEllipseHandle in CallsValue or KEllipseLayout in CallsValue:
        raise BodyUnsupported("SOLIDWORKS ellipse archive requires fresh layout usage")
    ContextValue.LayoutsValue = {**ContextValue.LayoutsValue, **KEllipseFields}
    ContextValue.SchemasValue = {**ContextValue.SchemasValue, KEllipseHandle: (1,)}
