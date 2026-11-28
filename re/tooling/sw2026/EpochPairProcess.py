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
from EpochClocks import ClockPlan, drawing_clocks, require
from EpochPart import make_epoch_child
from OriginChildShape import inspect_child
from OriginPairChecks import check_display
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginFile import MakeOriginFile
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def main():
    request = json.load(sys.stdin)
    require(type(request) is dict and set(request) == {
        "schema", "case", "origin_request", "clock_plan", "drawing_clock_plan", "changed_axis"}
        and request["schema"] == "kit.sw2026.sdk-epoch-pair-request.v1",
        "epoch process requires its complete declared neutral request")
    clocks = ClockPlan.from_data(request["clock_plan"])
    drawing_clocks(request["drawing_clock_plan"])
    job = request["origin_request"]
    require(set(job) == {"schema", "drawing_document", "native", "part", "support_names", "child_policy", "origin_display"}
            and job["schema"] == "kit.sw2026.sdk-origin-drawing-process.v1"
            and job["origin_display"] == {"selection": "actual-child-origin", "population_argument": 0}
            and type(job["origin_display"]["population_argument"]) is int,
            "epoch experiment preserves the existing actual-origin population route")
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    AUDIT.BeginBuild()
    child, settings, keys, composition = make_epoch_child(job, clocks)
    source_child = child.BytesValue
    native = linked_input({key: job[key] for key in ("schema", "drawing_document", "native", "part", "support_names")})
    candidate = MakeOriginFile(native, child)
    require(candidate.ChildValue is child and child.BytesValue == source_child
            and candidate.HeaderValue is candidate.ModelGraph.ModelValue.FieldsValue["fa8"],
            "epoch drawing lost the actual child or drawing header identity")
    reemitted, _, _ = EmitPartStreams(child.SystemValue, child.ResolvedValue.RootsValue,
                                     (child.HeaderValue, child.TopHeader, child.ManagerHeader),
                                     child.DefinitionValue, settings, child.PlanValue, keys)
    require(reemitted == child.StreamsValue, "epoch graph did not re-emit its independently modeled clocks")
    require(SldprtArchive.from_bytes(candidate.BytesValue).streams == candidate.StreamsValue
            and SldprtArchive.from_bytes(child.BytesValue).streams == child.StreamsValue,
            "epoch complete container framing differs")
    profile = check_display(candidate.UiGraph, child.ResolvedValue.RootsValue, child.HeaderValue)
    shape = inspect_child(child.ResolvedValue.RootsValue, "corner-anchored")
    require(not AUDIT.DeniedReads, "epoch construction attempted runtime input access")
    allowed = {"__main__", "EpochClocks", "EpochPart", "EpochText", "OriginPairChecks", "OriginChildShape",
               "DrawingSdkLinkedInput", "DrawingSdkInput", "SdkBlindPartSettings"}
    imports = sorted(name for name, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/") and name not in allowed)
    require(not imports, "epoch SDK construction loaded a research implementation: " + repr(imports))
    return {
        "schema": "kit.sw2026.sdk-epoch-pair-result.v1", "passed": True, "case": request["case"],
        "child_base64": b64encode(child.BytesValue).decode("ascii"),
        "child_sha256": sha256(child.BytesValue).hexdigest(), "child_bytes": len(child.BytesValue),
        "drawing_base64": b64encode(candidate.BytesValue).decode("ascii"),
        "drawing_sha256": sha256(candidate.BytesValue).hexdigest(), "drawing_bytes": len(candidate.BytesValue),
        "child_streams": {key: {"bytes": len(value), "sha256": sha256(value).hexdigest()} for key, value in child.StreamsValue.items()},
        "streams": {key: {"bytes": len(value), "sha256": sha256(value).hexdigest()} for key, value in candidate.StreamsValue.items()},
        "clock_plan": clocks.to_data(), "drawing_clock_plan": request["drawing_clock_plan"],
        "composition": composition, "profile": profile, "child_shape": shape,
        "orientation": native.DrawingValue.Sheets[0].Views[0].OrientationName,
        "native_child_path": native.DrawingValue.ModelRefs[0].SourcePath,
        "native_drawing_path": native.FileValue.PathName,
        "child_neutral": {"name": child.PlanValue.NameValue, "sketch_name": child.PlanValue.SketchName,
                          "feature_name": child.PlanValue.FeatureName, "configuration_name": child.PlanValue.ConfigName,
                          "driver_names": list(child.PlanValue.SketchDriverNames), "depth_name": child.PlanValue.DepthName,
                          "vertices_m": child.PlanValue.VerticesValue, "depth_m": child.PlanValue.DepthValue},
        "view_position_m": [native.DrawingValue.Sheets[0].Views[0].PositionValue.x, native.DrawingValue.Sheets[0].Views[0].PositionValue.y],
        "view_scale": native.DrawingValue.Sheets[0].Views[0].ScaleRatio,
        "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "sdk_research_imports": imports,
        "native_acceptance": False, "heldout_acceptance": False, "public_drawing_writer_enabled": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error),
                          "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "native_acceptance": False}))
        raise SystemExit(3)
