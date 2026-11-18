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

from SdkBlindPartChecks import require
from SdkBlindPartSettings import settings
from SdkCornerChecks import corner
from SdkCornerRejects import malformed
from SdkRectDimRejects import input_value
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
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
    require(type(document) is CadDocument, "corner process requires an actual serialized neutral document")
    inputs = settings(REQUEST["settings"])
    plan = ProjectRectDims(document)
    CheckPartInput(document, inputs, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(inputs, plan, allocator)
    profile = MakePartProfMut(system, inputs, plan, allocator)
    dimensions = MakeRectDimsMut(profile, input_value(REQUEST["rectangle_dimensions"], inputs), allocator)
    anchor = MakeCornerMut(profile, system.OriginValue)
    require(anchor.PointValues[:4] == profile.GeometryValue.PointValues,
            "external point must not become an extra neutral contour vertex")
    candidate = FinishBlindMut(system, profile, inputs, plan, allocator,
                              MakeSketchKeys(dimensions, inputs.DocumentUnits.LengthUnit))
    checked = corner(profile.ProfileValue, system.OriginValue.ProfileValue, system.RootValue, plan.VerticesValue, False)
    require(candidate.HeaderValue.FieldsValue["f08"] == 27 and len(candidate.ResolvedValue.RootsValue) == 19,
            "the inline anchor must not consume model feature or dimension identities")
    imports = sorted(name for name, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/") and
                     name not in ("__main__", "SdkBlindPartChecks", "SdkBlindPartSettings", "SdkCornerChecks", "SdkCornerRejects", "SdkRectDimRejects"))
    require(not imports, "SDK construction imported research implementation: " + repr(imports))
    width, height, depth = plan.WidthValue, plan.HeightValue, plan.DepthValue
    return {"passed": True, "scope": "sdk dimensioned positive origin rectangle with actual native external origin coincidence",
            "name": plan.NameValue, "native_path": inputs.OutputValue.PathName, "next_id": candidate.HeaderValue.FieldsValue["f08"],
            "feature_count": len(candidate.ResolvedValue.RootsValue), "vertices_m": plan.VerticesValue, "depth_m": depth,
            "anchor": checked, "rejections": malformed(document, inputs, REQUEST["rectangle_dimensions"]),
            "config_map_counter": candidate.ConfigValue.MapValue.CounterValue,
            "resolved_map_counter": candidate.ResolvedValue.MapValue.CounterValue,
            "usage": {"config": candidate.ConfigValue.ReportValue, "resolved": candidate.ResolvedValue.ReportValue},
            "analytic_geometry": {"body_count": 1, "volume_m3": width * height * depth,
                                  "area_m2": 2 * (width * height + width * depth + height * depth),
                                  "com_m": [width / 2, height / 2, depth / 2], "bounds_m": [[0.0, 0.0, 0.0], [width, height, depth]]},
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")}
                        for name, data in candidate.StreamsValue.items()},
            "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(),
            "blob": b64encode(candidate.BytesValue).decode("ascii"), "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "sdk_runtime_research_imports": len(imports), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
