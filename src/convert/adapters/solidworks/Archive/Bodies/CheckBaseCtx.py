from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# alternate import archive branches need their own proven ownership and field layout
def CheckBaseCtx(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000 or ContextValue.FlagsValue != {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": 1,
    }:
        raise BodyUnsupported("unsupported ordinary base body archive context")
