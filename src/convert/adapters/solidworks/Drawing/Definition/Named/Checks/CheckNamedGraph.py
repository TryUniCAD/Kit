from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckBlankDoc import (
    CheckBlankDoc,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontRefs import (
    CheckFrontRefs,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckFrontSheet import (
    CheckFrontSheet,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckViewOwn import (
    CheckViewOwn,
)
from convert.adapters.solidworks.Drawing.Definition.Named.Checks.CheckNamedState import (
    CheckNamedState,
)
from convert.adapters.solidworks.Drawing.Definition.Named.NamedGraph import NamedGraph
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# named profiles must preserve the original active sheet and child reference ownership before extending orientation admission
def CheckNamedGraph(GraphValue: NamedGraph) -> None:
    Document = GraphValue.DocumentValue
    CheckBlankDoc(BlankGraph(Document, GraphValue.VersionValue))
    ModelValue = NeedConceptNode(Document.FieldsValue["model"], "moDrawing_c")
    FieldsValue = ModelValue.FieldsValue
    SheetValue = NeedConceptNode(FieldsValue["f1430"], "moDrSheet")
    Children = ReadBlankKids(ModelValue)
    if (
        len(Children) != 7
        or sum(NodeValue is SheetValue for NodeValue in Children) != 1
        or any(FieldsValue[FieldName] for FieldName in ("f1560", "f1570", "f1538"))
        or FieldsValue["n1740"] != 0
        or FieldsValue["f1458"] is not None
        or FieldsValue["fe80"] is None
        or NeedConceptMap(FieldsValue["f14f8"])["items"]
        or NeedConceptMap(FieldsValue["zero_instance_blocks"])["items"]
        or NeedConceptNode(FieldsValue["fed0"], "moLayerMgr_c").FieldsValue["f30"]
        is not ModelValue
    ):
        raise BodyUnsupported(
            "named drawing Definition has unqualified root ownership or model link caches"
        )
    Supports = CheckFrontSheet(SheetValue, ModelValue)
    UiSketch = NeedConceptNode(Document.FieldsValue["fac0"], "uoSketch")
    if UiSketch.FieldsValue["profile_feature_id"] != Supports[1].FieldsValue["f08"]:
        raise BodyUnsupported(
            "named drawing Definition ui sketch has the wrong active sheet profile"
        )
    ViewValue = Supports[3]
    CheckViewOwn(ViewValue, ModelValue)
    CheckNamedState(ViewValue, GraphValue.OrientationValue)
    CheckFrontRefs(ViewValue, ModelValue)
