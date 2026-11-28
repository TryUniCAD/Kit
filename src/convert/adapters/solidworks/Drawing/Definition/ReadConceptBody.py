from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Drawing.Definition.ConceptState import ConceptState
from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.PlainNoteRequired import (
    PlainNoteError,
)
from convert.adapters.solidworks.Drawing.Definition.RunConceptRule import RunMethodMut
from convert.adapters.solidworks.Drawing.Definition.ShapeClasses import KShapeClasses


# native class tags must match the pinned release before any field dispatch
def ReadConceptBody(
    State: ConceptState, Reader: GraphReader, NodeValue: ArchiveNode
) -> None:
    ClassValue = NodeValue.ClassValue
    if not isinstance(ClassValue, RuntimeClass):
        raise ValueError("drawing concept contains an unresolved external class")
    ClassName = ClassValue.NameValue
    Schema = ClassValue.SchemaValue
    if ClassName == "moDisplayNote_c" and Schema == 1:
        raise PlainNoteError(f"unqualified drawing class {ClassName} schema {Schema}")
    if KShapeClasses.get(ClassName) != Schema:
        raise ValueError(f"unqualified drawing class {ClassName} schema {Schema}")
    HeaderReader = KHeaderClasses.get((ClassName, Schema))
    if HeaderReader is not None:
        HeaderReader(Reader, NodeValue)
    else:
        RunMethodMut(
            FieldScope(Reader, State, ClassName, NodeValue.FieldsValue), ClassName
        )
