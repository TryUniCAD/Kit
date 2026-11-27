from dataclasses import replace as CopyData
from pathlib import Path as FilePath
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


# an otherwise qualified archive isolates the semantic face map from unsupported journal attributes
def MakeFaceMap(Source: FilePath, Target: FilePath) -> None:
    Model = ReadDocument(Source.read_bytes())
    BodyNode = next(
        NodeValue
        for NodeValue in BuildGraph(Model).Nodes.values()
        if "faceVisualMaterialByAttrTagID" in NodeValue.Fields
        and "visualMaterial" in NodeValue.Fields
    )
    FaceMap = ValueMap((ValuePair("1", BodyNode.Fields["visualMaterial"]),))
    Segments = tuple(
        CopyData(
            Segment,
            Records=tuple(
                CopyData(
                    Record,
                    Groups=tuple(
                        CopyData(
                            Group,
                            Fields=tuple(
                                (
                                    CopyData(Field, Value=FaceMap)
                                    if Field.FieldName
                                    == "faceVisualMaterialByAttrTagID"
                                    else Field
                                )
                                for Field in Group.Fields
                            ),
                        )
                        for Group in Record.Groups
                    ),
                )
                for Record in Segment.Records
            ),
        )
        for Segment in Model.Segments
    )
    _ = Target.write_bytes(EmitParsed(CopyData(Model, Segments=Segments)))
