from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankDoc import (
    CheckBlankDoc,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankSheet import (
    CheckBlankSheet,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)


# the complete codec admits only one unformatted empty sheet with its real support aliases
def CheckBlankGraph(GraphValue: BlankGraph) -> None:
    CheckBlankDoc(GraphValue)
    Document = GraphValue.DocumentValue
    FieldsValue = Document.FieldsValue
    ModelValue = NeedConceptNode(FieldsValue["model"], "moDrawing_c")
    ModelFields = ModelValue.FieldsValue
    if (
        any(ModelFields[FieldName] for FieldName in ("f1560", "f1570", "f1538"))
        or ModelFields["n1740"] != 0
        or ModelFields["f1458"] is not None
        or ModelFields["fe80"] is None
    ):
        raise BodyUnsupported("blank drawing Definition excludes populated model links")
    SheetValue = NeedConceptNode(ModelFields["f1430"], "moDrSheet")
    OwnedValue = ReadBlankKids(ModelValue)
    if (
        len(OwnedValue) != 7
        or sum(ChildValue is SheetValue for ChildValue in OwnedValue) != 1
    ):
        raise BodyUnsupported(
            "blank drawing Definition requires one active owned sheet"
        )
    Supports = CheckBlankSheet(SheetValue)
    ManagerValue = NeedConceptNode(ModelFields["f16a8"], "moDrwCompPropMgr_c")
    if (
        ManagerValue.FieldsValue["f18"] is not ModelValue
        or ManagerValue.FieldsValue["f08"]
    ):
        raise BodyUnsupported(
            "blank drawing Definition has invalid component property ownership"
        )
    NamesValue = NeedConceptMap(ModelFields["f14f8"])
    BlocksValue = NeedConceptMap(ModelFields["zero_instance_blocks"])
    if NamesValue["items"] or BlocksValue["items"]:
        raise BodyUnsupported(
            "blank drawing Definition excludes named caches or block instances"
        )
    HeaderValue = NeedConceptNode(ModelFields["fa8"], "moHeader_c")
    DirectoryValue = HeaderValue.FieldsValue["f30"]
    if (
        DirectoryValue is not None
        and NeedConceptNode(DirectoryValue, "moExtObjectList_c").FieldsValue["items"]
    ):
        raise BodyUnsupported("blank drawing Definition excludes external model files")
    UiSketch = NeedConceptNode(FieldsValue["fac0"], "uoSketch")
    if UiSketch.FieldsValue["profile_feature_id"] != Supports[1].FieldsValue["f08"]:
        raise BodyUnsupported(
            "blank drawing Definition ui sketch has the wrong profile identity"
        )
    LayersValue = NeedConceptNode(ModelFields["fed0"], "moLayerMgr_c")
    if LayersValue.FieldsValue["f30"] is not ModelValue:
        raise BodyUnsupported(
            "blank drawing Definition layer manager has the wrong owner"
        )
