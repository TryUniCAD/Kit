from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinEdges import (
    CheckThinEdges,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinFace import (
    CheckThinFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadFaceRims import (
    ReadFaceRims,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.ReadThinPoints import (
    ReadThinPoints,
)
from interchange.brep.Topology.BrepModel import BrepModel


# the original cache remains authoritative once its boundary agrees with all live drivers
def CheckThinBrep(Actual: BrepModel, Expected: BrepModel) -> None:
    PointsValue = ReadThinPoints(Actual, Expected)
    EdgeIds = CheckThinEdges(Actual, Expected, PointsValue)
    FacesValue = ReadFaceRims(Actual, EdgeIds)
    TargetsValue = ReadFaceRims(
        Expected, {EdgeValue.id: EdgeValue.id for EdgeValue in Expected.edges}
    )
    if FacesValue.keys() != TargetsValue.keys() or len(FacesValue) != len(Actual.faces):
        raise ValueError(
            "SOLIDWORKS thin cache has incomplete sector face trim ownership"
        )
    SurfacesValue = {Surface.id: Surface for Surface in Actual.surfaces}
    TargetSurfs = {Surface.id: Surface for Surface in Expected.surfaces}
    for RimValue, FaceValue in FacesValue.items():
        CheckThinFace(
            SurfacesValue[FaceValue.surface_id],
            TargetSurfs[TargetsValue[RimValue].surface_id],
        )
