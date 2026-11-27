from pathlib import Path as FilePath

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# encoded counterexamples must challenge ownership and saved geometry through real archive reads
def ChangeOffset(Source: FilePath, Target: FilePath, CaseName: str) -> None:
    Model = ReadDocument(Source.read_bytes())
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Binding = Graph.Resolve(Context.Extrude.Fields["profileOffset"])
    Parameter = Graph.Resolve(Binding.Fields["parameter"])
    Cases: dict[str, tuple[NativeNode, str, KEntityValue]] = {
        "start_kind": (Context.Extrude, "profileLocaltionType", 0),
        "entity_start": (Context.Extrude, "profileLocaltionType", 2),
        "missing_offset": (Context.Extrude, "profileOffset", None),
        "wrong_role": (
            Context.Extrude,
            "profileOffset",
            Context.Extrude.Fields["rTaperAngle"],
        ),
        "owner": (Binding, "rrOwnerFeature", Context.Sketch.Fields["rDcNode"]),
        "parent": (Binding, "rParentFeature", Context.Sketch.Fields["rDcNode"]),
        "reciprocal": (Parameter, "dcParameter", Context.Extrude.Fields["rTaperAngle"]),
        "allocator": (Binding, "rparamId", Context.Along.Fields["rparamId"]),
        "units": (Parameter, "unit", "deg"),
        "native_name": (Parameter, "name", "AlongDistance"),
        "value_copy": (Binding, "value", 1.1),
        "nonfinite": (Binding, "value", float("inf")),
        "taper": (Context.Taper, "value", 0.1),
    }
    NodeValue, FieldName, FieldValue = Cases[CaseName]
    Changed = ChangeField(Model, NodeValue.ObjectId, FieldName, FieldValue)
    _ = Target.write_bytes(EmitParsed(Changed))
