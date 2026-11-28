from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepEdge, BrepFace


# qualified analytic carriers need a unique owner and a stable output order
@DataClass(frozen=True, slots=True)
class PrismCarriers:
    LinesValue: tuple[LineCurve, ...]
    PlanesValue: tuple[PlaneSurface, ...]
    LineOwners: Mapping[str, BrepEdge]
    PlaneOwners: Mapping[str, BrepFace]


# only used line and plane carriers with a single realizing boundary entity can be emitted
def ReadCarriers(ModelValue: BrepModel) -> PrismCarriers:
    LinesValue = tuple(Value for Value in ModelValue.curves if type(Value) is LineCurve)
    PlanesValue = tuple(
        Value for Value in ModelValue.surfaces if type(Value) is PlaneSurface
    )
    EdgesValue = {EdgeValue.curve_id: EdgeValue for EdgeValue in ModelValue.edges}
    FacesValue = {FaceValue.surface_id: FaceValue for FaceValue in ModelValue.faces}
    if (
        len(LinesValue) != len(ModelValue.curves)
        or len(PlanesValue) != len(ModelValue.surfaces)
        or len(EdgesValue) != len(ModelValue.edges)
        or len(FacesValue) != len(ModelValue.faces)
        or EdgesValue.keys() != {LineValue.id for LineValue in LinesValue}
        or FacesValue.keys() != {PlaneValue.id for PlaneValue in PlanesValue}
    ):
        raise ValueError(
            "local prism requires one exact line per edge and one plane per face"
        )
    return PrismCarriers(LinesValue, PlanesValue, EdgesValue, FacesValue)
