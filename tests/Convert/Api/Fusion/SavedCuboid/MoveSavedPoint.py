from dataclasses import replace as ReplaceData
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedCuboid.MoveDimPoint import MoveDimPoint


# typed mutation keeps the public compatibility test independent of vendor application launches
def MoveSavedPoint(
    Model: DocumentModel, AxisName: str, PointName: str, CoordinateName: str
) -> DocumentModel:
    Dimension = next(
        Value
        for Value in BuildGraph(Model).ByClass("FusionSketchLinearDim")
        if Value.Fields["constraintType"] == 1 << (22 + ("x", "y").index(AxisName))
    )
    InfoValue = Dimension.Fields["LinearDimensionInfo"]
    assert isinstance(InfoValue, ValueObject)
    Moved = ReplaceData(
        InfoValue,
        Groups=tuple(
            ReplaceData(
                Group,
                Fields=tuple(
                    (
                        ReplaceData(
                            Field, Value=MoveDimPoint(Field.Value, CoordinateName)
                        )
                        if Field.FieldName == PointName
                        else Field
                    )
                    for Field in Group.Fields
                ),
            )
            for Group in InfoValue.Groups
        ),
    )
    return ChangeField(Model, Dimension.ObjectId, "LinearDimensionInfo", Moved)
