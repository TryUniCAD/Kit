from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.SavedCameras.CamFieldKeys import CamFieldKeys


# view records compare in owner order so detached or aliased cameras cannot pass by value alone
def ReadCamViews(
    Bytes: bytes,
) -> tuple[tuple[str, bool, tuple[tuple[str, object], ...]], ...]:
    Graph = BuildGraph(ReadDocument(Bytes))
    (Settings,) = Graph.ByClass("CommonDataAssetSettings")
    (Roster,) = Graph.ByClass("NamedViews")
    assert ResolveField(Graph, Settings, "namedViews", "NamedViews") == Roster
    Views = LinkedNodes(Graph, Roster, "children")
    assert set(ViewNode.Identity for ViewNode in Views) == set(
        ViewNode.Identity for ViewNode in Graph.ByClass("NamedView")
    )
    Cameras: set[str] = set()
    Records: list[tuple[str, bool, tuple[tuple[str, object], ...]]] = []
    for ViewNode in Views:
        assert ResolveField(Graph, ViewNode, "rParent", "NamedViews") == Roster
        Camera = ResolveField(Graph, ViewNode, "m_rCamera", "Camera")
        assert Camera.Identity not in Cameras
        Cameras.add(Camera.Identity)
        ViewName, Modify = ViewNode.Fields["m_name"], ViewNode.Fields["m_bEnableModify"]
        assert isinstance(ViewName, str) and isinstance(Modify, bool)
        Records.append((ViewName, Modify, tuple(CamFieldKeys(Camera))))
    assert Cameras == {Camera.Identity for Camera in Graph.ByClass("Camera")}
    return tuple(Records)
