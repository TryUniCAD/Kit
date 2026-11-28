from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletHist import (
    ReadFilletHist,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletBrep import (
    BindFilletBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletModel import (
    BindFilletModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.FilletCentroid import (
    FilletCentroid,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.CheckFilletGeom import (
    CheckFilletGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.JoinFilletEdge import (
    JoinFilletEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.MakeFilletTopo import (
    MakeFilletTopo,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletBox import (
    ReadFilletBox,
)
from interchange.document.Models.DocumentModel import CadDocument


# actual same archive topology and saved feature semantics must qualify together
def BindFilletDoc(Document: CadDocument, Archive: SldprtArchive) -> CadDocument:
    (BodyValue,) = Document.bodies
    if Document.brep is None:
        raise ValueError("saved fillet requires an actual decoded active shell")
    History = ReadFilletHist(Archive)
    Header = ReadHeaderGraph(Archive.require("Header2"), 19000)
    EdgeValue = JoinFilletEdge(History, Header)
    Bounds, AxisIndex, Signs = ReadFilletBox(History, EdgeValue)
    CheckFilletGeom(History, EdgeValue, Bounds, AxisIndex, Signs)
    ModelValue = BindFilletBrep(History, Document.brep, BodyValue.id)
    Topology = MakeFilletTopo(Bounds, AxisIndex, History.RadiusValue)
    Centroid = FilletCentroid(Bounds, AxisIndex, Signs, History.RadiusValue)
    return BindFilletModel(
        ReplaceValue(Document, brep=ModelValue), History, EdgeValue, Topology, Centroid
    )
