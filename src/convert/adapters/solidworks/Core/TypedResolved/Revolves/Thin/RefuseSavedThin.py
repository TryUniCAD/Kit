from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import HasPayload
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.IsThinRev import (
    IsThinRev,
)


# a physical solid cache cannot qualify the editable history of a saved thin revolve
def RefuseSavedThin(Archive: SldprtArchive, Model: NativeModel) -> None:
    if (
        IsThinRev(Model)
        and ContainerMo(Archive.streams) == 19000
        and any(HasPayload(Record.data) for Record in Archive.records)
    ):
        raise SldprtFormat("saved thin revolve has unverified editable history")
