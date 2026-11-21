from dataclasses import replace as Replace

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)


# independent authored geometry exercises the public end mode without opening any reference file
def MakeRevCase(PartName: str, TwoSides: bool) -> CadDocument:
    Document = MakePlainDoc(PartName, 18.0, 26.0, 10.0)
    Sketch = Document.sketches[0]
    Feature = Document.feature_timeline[0]
    AxisLine = SketchEntity(
        "line/axis",
        GeometryKind.KLine,
        LineGeometry(PlaneVector(-16, -24), PlaneVector(-16, 23)),
        construction=True,
    )
    Axis = Selection(
        "selection/axis",
        "Selected axis line",
        (
            SelectPathElem("sketch", Sketch.id),
            SelectPathElem("sketch_entity", AxisLine.id),
        ),
    )
    Rules = tuple(
        SketchRelation(
            f"relation/{Index}",
            "horizontal" if Index % 2 == 0 else "vertical",
            (ConstraintRef(Entity.id),),
        )
        for Index, Entity in enumerate(Sketch.entities)
    )
    Parameters = tuple(
        Parameter(
            f"parameter/{Name}",
            Name,
            ParameterValue(Angle, ValueKind.KAngle, "rad"),
            ParameterRole.KDriving,
            owner_id=Feature.id,
        )
        for Name, Angle in (("D1", 1.25), ("D2", 0.875))[: 1 + int(TwoSides)]
    )
    Definition = AngularRevolve(
        Axis.id,
        Parameters[0].id,
        SpaceVector(-16, 0, 24),
        SpaceVector(0, 0, -1),
        SideMode="two_sided" if TwoSides else "one_sided",
        AgainstParameterId=Parameters[1].id if TwoSides else None,
    )
    Plane = Replace(
        Document.support_planes[0],
        name="Top Plane",
        transform=Transform(
            SpaceVector(0, 0, 0),
            SpaceVector(1, 0, 0),
            SpaceVector(0, 0, -1),
            SpaceVector(0, 1, 0),
        ),
    )
    return Replace(
        Document,
        configurations=(Replace(Document.configurations[0], name="Default"),),
        support_planes=(Plane,),
        sketches=(
            Replace(Sketch, entities=(*Sketch.entities, AxisLine), constraints=Rules),
        ),
        selections=(Axis,),
        parameters=Parameters,
        feature_timeline=(
            Replace(
                Feature,
                kind=FeatureKind.KRevolution,
                definition=Definition,
                parameter_ids=tuple(Driver.id for Driver in Parameters),
                selection_ids=(Axis.id,),
            ),
        ),
    )
