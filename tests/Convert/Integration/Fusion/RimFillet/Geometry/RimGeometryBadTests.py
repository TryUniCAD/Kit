from pathlib import Path

from pytest import mark as MarkTests, raises as RaisesError

from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimLive import CheckRimLive
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimSnaps import (
    CheckRimSnaps,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from tests.Convert.Integration.Fusion.RimFillet.Geometry.ChangeRimModel import (
    ChangeRimModel,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)


# complete emitted and parsed native corruptions must fail the geometry or saved predecessor boundary
@MarkTests.parametrize(
    "CaseName",
    (
        "torus_major",
        "torus_minor",
        "torus_center",
        "top_winding",
        "seam_parameter",
        "tracker_owner",
        "snapshot_height",
        "history_end",
        "history_scale",
        "selected_lower",
        "adjacent_faces",
        "body_clock",
        "blend_operation",
        "bottom_source",
        "attribute_cycle",
    ),
)
def CheckBadRimGeo(TmpPath: Path, CaseName: str) -> None:
    Sample = next(
        Value for Value in ReadPolicyCases() if Value.CaseName == "source-discovery-01"
    )
    Model = ReadDocument(Sample.Source.read_bytes())
    Payload = EmitParsed(ChangeRimModel(Model, CaseName))
    Target = TmpPath / "MalformedRim.f3d"
    _ = Target.write_bytes(Payload)
    Model = ReadDocument(Target.read_bytes())
    Graph = BuildGraph(Model)
    Context = ReadRimContext(Graph)
    Shape = ReadCircle(Graph, Context.Extrusion)
    with RaisesError(ValueError):
        Prior, _ = CheckRimLive(Model, Graph, Context, Shape)
        CheckRimSnaps(Model, Graph, Context, Shape, Prior)
