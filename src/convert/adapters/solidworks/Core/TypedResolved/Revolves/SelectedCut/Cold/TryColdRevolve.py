from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.BuildColdRevolve import (
    BuildColdRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolvePart import (
    ColdRevolvePart,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ReadColdRevolve import (
    ReadColdRevolve,
)


# only the actual cache free selected revolve profile can reconstruct two bodies before native rebuild
def TryColdRevolve(
    Archive: SldprtArchive, Model: NativeModel, Settings: ReadOptions
) -> ColdRevolvePart | None:
    if (
        not Settings.include_brep
        or Settings.extract_raw_brep
        or Model.active_configuration_id != 0
        or tuple((Value.configuration_id, Value.name) for Value in Model.configurations)
        != ((0, "Default"),)
        or tuple(Value.kind for Value in Model.operations)
        != ("revolve_join", "revolve_join", "revolve_cut")
        or not IsCacheAbsent(Archive)
    ):
        return None
    try:
        LinkValue = ReadNativeLink(Archive, 0)
        Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        return BuildColdRevolve(ReadColdRevolve(LinkValue, Manager, Model))
    except (ValueError, TypeError, KeyError, OverflowError):
        return None
