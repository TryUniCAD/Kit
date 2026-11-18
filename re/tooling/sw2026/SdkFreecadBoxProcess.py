from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from ProjectFreecadBox import project
from SdkCornerChecks import corner
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange import CadDocument
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))


def build(request):
    if set(request) != {"document", "native_path"}:
        raise ValueError("FreeCAD box construction requires its neutral document and explicit native destination")
    document = FromData(request["document"])
    if type(document) is not CadDocument:
        raise TypeError("FreeCAD box construction requires an actual neutral document")
    projected = project(document)
    part = projected.model
    plan = ProjectRectDims(part)
    output = RequirePartPath(request["native_path"], projected.creation_epoch)
    recipe = MakePartRecipe(plan, projected.creation_epoch)
    settings = replace(BindPartIntent(part, plan, recipe, output), PropertiesValue=projected.properties)
    CheckPartInput(part, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    margin = min(plan.WidthValue, plan.HeightValue) / 4
    placement = RectDimInput((plan.WidthValue / 2, -margin),
                             (plan.WidthValue + margin, plan.HeightValue / 2), False, 1, False)
    dimensions = MakeRectDimsMut(profile, placement, allocator)
    MakeCornerMut(profile, system.OriginValue)
    anchor = corner(profile.ProfileValue, system.OriginValue.ProfileValue, system.RootValue, plan.VerticesValue, False)
    part_file = FinishBlindMut(system, profile, settings, plan, allocator,
                               MakeSketchKeys(dimensions, settings.DocumentUnits.LengthUnit))
    return {
        "passed": True,
        "native_acceptance": False,
        "public_writer_qualified": False,
        "source_sha256": document.source.sha256,
        "source_dimensions_mm": projected.dimensions_mm,
        "source_body_label": projected.source_body_label,
        "source_feature_label": projected.source_feature_label,
        "parameter_bindings": projected.parameter_bindings,
        "actual_native_body_label_plan": plan.FeatureName,
        "creation_epoch": projected.creation_epoch,
        "source_text": {"summary": projected.properties.SummaryFields, "file": projected.properties.DocumentFields},
        "geometry": projected.geometry,
        "origin_coincidence": anchor,
        "native_path": output.PathName,
        "bytes": len(part_file.BytesValue),
        "sha256": sha256(part_file.BytesValue).hexdigest(),
        "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
                    for name, data in part_file.StreamsValue.items()},
        "runtime_input_file_reads": len(AUDIT.DeniedReads),
        "blob": b64encode(part_file.BytesValue).decode("ascii"),
    }


if __name__ == "__main__":
    request = json.load(sys.stdin)
    AUDIT.BeginBuild()
    print(json.dumps(build(request), sort_keys=True, allow_nan=False))
