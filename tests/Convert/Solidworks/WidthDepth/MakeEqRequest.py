from dataclasses import replace as ReplaceValue
from json import loads as LoadJson

from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchRelation
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Convert.Solidworks.PlainWriting.MakePlainDoc import MakePlainDoc


# disclosed dimensions names and output event independently supply the queue model
def MakeEqRequest() -> dict[str, object]:
    NameValue = "WidthDepthSameLocator04"
    WidthValue, HeightValue = 39.125, 17.375
    Plain = MakePlainDoc(
        NameValue,
        ((0.0, 0.0), (WidthValue, 0.0), (WidthValue, HeightValue), (0.0, HeightValue)),
        WidthValue / 2.0,
    )
    (SketchValue,) = Plain.sketches
    (DepthValue,) = Plain.parameters
    WidthDriver = SketchDriver("width", "D1", WidthValue, SketchValue.id)
    HeightDriver = SketchDriver("height", "D2", HeightValue, SketchValue.id)
    BoundSketch = BindEqSketch(SketchValue, WidthDriver, HeightDriver)
    Model = ReplaceValue(
        Plain,
        sketches=(BoundSketch,),
        parameters=(HeightDriver, DepthValue, WidthDriver),
    )
    return {
        "document": LoadJson(Model.to_json()),
        "equation": {
            "target": DepthValue.id,
            "dependency": WidthDriver.id,
            "divisor": 2,
        },
        "sdk_created_at": 1795164000,
        "settings": {
            "output": {"path_name": rf"C:\KitSdkCandidates\{NameValue}.SLDPRT"}
        },
    }


# the two actual sketch sides own distinct driving distances and axis relations
def BindEqSketch(
    SketchValue: Sketch, WidthDriver: Parameter, HeightDriver: Parameter
) -> Sketch:
    AxisRows = tuple(
        SketchRelation(
            f"relation/axis/{IndexValue}", KindValue, (ConstraintRef(EntityValue.id),)
        )
        for IndexValue, (EntityValue, KindValue) in enumerate(
            zip(SketchValue.entities, ("horizontal", "vertical") * 2, strict=True)
        )
    )
    LengthRows = tuple(
        SketchRelation(
            f"relation/length/{IndexValue}",
            "distance",
            (ConstraintRef(EntityId, "start"), ConstraintRef(EntityId, "end")),
            parameter_id=DriverValue.id,
        )
        for IndexValue, (EntityId, DriverValue) in enumerate(
            zip(("edge/0", "edge/1"), (WidthDriver, HeightDriver), strict=True)
        )
    )
    return ReplaceValue(
        SketchValue,
        constraints=(*AxisRows, *LengthRows),
        parameter_ids=(WidthDriver.id, HeightDriver.id),
    )


# each authored driving length belongs to its actual sketch and selected side
def SketchDriver(
    LabelValue: str, NameValue: str, Distance: float, OwnerId: str
) -> Parameter:
    return Parameter(
        f"parameter/{LabelValue}",
        NameValue,
        ParameterValue(Distance, ValueKind.KLength, "mm"),
        ParameterRole.KDriving,
        owner_id=OwnerId,
    )
