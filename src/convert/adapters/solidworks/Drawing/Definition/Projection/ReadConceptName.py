from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)


# referenced naming handles supply the actual native names of sheets and views
def ReadConceptName(Owner: ArchiveNode) -> str:
    NameNode = NeedConceptNode(Owner.FieldsValue.get("f18"), "moNodeName_c")
    NameValue = NameNode.FieldsValue.get("f08")
    if not isinstance(NameValue, str) or not NameValue:
        raise ValueError("SOLIDWORKS drawing concept lacks an owner name")
    return NameValue
