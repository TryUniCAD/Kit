from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartSettings import settings
from SdkBlindPartChecks import geometry, node, require
from SdkRectDimChecks import dimensions
from SdkRectDimRejects import input_value, malformed
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def main():
    document = FromData(REQUEST["document"])
    require(type(document) is CadDocument, "process must receive an actual serialized neutral document")
    inputs = settings(REQUEST["settings"])
    candidate = MakeRectDimPart(document, inputs, input_value(REQUEST["rectangle_dimensions"], inputs))
    profile, sketch = candidate.ProfileValue.ProfileValue, candidate.ProfileValue.GeometryValue.SketchValue
    ids = [row["d"].FieldsValue["f50"] for row in sketch.FieldsValue["dims"]["val_g2"]]
    require(candidate.ConfigValue.RootValue is candidate.SystemValue.RootValue and
            candidate.ResolvedValue.RootsValue[-2] is profile and
            candidate.ResolvedValue.RootsValue[-1] is candidate.BossValue.FeatureValue,
            "complete dimensioned part lost its actual linked graph roots")
    require(candidate.BossValue.FeatureValue.FieldsValue["f60"]["list"]["items"][0]["o"] is profile,
            "boss lost the actual dimensioned profile dependency")
    checked = dimensions(profile, candidate.SystemValue.RootValue, candidate.PlanValue.VerticesValue,
                         ids, REQUEST["rectangle_dimensions"], False)
    boss_dimensions = (*candidate.BossValue.DimensionsValue, candidate.BossValue.FromValue)
    boss_ids = [graph.DimensionValue.FieldsValue["f50"] for graph in boss_dimensions]
    require(len(set((*ids, *boss_ids))) == 7 and ids == [19, 20] and boss_ids == [22, 23, 24, 25, 26],
            "sketch drivers did not allocate before boss feature and retained dimension identities")
    require(candidate.HeaderValue.FieldsValue["f08"] == 27, "complete allocator did not retain seven dimensions and one later boss feature")
    require(candidate.SystemValue.RootValue.FieldsValue["fd44"] == 12, "dimension display allocation changed during boss construction")
    require(candidate.CurrentConfig is candidate.SystemValue.ManagerValue.FieldsValue["f360"], "active configuration alias differs")
    imports = sorted(name for name, module in tuple(sys.modules.items())
        if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
        and name not in ("__main__", "SdkBlindPartSettings", "SdkBlindPartChecks", "SdkRectDimChecks", "SdkRectDimRejects"))
    require(not imports, "SDK-only rectangle dimension construction imported research implementation: " + repr(imports))
    plan = candidate.PlanValue
    width, height, depth = plan.WidthValue, plan.HeightValue, plan.DepthValue
    return {"passed": True, "scope": "complete sdk neutral rectangle with real horizontal vertical and point distance drivers before blind boss",
            "name": plan.NameValue, "native_path": inputs.OutputValue.PathName, "root_id": candidate.SystemValue.RootValue.FieldsValue["f08"],
            "next_id": candidate.HeaderValue.FieldsValue["f08"], "feature_count": len(candidate.ResolvedValue.RootsValue),
            "dimension_ids": ids, "boss_dimension_ids": boss_ids, "sketch_dimensions": checked,
            "depth_m": depth, "vertices_m": plan.VerticesValue,
            "analytic_geometry": {"body_count": 1, "volume_m3": width * height * depth,
                "area_m2": 2 * (width * height + width * depth + height * depth),
                "com_m": [sum(point[axis] for point in plan.VerticesValue) / 4 for axis in (0, 1)] + [depth / 2]},
            "actual_model_alias": True, "actual_profile_dependency": True,
            "config_map_counter": candidate.ConfigValue.MapValue.CounterValue, "resolved_map_counter": candidate.ResolvedValue.MapValue.CounterValue,
            "usage": {"config": candidate.ConfigValue.ReportValue, "resolved": candidate.ResolvedValue.ReportValue},
            "malformed": malformed(document, inputs, REQUEST["rectangle_dimensions"]),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in candidate.StreamsValue.items()},
            "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(), "blob": b64encode(candidate.BytesValue).decode("ascii"),
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
