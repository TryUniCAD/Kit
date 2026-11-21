from types import MappingProxyType

from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.Notes.NoteVirtuals import (
    KNoteVirtuals,
)

from convert.adapters.solidworks.Drawing.Definition.Emission.BlankVirtuals import (
    KBlankVirtuals,
)

# view and reference inheritance must dispatch their own concrete classes through the shared concept serializers
KFrontVirtuals = MappingProxyType(
    {
        **KBlankVirtuals,
        **KNoteVirtuals,
        **{
            (ClassName, SlotValue): TargetValue
            for ClassName in (
                "moAbsoluteView",
                "moReferenceInternal_c",
                "moReferenceModel_c",
            )
            for SlotValue, TargetValue in (
                (1208, "moConcept_c.SerializeLWData"),
                (1216, "moConcept_c.SerializeResolvedData"),
                (1016, True),
                (1000, "moFeature_c.SerializeXmlData"),
            )
        },
    }
)
