from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json

from DrawingSdkLinkedInput import linked_input
from OriginPairChild import make_child
from OriginChildShape import inspect_child
from OriginPairChecks import check_display, require
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Construction.Linked.MakeLinkedFile import MakeLinkedFile
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginFile import MakeOriginFile
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def main():
    job = json.load(sys.stdin)
    keys = {"schema", "drawing_document", "native", "part", "support_names", "child_policy", "origin_display"}
    require(set(job) == keys and job["schema"] == "kit.sw2026.sdk-origin-drawing-process.v1", "origin pair job differs")
    require(job["origin_display"] == {"selection": "actual-child-origin", "population_argument": 0}
            and type(job["origin_display"]["population_argument"]) is int, "origin pair requires explicit ordinary population of the actual child origin")
    for name in ("utf-16-le", "utf-8", "latin-1"):
        lookup(name)
    AUDIT.BeginBuild()
    child, settings, child_keys = make_child(job)
    original_child = child.BytesValue
    native = linked_input({name: job[name] for name in keys - {"child_policy", "origin_display"}})
    baseline = MakeLinkedFile(native, child)
    candidate = MakeOriginFile(native, child)
    require(candidate.ChildValue is child and candidate.HeaderValue is candidate.ModelGraph.ModelValue.FieldsValue["fa8"],
            "origin pair lost actual generated child or header identity")
    changed = [name for name in candidate.StreamsValue if candidate.StreamsValue[name] != baseline.StreamsValue[name]]
    require(changed == ["Contents/Definition"], "origin pair changed unrelated default streams")
    require(child.BytesValue == original_child and candidate.ModelGraph.Allocator.NextValue == baseline.ModelGraph.Allocator.NextValue,
            "origin pair mutated child bytes or persistent feature allocation")
    orientation = native.DrawingValue.Sheets[0].Views[0].OrientationName
    loaded = ReadNamedDef(candidate.StreamsValue["Contents/Definition"], 19000, orientation)
    require(WriteNamedDef(loaded.GraphValue).OutputValue == candidate.StreamsValue["Contents/Definition"], "origin Definition byte round trip differs")
    require(SldprtArchive.from_bytes(candidate.BytesValue).streams == candidate.StreamsValue, "origin pair container differs")
    reemitted, _, _ = EmitPartStreams(child.SystemValue, child.ResolvedValue.RootsValue,
                                    (child.HeaderValue, child.TopHeader, child.ManagerHeader), child.DefinitionValue,
                                    settings, child.PlanValue,
                                    child_keys)
    require(reemitted == child.StreamsValue, "origin drawing mutated its actual dimensioned child graph")
    require(not AUDIT.DeniedReads, "origin pair attempted runtime input access")
    generated = check_display(candidate.UiGraph, child.ResolvedValue.RootsValue, child.HeaderValue)
    loaded_row = check_display(loaded.GraphValue, child.ResolvedValue.RootsValue, child.HeaderValue)
    child_shape = inspect_child(child.ResolvedValue.RootsValue, job["child_policy"]["kind"])
    require(generated == loaded_row and "drawing.profile_displays" in loaded.Unprojected, "origin display retention or explicit projection boundary differs")
    imports = sorted(name for name, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in ("__main__", "OriginPairChild", "OriginPairChecks", "OriginChildShape", "DrawingSdkLinkedInput", "DrawingSdkInput", "SdkBlindPartSettings"))
    require(not imports, "SDK origin construction loaded research implementation: " + repr(imports))
    return {"schema": "kit.sw2026.sdk-origin-drawing-result.v1", "passed": True,
            "drawing_sha256": sha256(candidate.BytesValue).hexdigest(), "drawing_bytes": len(candidate.BytesValue),
            "drawing_base64": b64encode(candidate.BytesValue).decode("ascii"),
            "child_sha256": sha256(child.BytesValue).hexdigest(), "child_bytes": len(child.BytesValue),
            "child_base64": b64encode(child.BytesValue).decode("ascii"),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in candidate.StreamsValue.items()},
            "changed_default_streams": changed, "child_graph_and_bytes_unchanged": child.BytesValue == original_child,
            "profile": generated, "orientation": orientation, "child_shape": child_shape,
            "native_child_path": native.DrawingValue.ModelRefs[0].SourcePath, "native_drawing_path": native.FileValue.PathName,
            "child_neutral": {"name": child.PlanValue.NameValue, "sketch_name": child.PlanValue.SketchName,
                              "feature_name": child.PlanValue.FeatureName, "configuration_name": child.PlanValue.ConfigName,
                              "driver_names": list(child.PlanValue.SketchDriverNames), "depth_name": child.PlanValue.DepthName,
                              "vertices_m": child.PlanValue.VerticesValue, "depth_m": child.PlanValue.DepthValue},
            "view_position_m": [native.DrawingValue.Sheets[0].Views[0].PositionValue.x, native.DrawingValue.Sheets[0].Views[0].PositionValue.y],
            "view_scale": native.DrawingValue.Sheets[0].Views[0].ScaleRatio,
            "body_count": 1, "child_full_constraint_expected": True,
            "population_argument": 0,
            "definition_map_next": loaded.MapValue.CounterValue, "persistent_next": candidate.ModelGraph.Allocator.NextValue,
            "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "sdk_research_imports": imports,
            "complete_typed_roundtrip": True, "origin_display_unprojected": True,
            "native_acceptance": False, "heldout_acceptance": False, "public_drawing_writer_enabled": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error),
                          "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "native_acceptance": False}))
        raise SystemExit(3)
