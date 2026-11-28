from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontExt import (
    CheckFrontExt,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
    NeedDrawNumber,
)


# internal and property references must share one directory entry and one actual child configuration
def CheckFrontRefs(ViewValue: ArchiveNode, ModelValue: ArchiveNode) -> None:
    Reference = NeedConceptNode(ViewValue.FieldsValue["f5d8"], "moReferenceInternal_c")
    HeaderValue = NeedConceptNode(ModelValue.FieldsValue["fa8"], "moHeader_c")
    Directory = NeedConceptNode(HeaderValue.FieldsValue["f30"], "moExtObjectList_c")
    Entry = NeedConceptNode(Reference.FieldsValue["f3b0"], "moExtObject_c")
    Selector = NeedConceptMap(Entry.FieldsValue["refcfg"])
    SelectorName = Selector["f08"]
    ChildFields = NeedConceptMap(Entry.FieldsValue["shared"])
    Manager = NeedConceptNode(ModelValue.FieldsValue["f16a8"], "moDrwCompPropMgr_c")
    Entries = Manager.FieldsValue["f08"]
    if (
        not isinstance(Entries, (list, tuple))
        or len(CastValue(Sequence[object], Entries)) != 1
    ):
        raise BodyUnsupported(
            "front drawing Definition requires one component property reference"
        )
    RowValue = NeedConceptMap(CastValue(Sequence[object], Entries)[0])
    PropertyModel = NeedConceptNode(RowValue["model"], "moReferenceModel_c")
    Properties = NeedConceptNode(RowValue["properties"], "suObArray")
    if (
        Directory.FieldsValue["items"] != (Entry,)
        or ChildFields["f20"] != 2
        or not isinstance(SelectorName, CStringValue)
        or SelectorName.TextValue != ""
        or Selector["f10"] != -1
        or Manager.FieldsValue["f18"] is not ModelValue
        or Reference.FieldsValue["owner"] is not ModelValue
        or PropertyModel.FieldsValue["owner"] is not ModelValue
        or PropertyModel.FieldsValue["f3b0"] is not Entry
        or PropertyModel.FieldsValue["f3c0"] != Reference.FieldsValue["f3c0"]
        or PropertyModel.FieldsValue["f4f8"] is not None
        or Properties.FieldsValue["items"]
        or NeedDrawNumber(Reference.FieldsValue["f08"]) < 0
        or PropertyModel.FieldsValue["f08"] != -1
        or Reference.FieldsValue["f370"] != ViewValue.FieldsValue["f600"]
    ):
        raise BodyUnsupported(
            "front drawing Definition has invalid external model ownership"
        )
    CheckFrontExt(Reference, ModelValue)


from collections.abc import Sequence
from typing import cast as CastValue
