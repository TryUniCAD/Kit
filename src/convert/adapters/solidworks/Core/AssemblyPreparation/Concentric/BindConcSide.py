from math import isclose as IsClose

from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.NeedCircChild import (
    NeedCircChild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.ReadMintedCyl import (
    ReadMintedCyl,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.brep.Topology.BrepTopology import BrepFace
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# canonical topology supplies an actual neutral selection identity from the complete authored extrusion
def ReadConcSide(
    Document: CadDocument, PlanValue: CirclePlan
) -> tuple[BrepFace, CylinderSurface]:
    CircleValue = Document.sketches[0].entities[0].geometry
    if not isinstance(CircleValue, CircleGeometry):
        raise ValueError("concentric selection requires its actual circular profile")
    BrepValue, _, _, _ = BuildCircular(
        PlanValue.BodyId,
        Document.support_planes[0].transform,
        CircleValue,
        0.0,
        PlanValue.DepthValue * 1000.0,
        CircleValue.radius,
        CircleValue.radius,
    )
    if GetBrepErrors(BrepValue, frozenset((PlanValue.BodyId,))):
        raise ValueError("concentric selection requires complete neutral topology")
    Surfaces = {Value.id: Value for Value in BrepValue.surfaces}
    (SideValue,) = (
        (FaceValue, Surface)
        for FaceValue in BrepValue.faces
        if isinstance(Surface := Surfaces[FaceValue.surface_id], CylinderSurface)
    )
    return SideValue


# selected side ownership requires the generated file and complete neutral feature history
def BindConcSide(
    Document: CadDocument, Candidate: PartCandidate, FaceTag: int
) -> tuple[BrepFace, CylinderSurface, CylFaceBuild]:
    if Document.brep is not None:
        raise ValueError("concentric preparation requires a feature-only child")
    PlanValue = PlanCircle(Document, Measured=True)
    if (
        NeedCircChild(Candidate) != PlanValue
        or ReadNodeName(Candidate.CurrentConfig) != PlanValue.ConfigName
    ):
        raise ValueError("concentric candidate differs from its actual owned child")
    SideValue, Surface = ReadConcSide(Document, PlanValue)
    FaceValue = ReadMintedCyl(Candidate, FaceTag)
    Origin = Surface.origin
    AxisValue = Surface.axis
    Neutral = (
        Origin.x * 0.001,
        Origin.y * 0.001,
        Origin.z * 0.001,
        AxisValue.x,
        AxisValue.y,
        AxisValue.z,
        Surface.radius * 0.001,
    )
    Actual = (*FaceValue.OriginValue, *FaceValue.AxisValue, FaceValue.RadiusValue)
    if SideValue.same_sense is not True or not all(
        IsClose(Expected, Observed, rel_tol=1e-12, abs_tol=1e-12)
        for Expected, Observed in zip(Neutral, Actual, strict=True)
    ):
        raise ValueError("concentric generated carrier differs from the neutral side")
    return SideValue, Surface, FaceValue
