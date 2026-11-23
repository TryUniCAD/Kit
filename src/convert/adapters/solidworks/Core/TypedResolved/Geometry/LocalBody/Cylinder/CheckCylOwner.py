from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckBareOwner import (
    CheckBareOwner,
)


# a periodic capsule needs physical feature atom and rollback ownership before projection
def CheckCylOwner(
    Archive: SldprtArchive,
    OwnerValue: NativeFeature,
    GroupKey: str,
    MarkValue: int,
    PriorMark: int,
) -> None:
    CheckBareOwner(
        Archive, OwnerValue, GroupKey, MarkValue, PriorMark, "local cylinder"
    )
