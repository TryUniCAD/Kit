from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Drawing.Definition.Appearance.ReadAppearState import (
    ReadAppearState,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


# the ui owner must select one proved document identity and exclude unmodeled optional payloads
def CheckBlankDoc(GraphValue: BlankGraph) -> None:
    Document = GraphValue.DocumentValue
    if GraphValue.VersionValue != 19000 or Document.ClassValue != RuntimeClass(
        "uiDrawingDoc_c", 1
    ):
        raise BodyUnsupported(
            "blank drawing Definition requires current ui drawing ownership"
        )
    FieldsValue = Document.FieldsValue
    _ = ReadAppearState(Document, GraphValue.VersionValue)
    if FieldsValue["drawing_end_marker"] != 3503:
        raise BodyUnsupported("blank drawing Definition has unqualified ui state")
    ClsidTail = FieldsValue["clsid_d"]
    if not isinstance(ClsidTail, bytes):
        raise BodyUnsupported(
            "blank drawing Definition requires a typed document clsid"
        )
    ClsidValue = (
        EncodeScalar(FieldsValue["clsid_a"], "u32")
        + EncodeScalar(FieldsValue["clsid_b"], "u16")
        + EncodeScalar(FieldsValue["clsid_c"], "u16")
        + ClsidTail
    )
    if ClsidValue != KDrawClsid:
        raise BodyUnsupported("blank drawing Definition has the wrong document clsid")
