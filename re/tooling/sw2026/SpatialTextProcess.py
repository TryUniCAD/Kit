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
from OriginPairChecks import check_display
from SpatialTextMut import compose_text_mut, require
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginFile import MakeOriginFile
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def main():
    request = json.load(sys.stdin)
    require(set(request) == {"schema", "origin_request", "text_points_xyz_m"}
            and request["schema"] == "kit.sw2026.spatial-text-request.v1", "spatial text request differs")
    job = request["origin_request"]
    require(set(job) == {"schema", "drawing_document", "native", "part", "support_names", "child_policy", "origin_display"}
            and job["schema"] == "kit.sw2026.sdk-origin-drawing-process.v1", "spatial text needs the complete qualified origin request")
    require(job["origin_display"] == {"selection": "actual-child-origin", "population_argument": 0}
            and type(job["origin_display"]["population_argument"]) is int,
            "spatial text preserves the actual ordinary origin display operation")
    for name in ("utf-16-le", "utf-8", "latin-1"):
        lookup(name)
    AUDIT.BeginBuild()
    baseline, settings, keys = make_child(job)
    child, before, after, changed = compose_text_mut(baseline, settings, keys, request["text_points_xyz_m"])
    native = linked_input({name: job[name] for name in set(job) - {"child_policy", "origin_display"}})
    pair = MakeOriginFile(native, child)
    loaded = ReadNamedDef(pair.StreamsValue["Contents/Definition"], 19000,
                          native.DrawingValue.Sheets[0].Views[0].OrientationName)
    require(WriteNamedDef(loaded.GraphValue).OutputValue == pair.StreamsValue["Contents/Definition"],
            "spatial text drawing Definition did not replay exactly")
    profile = check_display(pair.UiGraph, child.ResolvedValue.RootsValue, child.HeaderValue)
    require(profile == check_display(loaded.GraphValue, child.ResolvedValue.RootsValue, child.HeaderValue),
            "spatial text drawing lost its real child origin or component aliases")
    shape = inspect_child(child.ResolvedValue.RootsValue, job["child_policy"]["kind"])
    imports = sorted(name for name, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in {"__main__", "SpatialTextMut", "OriginPairChild", "OriginPairChecks", "OriginChildShape",
                                      "DrawingSdkLinkedInput", "DrawingSdkInput", "SdkBlindPartSettings"})
    require(not AUDIT.DeniedReads and not imports, "spatial text construction crossed its input or implementation boundary")
    return {"schema": "kit.sw2026.spatial-text-result.v1", "passed": True,
            "child_base64": b64encode(child.BytesValue).decode("ascii"),
            "drawing_base64": b64encode(pair.BytesValue).decode("ascii"),
            "child_sha256": sha256(child.BytesValue).hexdigest(), "child_bytes": len(child.BytesValue),
            "drawing_sha256": sha256(pair.BytesValue).hexdigest(), "drawing_bytes": len(pair.BytesValue),
            "baseline_child_sha256": sha256(baseline.BytesValue).hexdigest(),
            "text_before": before, "text_after": after, "changed_child_streams": changed,
            "child_shape": shape, "profile": profile,
            "orientation": native.DrawingValue.Sheets[0].Views[0].OrientationName,
            "native_child_path": native.DrawingValue.ModelRefs[0].SourcePath,
            "native_drawing_path": native.FileValue.PathName,
            "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "sdk_research_imports": imports,
            "source_original_admission": False, "native_acceptance": False, "heldout_acceptance": False,
            "public_drawing_writer_enabled": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error),
                          "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "native_acceptance": False}))
        raise SystemExit(3)
