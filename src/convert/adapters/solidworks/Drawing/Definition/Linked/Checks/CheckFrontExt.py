from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# drawing external features require their real live reference backlink and containing drawing file identity
def CheckFrontExt(Reference: ArchiveNode, ModelValue: ArchiveNode) -> None:
    External = NeedConceptNode(Reference.FieldsValue["f4f8"], "moExtFeature_c")
    FieldsValue = External.FieldsValue
    HeaderValue = NeedConceptNode(ModelValue.FieldsValue["fa8"], "moHeader_c")
    OwnerFile = NeedConceptNode(HeaderValue.FieldsValue["f38"], "moExtObject_c")
    FileFields = NeedConceptMap(FieldsValue["f10"])
    SharedFile = NeedConceptMap(OwnerFile.FieldsValue["shared"])
    NameValue = NeedConceptNode(FieldsValue["f38"], "moCStringHandle_c").FieldsValue[
        "value"
    ]
    NodeName = NeedConceptNode(
        Reference.FieldsValue["f18"], "moNodeName_c"
    ).FieldsValue["f08"]
    if (
        FieldsValue["f50"] is not Reference
        or FieldsValue["f44"] != Reference.FieldsValue["f08"]
        or FieldsValue["f40"] != 0
        or FieldsValue["f58"] != -1
        or FieldsValue["f18"] != {"f08": "", "f10": -1}
        or (FileFields["f20"], FileFields["f08"]) != (4, 0)
        or any(
            FileFields[FieldName] is not SharedFile[FieldName]
            for FieldName in ("h18", "h10")
        )
        or not isinstance(NameValue, CStringValue)
        or NameValue.TextValue != NodeName
    ):
        raise BodyUnsupported(
            "front drawing Definition has an unqualified external feature profile"
        )
