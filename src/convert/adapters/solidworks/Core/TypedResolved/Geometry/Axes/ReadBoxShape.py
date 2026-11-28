from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadAxisGeom import (
    ReadAxisGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import (
    ReadColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.IsBoxAxisModel import (
    IsBoxAxisModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# only the cache free principal axis model enters the linked signed stock reader
def ReadBoxShape(
    Archive: SldprtArchive, ModelValue: NativeModel, Settings: ReadOptions, BodyId: str
) -> tuple[NativeModel, PartGeometry | None]:
    if Settings.extract_raw_brep or not IsBoxAxisModel(Archive, ModelValue):
        return ModelValue, None
    try:
        LinkValue = ReadNativeLink(Archive, ModelValue.active_configuration_id)
        ManagerValue = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        return ReadAxisGeom(
            Archive,
            LinkValue,
            ManagerValue,
            ModelValue,
            ReadColdOutput(LinkValue),
            BodyId,
        )
    except (ValueError, TypeError, KeyError, OverflowError) as ErrorInfo:
        if Settings.strict:
            raise SldprtFormat(
                "cache free axis box has unverified typed history"
            ) from ErrorInfo
        return ModelValue, None
