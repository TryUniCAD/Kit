from dataclasses import replace as CopyData

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# auxiliary corruption must remain independently encoded without changing the geometric drivers
def ChangeDualAux(Model: DocumentModel, ModeName: str) -> DocumentModel:
    Context = SelectExtrusion(BuildGraph(Model))
    FieldName, MemberName, Amount = (
        ("visualMaterial", "UseCustomizedColor", True)
        if ModeName == "appearance"
        else (
            ("physicalMaterial", "assetReference", "missing-asset")
            if ModeName == "material"
            else ("visualMaterial", "assetReference", "missing-appearance")
        )
    )
    Value = Context.BodyNode.Fields[FieldName]
    assert isinstance(Value, ValueObject)
    assert any(
        Field.FieldName == MemberName
        for Group in Value.Groups
        for Field in Group.Fields
    )
    Changed = CopyData(
        Value,
        Groups=tuple(
            CopyData(
                Group,
                Fields=tuple(
                    (
                        CopyData(Field, Value=Amount)
                        if Field.FieldName == MemberName
                        else Field
                    )
                    for Field in Group.Fields
                ),
            )
            for Group in Value.Groups
        ),
    )
    return ChangeField(Model, Context.BodyNode.ObjectId, FieldName, Changed)
