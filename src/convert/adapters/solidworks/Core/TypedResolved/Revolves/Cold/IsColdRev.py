from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)


# the typed analytic path applies only when the native revolve has no physical body cache
def IsColdRev(Archive: SldprtArchive, Model: NativeModel) -> bool:
    return (
        ContainerMo(Archive.streams) == 19000
        and any(Value.kind == "revolve_join" for Value in Model.operations)
        and IsCacheAbsent(Archive)
    )
