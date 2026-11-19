from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.FavoriteFields import (
    KNoteFavoriteFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.CharacterFields import (
    KNoteCharacterFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.LineFields import (
    KNoteLineFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.TextFields import (
    KNoteTextFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.WrapperFields import (
    KNoteWrapperFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.AbsoluteFields import (
    KNoteAbsoluteFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.ComponentFields import (
    KNoteComponentFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.CurveFields import (
    KNoteCurveFields,
)
from types import MappingProxyType

from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.AttachFields import (
    KNoteAttachFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.DetailFields import (
    KNoteDetailFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteFields import (
    KNoteFields,
)

from convert.adapters.solidworks.Archive.Definition.Fields.DocStyleFields import (
    KDocStyleFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.BlankLayouts import (
    KBlankLayouts,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.CompFields import (
    KCompFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.DownstreamFields import (
    KDownstreamFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.EnvironmentFields import (
    KDrawingEnvironmentFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.EdgeFields import (
    KEdgeFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.SupportFields import (
    KSupportFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.ViewFields import (
    KViewFields,
)

# a linked profile must preserve the exact blank layout while adding independently proved view owners
KFrontLayouts = MappingProxyType(
    {
        **KNoteAttachFields,
        **KNoteDetailFields,
        **KNoteFields,
        **KNoteFavoriteFields,
        **KNoteCharacterFields,
        **KNoteLineFields,
        **KNoteTextFields,
        **KNoteWrapperFields,
        **KNoteAbsoluteFields,
        **KNoteComponentFields,
        **KNoteCurveFields,
        **KBlankLayouts,
        **KViewFields,
        **KSupportFields,
        **KCompFields,
        **KEdgeFields,
        **KDownstreamFields,
        **KDrawingEnvironmentFields,
        "moScaleSysScale_c": (),
        "moLineStyle_c": KDocStyleFields["moLineStyle_c"],
        "moBomInfoMgr_c": KDocStyleFields["moBomInfoMgr_c"],
    }
)
