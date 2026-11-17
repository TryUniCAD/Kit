from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# native runtime feature owners must be reconstructed from serialized containment without introducing separate wire fields
def BindFrontMut(Document: ArchiveNode) -> None:
    ModelValue = NeedConceptNode(Document.FieldsValue["model"], "moDrawing_c")
    SheetValue = NeedConceptNode(ModelValue.FieldsValue["f1430"], "moDrSheet")
    PairsValue = [(ChildValue, ModelValue) for ChildValue in ReadBlankKids(ModelValue)]
    PairsValue.extend(
        (ChildValue, SheetValue) for ChildValue in ReadBlankKids(SheetValue)
    )
    for ViewValue in ReadBlankKids(SheetValue):
        if ViewValue.ClassValue.NameValue != "moAbsoluteView":
            continue
        PairsValue.extend(
            (ChildValue, ViewValue) for ChildValue in ReadBlankKids(ViewValue)
        )
        PairsValue.append(
            (
                NeedConceptNode(ViewValue.FieldsValue["f5d8"], "moReferenceInternal_c"),
                ModelValue,
            )
        )
    Manager = NeedConceptNode(ModelValue.FieldsValue["f16a8"], "moDrwCompPropMgr_c")
    RowsValue = Manager.FieldsValue["f08"]
    if not isinstance(RowsValue, (tuple, list)):
        raise BodyUnsupported(
            "front drawing Definition requires ordered property references"
        )
    for RowValue in CastValue(Sequence[object], RowsValue):
        PairsValue.append(
            (
                NeedConceptNode(
                    NeedConceptMap(RowValue)["model"], "moReferenceModel_c"
                ),
                ModelValue,
            )
        )
    for ChildValue, OwnerValue in PairsValue:
        if ChildValue.FieldsValue.setdefault("owner", OwnerValue) is not OwnerValue:
            raise BodyUnsupported(
                "front drawing Definition has conflicting runtime containment"
            )


from collections.abc import Sequence
from typing import cast as CastValue
