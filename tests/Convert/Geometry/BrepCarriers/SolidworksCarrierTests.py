from itertools import combinations as Combinations, product as Product
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import approx as Approx

from convert.adapters.solidworks.Core.Adapter import ReadSldprt
from interchange.brep.Curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel

# the committed native files and their measurements must come from the same checkout
KResearch = FilePath(__file__).resolve().parents[4] / "re"


# axis aligned supports and trimmed endpoints are independent consequences of the measured box dimensions
def TestBoxCarriers() -> None:
    Folder = KResearch / "solidworks/FeatureLadderRecovery/Cases/solidworks-059"
    Evidence = LoadJson((Folder / "GroundTruth.json").read_text(encoding="utf-8"))
    for CaseRow in Evidence["cases"][:2]:
        SizeData = CaseRow["parameters_mm"]
        Bounds = (
            (0.0, SizeData["width"]),
            (0.0, SizeData["height"]),
            (-SizeData["depth"], 0.0),
        )
        Model = ReadSldprt(Folder / f"{CaseRow['case']}.SLDPRT").brep
        assert Model is not None
        assert (len(Model.faces), len(Model.edges)) == (6, 12)
        Planes = {Surface.id: Surface for Surface in Model.surfaces}
        Supports: set[tuple[int, float]] = set()
        for FaceValue in Model.faces:
            Surface = Planes[FaceValue.surface_id]
            assert isinstance(Surface, PlaneSurface)
            Normal = (Surface.normal.x, Surface.normal.y, Surface.normal.z)
            Origin = (Surface.origin.x, Surface.origin.y, Surface.origin.z)
            AxisIndex = max(range(3), key=Normal.__getitem__)
            if Normal[AxisIndex] == 0.0:
                AxisIndex = min(range(3), key=Normal.__getitem__)
            assert abs(Normal[AxisIndex]) == 1.0 and sum(map(abs, Normal)) == 1.0
            Supports.add((AxisIndex, Origin[AxisIndex]))
        assert Supports == {
            (AxisIndex, Limit)
            for AxisIndex, Limits in enumerate(Bounds)
            for Limit in Limits
        }
        VerifyBoxEdges(Model, Bounds)


# each trimmed line must evaluate to the actual vertices of a distinct measured box edge
def VerifyBoxEdges(Model: BrepModel, Bounds: tuple[tuple[float, float], ...]) -> None:
    Curves = {Curve.id: Curve for Curve in Model.curves}
    Vertices = {Vertex.id: Vertex.point for Vertex in Model.vertices}
    Edges: set[frozenset[tuple[float, float, float]]] = set()
    for EdgeValue in Model.edges:
        Curve = Curves[EdgeValue.curve_id]
        assert isinstance(Curve, LineCurve)
        Points: list[tuple[float, float, float]] = []
        for VertexId, Parameter in (
            (EdgeValue.start_vertex_id, EdgeValue.start_parameter),
            (EdgeValue.end_vertex_id, EdgeValue.end_parameter),
        ):
            Vertex = Vertices[VertexId]
            assert Parameter is not None
            Point = (Vertex.x, Vertex.y, Vertex.z)
            assert Point == Approx(
                (
                    Curve.origin.x + Parameter * Curve.direction.x,
                    Curve.origin.y + Parameter * Curve.direction.y,
                    Curve.origin.z + Parameter * Curve.direction.z,
                )
            )
            Points.append(Point)
        Edges.add(frozenset(Points))
    assert Edges == {
        frozenset((First, Second))
        for First, Second in Combinations(Product(*Bounds), 2)
        if sum(
            FirstValue != SecondValue
            for FirstValue, SecondValue in zip(First, Second, strict=True)
        )
        == 1
    }


# the independent radius edit must move both the cylindrical wall and its two circular boundaries
def TestRoundShapes() -> None:
    Folder = KResearch / "automation/PairedCaptures/P05/solidworks-c3d4361662e0"
    Evidence = LoadJson((Folder / "measurements.json").read_text(encoding="utf-8"))
    for EditedRow in Evidence["observations"]["edits"]:
        if EditedRow["parameter"] == "outer_radius_mm":
            break
    else:
        raise AssertionError("missing outer radius measurement")
    Dimensions = {
        Dimension["name"]: Dimension["system_value"] * 1000
        for Feature in EditedRow["edited"]["feature_tree"]
        for Dimension in Feature["dimensions"]
    }
    Inner = Dimensions["inner_radius_mm"]
    Outer = Dimensions["outer_radius_mm"]
    Height = Dimensions["height_mm"]
    Model = ReadSldprt(Folder / EditedRow["saved_file"]).brep
    assert Model is not None
    assert (len(Model.faces), len(Model.edges)) == (4, 4)
    assert all(isinstance(Curve, CircleCurve) for Curve in Model.curves)
    Circles = tuple(Curve for Curve in Model.curves if isinstance(Curve, CircleCurve))
    assert sorted(Curve.radius for Curve in Circles) == Approx(
        [Inner, Inner, Outer, Outer]
    )
    assert sorted(Curve.center.z for Curve in Circles) == Approx([0, 0, Height, Height])
    Cylinders = tuple(
        Surface for Surface in Model.surfaces if isinstance(Surface, CylinderSurface)
    )
    assert sorted(Surface.radius for Surface in Cylinders) == Approx([Inner, Outer])
    RoundShapes: tuple[CircleCurve | CylinderSurface, ...] = (*Circles, *Cylinders)
    for Carrier in RoundShapes:
        assert (Carrier.axis.x, Carrier.axis.y, abs(Carrier.axis.z)) == Approx(
            (0, 0, 1)
        )
