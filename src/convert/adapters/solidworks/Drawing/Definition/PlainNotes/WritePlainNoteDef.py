from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Definition.DefinitionWire import DefinitionWire
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankGraph import (
    CheckBlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteDrawBody import (
    WriteDrawBody,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontLayouts import (
    KFrontLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontSchemas import (
    KFrontSchemas,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontVirtuals import (
    KFrontVirtuals,
)
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteDrawing import (
    ResolvePlainNote,
)
from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteText import (
    ReadNoteText,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)


# the actual note folder may own its one verified annotation while other drawing owners remain in the blank profile
def WritePlainNoteDef(GraphValue: BlankGraph) -> DefinitionWire:
    CheckBlankGraph(GraphValue)
    ModelValue = NeedConceptNode(
        GraphValue.DocumentValue.FieldsValue["model"], "moDrawing_c"
    )
    SheetValue = NeedConceptNode(ModelValue.FieldsValue["f1430"], "moDrSheet")
    TextValue = ResolvePlainNote(SheetValue)
    _ = ReadNoteText(TextValue)
    FolderValue = NeedConceptNode(SheetValue.FieldsValue["f390"], "moDetailFolder_c")
    ContextValue = BodyContext(
        GraphValue.VersionValue, KFrontLayouts, KFrontVirtuals, KFrontSchemas
    )
    ContextValue.FlagsValue["owner_is_drawing"] = 1
    return WriteDrawBody(GraphValue, ContextValue, NoteFolder=FolderValue)
