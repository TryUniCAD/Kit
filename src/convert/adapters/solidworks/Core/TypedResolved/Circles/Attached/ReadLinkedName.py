from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.AttachedRound import (
    AttachedRound,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.AttachCircError import (
    AttachCircError,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.CheckBodyCache import (
    CheckBodyCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadAttachBody import (
    ReadAttachBody,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# recognized attached geometry must agree before its body name enters the portable model
def ReadLinkedName(
    LinkValue: NativeLink,
    Owner: ExtrudeOwner,
    CircleValue: LocalCircle,
    InactiveDepth: float,
    BodyId: int,
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    SavedBody: bool,
) -> tuple[str, AttachedRound]:
    try:
        if SavedBody:
            CheckBodyCache(
                LinkValue,
                Owner.NodeValue,
                CircleValue,
                InactiveDepth,
                ModelValue.configurations[0].name,
            )
        return ReadAttachBody(
            LinkValue,
            Owner.NodeValue,
            BodyId,
            Archive.require(KPartitionStream),
            ModelValue,
            SavedBody=SavedBody,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as ErrorInfo:
        raise AttachCircError(str(ErrorInfo)) from ErrorInfo
