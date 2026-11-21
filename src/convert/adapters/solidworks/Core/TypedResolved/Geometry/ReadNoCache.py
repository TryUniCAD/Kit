from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.ReadCircleGeom import (
    ReadCircleGeom,
)
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadPocketGeom import (
    ReadPocketGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.BuildPrismGeom import (
    BuildPrismGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismScope import (
    CheckPrismScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismPlan import (
    ReadPrismPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.ReadRevGeom import (
    ReadRevGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinGeom import (
    ReadThinGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import (
    ReadColdOutput,
)


# unsupported no cache documents must retain the existing strict payload error while proven ordinary prisms gain computed neutral geometry
def ReadNoCache(
    Archive: SldprtArchive, ModelValue: NativeModel, BodyId: str
) -> PartGeometry | None:
    if not IsCacheAbsent(Archive):
        return None
    RelationValue = ModelValue.WidthDepth
    if RelationValue is not None and RelationValue.SourceValue is not Archive:
        return None
    try:
        LinkValue = (
            ReadNativeLink(Archive, ModelValue.active_configuration_id)
            if RelationValue is None
            else RelationValue.LinkValue
        )
        ManagerValue = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        if ModelValue.TypedGraph.get("cut_body_dependency") is not None:
            return ReadPocketGeom(LinkValue, ManagerValue, ModelValue, BodyId)
        if any(
            Feature.class_name == "moRevolution_c" for Feature in ModelValue.features
        ):
            return ReadRevGeom(LinkValue, ManagerValue, ModelValue, BodyId)
        if any(
            Feature.class_name == "moRevolutionThin_c"
            for Feature in ModelValue.features
        ):
            return ReadThinGeom(LinkValue, ManagerValue, ModelValue, BodyId)
        if any(
            SketchValue.TypedCircle is not None for SketchValue in ModelValue.sketches
        ):
            return ReadCircleGeom(LinkValue, ManagerValue, ModelValue, BodyId)
        ColdValue = ReadColdOutput(LinkValue)
        Features = CheckPrismScope(LinkValue, ManagerValue, ModelValue, ColdValue)
        return BuildPrismGeom(
            ReadPrismPlan(LinkValue, Features, ColdValue),
            BodyId,
            ColdValue,
            CreatorValue=Features[ModelValue.operations[0].object_id],
        )
    except (ValueError, TypeError, KeyError):
        return None
