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
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import (
    KAnchorFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.WidthDimLayouts import (
    KWidthDimLayouts,
    KWidthDimSchemas,
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
    *,
    PartRelations: bool = False,
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
    if (
        LinkContext["model_compressed_stream"] != 1
        or LinkContext["model_is_part"] != 1
        or OwnerValue.ClassValue.NameValue != "moPart_c"
    ):
        raise BodyUnsupported(
            "resolved context does not match the inherited ordinary model"
        )
    if LinkContext["cmgr_f658"] != 0:
        raise BodyUnsupported(
            "ordinary resolved graph has an unsupported manager suffix"
        )
    return BodyContext(
        VersionValue,
        (
            {**KResolvedLayouts, **KAnchorFields, **KWidthDimLayouts}
            if PartRelations
            else KResolvedLayouts
        ),
        KResolvedVirtuals,
        {**KResolvedSchemas, **KWidthDimSchemas} if PartRelations else KResolvedSchemas,
        UsageValue,
        FlagsValue=(
            {**LinkContext, "part_relations": 1} if PartRelations else dict(LinkContext)
        ),
        PartRootValue=OwnerValue,
    )
