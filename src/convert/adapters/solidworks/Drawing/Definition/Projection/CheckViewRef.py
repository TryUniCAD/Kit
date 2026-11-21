from ntpath import normcase as NormCase, normpath as NormPath

from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef


# the view reference must reuse its inline directory entry and selected configuration
def CheckViewRef(
    ViewNode: ArchiveNode,
    Directory: ArchiveNode,
    ModelRef: DrawingModelRef,
    Configuration: str,
) -> None:
    Reference = NeedConceptNode(
        ViewNode.FieldsValue.get("f5d8"), "moReferenceInternal_c"
    )
    Entry = Reference.FieldsValue.get("f3b0")
    Saved = GetFileRef(Entry)
    Choice = NeedConceptMap(Reference.FieldsValue.get("f3c0"))
    if (
        Directory.FieldsValue.get("items") != (Entry,)
        or Saved.KindValue != 2
        or Saved.ConfigValue
        or Choice.get("f08") != Configuration
        or NormCase(NormPath(Saved.PathValue))
        != NormCase(NormPath(ModelRef.SourcePath))
    ):
        raise ValueError(
            "drawing Definition and native model reference indexes disagree"
        )
