from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import (
    KResolvedLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedSchemas import (
    KResolvedSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedVirtuals import (
    KResolvedVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot


# resolved grammar needs the separate manager word and actual model type before reading any feature
def MakeResolvedCtx(
    VersionValue: int,
    SeedValue: MapSnapshot,
    LinkContext: Mapping[str, int],
    UsageValue: BodyUsage | None,
) -> BodyContext:
    UsageValue = NewBodyUsage(VersionValue, UsageValue)
    if set(LinkContext) != {
        "model_compressed_stream",
        "model_is_part",
        "cmgr_f658",
    } or any(type(Value) is not int for Value in LinkContext.values()):
        raise BodyUnsupported(
            "ordinary resolved graph requires its exact typed model and manager context"
        )
    OwnerValue = FindModelRoot(SeedValue)
    if LinkContext["model_compressed_stream"] != 1 or LinkContext[
        "model_is_part"
    ] != int(OwnerValue.ClassValue.NameValue == "moPart_c"):
        raise BodyUnsupported(
            "resolved context does not match the inherited ordinary model"
        )
    return BodyContext(
        VersionValue,
        KResolvedLayouts,
        KResolvedVirtuals,
        KResolvedSchemas,
        UsageValue,
        FlagsValue=dict(LinkContext),
    )
