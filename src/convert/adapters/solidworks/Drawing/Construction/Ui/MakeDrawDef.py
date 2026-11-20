from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefHead import (
    MakeDefHead,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefTail import (
    MakeDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootGraph import (
    DrawRootGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import (
    BlankGraph,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import KDrawClsid


# drawing ui construction must reuse shared native settings while retaining its real model and sheet sketch owners
def MakeDrawDef(
    Settings: ModelDefInput, GraphValue: DrawRootGraph, *, DisplayGrid: bool = True
) -> BlankGraph:
    if type(Settings) is not ModelDefInput or type(GraphValue) is not DrawRootGraph:
        raise TypeError(
            "drawing ui construction requires typed settings and an actual model graph"
        )
    ModelValue = GraphValue.ModelValue
    RequireRootNode(ModelValue, "moDrawing_c")
    SheetValue = GraphValue.SheetValue
    if (
        ModelValue.FieldsValue["f1430"] is not SheetValue.SheetValue
        or SheetValue.SheetValue.FieldsValue["owner"] is not ModelValue
        or SheetValue.UiSketch.FieldsValue["profile_feature_id"]
        != SheetValue.ProfileValue.FieldsValue["f08"]
    ):
        raise ValueError(
            "drawing ui construction has an unrelated active sheet or sketch"
        )
    FieldsValue = (
        MakeDefHead(Settings, DisplayGrid=DisplayGrid)
        | MakeDefTail()
        | {
            "clsid_a": int.from_bytes(KDrawClsid[:4], "little"),
            "clsid_b": int.from_bytes(KDrawClsid[4:6], "little"),
            "clsid_c": int.from_bytes(KDrawClsid[6:8], "little"),
            "clsid_d": KDrawClsid[8:],
            "model": ModelValue,
            "fac0": SheetValue.UiSketch,
            "facc": 2,
            "drawing_end_marker": 3503,
            "f16c8": 0,
            "f16dc": 0,
        }
    )
    SheetFields = SheetValue.SheetValue.FieldsValue
    if SheetFields["has_f430"] == 1:
        FieldsValue["faf0"] = dict(NeedConceptMap(SheetFields["f430"]))
    return BlankGraph(
        ArchiveNode(RuntimeClass("uiDrawingDoc_c", 1), FieldsValue),
        Settings.VersionValue,
    )
