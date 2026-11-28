from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    RequireProp,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.document.Models.DocumentModel import CadDocument


# literal pad presentation must attach to its own sketch and actual creating feature
def CheckPadOwners(Document: CadDocument, Metadata: Mapping[str, object]) -> None:
    if (
        Document.assembly is not None
        or Document.DrawingValue is not None
        or len(Document.bodies) != 1
        or len(Document.sketches) != 1
        or len(Document.feature_timeline) != 1
    ):
        raise ValueError(
            "FreeCAD Pad presentation requires one sketch and its one body"
        )
    BodyValue, Sketch, Feature = (
        Document.bodies[0],
        Document.sketches[0],
        Document.feature_timeline[0],
    )
    if (
        type(Feature.definition) is not ExtrudeFeature
        or Feature.sketch_id != Sketch.id
        or BodyValue.final_feature_id != Feature.id
        or Feature.suppressed
        or Sketch.suppressed
    ):
        raise ValueError("FreeCAD Pad presentation lost its actual creating feature")
    ObjectRows = NativeRows(Metadata["objects"])
    for Value, KindValue, TypeName in (
        (BodyValue, "body", "PartDesign::Body"),
        (Sketch, "sketch", "Sketcher::SketchObject"),
        (Feature, "feature", "PartDesign::Pad"),
    ):
        Record = NativeRecord(Value.attributes.get("freecad"))
        NameValue = ReadBoxString(Record["name"])
        if (
            Record not in ObjectRows
            or Record["type_id"] != TypeName
            or Value.id != f"freecad:{KindValue}:{NameValue}"
        ):
            raise ValueError("FreeCAD Pad presentation has a foreign owner")
        RequireProp(
            NativeRecord(Record["properties"]), "Label", "String", "String", Value.name
        )
