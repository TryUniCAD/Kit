from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.BuildPrismGeom import (
    BuildPrismGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismScope import (
    CheckPrismScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismGeometry import (
    PrismGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import (
    ReadPrismPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import (
    ReadColdOutput,
)


# unsupported no cache documents must retain the existing strict payload error while proven ordinary prisms gain computed neutral geometry
def ReadNoCache(
    Archive: SldprtArchive, ModelValue: NativeModel, BodyId: str
) -> PrismGeometry | None:
    if not IsCacheAbsent(Archive):
        return None
    try:
        LinkValue = ReadNativeLink(Archive, ModelValue.active_configuration_id)
        ManagerValue = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        ColdValue = ReadColdOutput(LinkValue)
        Features = CheckPrismScope(LinkValue, ManagerValue, ModelValue, ColdValue)
        return BuildPrismGeom(
            ReadPrismPlan(LinkValue, Features, ColdValue), BodyId, ColdValue
        )
    except (ValueError, TypeError, KeyError):
        return None
