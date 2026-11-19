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
