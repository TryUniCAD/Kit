from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfView import (
    MakeChmfView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import (
    MakeDistTail,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Shells.OpenShellPlan import (
    OpenShellPlan,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import (
    PutAnnoCatalog,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# one model frame places the wall driver on the negative x side and its annotation on the cap
def MakeShellView(
    Model: ArchiveNode,
    Feature: ArchiveNode,
    HandleValue: ArchiveNode,
    Frame: PlaneFrame,
    PlanValue: OpenShellPlan,
) -> ArchiveNode:
    ViewValue = AnnoViewInput(
        "Shell Driver View", (Frame.AxisU, Frame.AxisV, Frame.NormalValue)
    )
    Views = PutAnnoCatalog(Model, 19000, (ViewValue,), None, (None,))
    ViewId = FieldInt(Views[ViewValue.NameValue].FieldsValue, "f360")
    ThicknessM = PlanValue.ThicknessM
    Stock = PlanValue.StockValue
    Origin = Frame.OriginValue
    Fields = MakeChmfView(Feature, HandleValue, ViewId, ThicknessM, False)
    Fields.update(MakeDistTail())
    Fields.update(
        f6a0={
            **RequireRecord(Fields["f6a0"]),
            "f38": MakePoint(
                XValue=Origin[0] + Stock.WidthValue / 2,
                YValue=Origin[1],
                ZValue=Stock.DepthValue,
            ),
        },
        f880=MakePoint(YValue=1.0),
        f8a8=1.25,
        f8b0=Stock.HeightValue / 10,
        f988=MakePoint(XValue=ThicknessM),
        f9a0=MakePoint(XValue=ThicknessM),
        fa38=MakePoint(XValue=1.0),
        fad0=ThicknessM,
        fb68=1,
        fb6c=1,
        ff80=0,
    )
    return MakeChmfNode("moDisplayDistanceDim_c", Fields)
