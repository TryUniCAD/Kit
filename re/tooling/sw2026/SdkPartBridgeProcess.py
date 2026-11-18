from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO, StringIO
import json
from math import isclose
from ntpath import basename
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartSettings import settings
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.PreparePart import PreparePart
from convert.api.ApiContext import GetRegistry
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentProvenance import HasProvenance
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentBoundary import GetDocument
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Records.RecordProvenance import Provenance
from interchange.serialization.Deserialize import FromData

REGISTRY = GetRegistry()
CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def malformed(document, recipe, target, options):
    name = basename(target)
    cases = (
        ("wrong_configuration", document, target, recipe, replace(options, configuration="missing")),
        ("assembly_format", document, target, recipe, replace(options, destination_format="solidworks.sldasm")),
        ("public_enable_knob", document, target, recipe, replace(options, values={"enable_writer": True})),
        ("wrong_overwrite_type", document, target, recipe, replace(options, overwrite=1)),
        ("wrong_policy_type", document, target, recipe, replace(options, values={"portable": "true"})),
        ("unnamed_stream", document, BytesIO(), recipe, WriteOptions()),
        ("text_stream", document, StringIO(), recipe, options),
        ("relative_path", document, name, recipe, WriteOptions()),
        ("unproven_host_locator", document, "/tmp/" + name, replace(recipe, OutputValue=SelfFileInput(r"C:\unproved namespace" + "\\" + name, recipe.OutputValue.SavedAt)), WriteOptions()),
        ("drive_relative_path", document, "C:" + name, recipe, WriteOptions()),
        ("assembly_suffix", document, target[:-7] + ".SLDASM", recipe, WriteOptions()),
        ("different_final_name", document, target, recipe, replace(options, values={"final_destination": r"C:\KitBridge\different.SLDPRT"})),
        ("different_model_name", document, r"C:\KitBridge\different.SLDPRT", recipe, WriteOptions()),
        ("windows_device", document, r"C:\KitBridge\con.SLDPRT", recipe, WriteOptions()),
        ("relative_segment", document, r"C:\KitBridge" + "\\..\\" + name, recipe, WriteOptions()),
        ("source_extensions", replace(document, source=replace(document.source, attributes={"unmapped": "authored extension"})), target, recipe, options),
        ("record_provenance", replace(document, feature_timeline=(replace(document.feature_timeline[0], provenance=Provenance("authored", "feature/boss")),)), target, recipe, options),
        ("supplied_topology", replace(document, bodies=(replace(document.bodies[0], topology=replace(document.bodies[0].topology, solid_count=1)),)), target, recipe, options),
        ("unknown_neutral_version", replace(document, schema_version="2.0"), target, recipe, options),
        ("nonplain_boss", replace(document, feature_timeline=(replace(document.feature_timeline[0], definition=replace(document.feature_timeline[0].definition, symmetric=True)),)), target, recipe, options),
        ("missing_recipe", document, target, None, options),
    )
    results = []
    for label, model, output, supplied, selected in cases:
        try:
            PreparePart(model, output, supplied, selected)
        except (ValueError, TypeError, KeyError) as error:
            results.append({"case": label, "rejected": True, "exception": type(error).__name__, "diagnostic": str(error)})
        else:
            raise ValueError("invalid adapter preparation accepted: " + label)
    return results


def public_reader(candidate):
    document = OpenDocument(candidate.BytesValue, SourceFormat="solidworks.sldprt", IncludeBrep=False, IncludeTess=False)
    bosses = [feature for feature in document.feature_timeline if feature.name == candidate.PlanValue.FeatureName]
    require(len(bosses) == 1 and type(bosses[0].definition) is ExtrudeFeature, "normal SDK read lost the actual blind boss")
    boss = bosses[0]
    sketches = [sketch for sketch in document.sketches if sketch.id == boss.sketch_id]
    require(len(sketches) == 1 and sketches[0].name == candidate.PlanValue.SketchName and len(sketches[0].entities) == 4,
            "normal SDK read lost the actual rectangle profile")
    parameters = [parameter for parameter in document.parameters if parameter.id in boss.parameter_ids and parameter.name == "D1"]
    require(len(parameters) == 1 and parameters[0].owner_id == boss.id and parameters[0].value == boss.definition.length,
            "normal SDK read lost driving parameter ownership")
    require(boss.definition.length.unit == "mm" and isclose(float(boss.definition.length.value) * 0.001, candidate.PlanValue.DepthValue, rel_tol=1e-12, abs_tol=0.0),
            "normal SDK read changed the actual driving depth")
    return {"boss_name": boss.name, "profile_name": sketches[0].name, "entity_count": len(sketches[0].entities),
            "driving_name": parameters[0].name, "driving_owner": True, "depth_m": candidate.PlanValue.DepthValue}


def main():
    document = FromData(REQUEST["document"])
    recipe = settings(REQUEST["settings"])
    final_path = recipe.OutputValue.PathName
    staged = "/unused/sdk-bridge-staging/" + basename(final_path)
    options = WriteOptions(configuration=document.configurations[0].id, destination_format="solidworks.sldprt",
                           values={"final_destination": final_path, "final_overwrite": True, "portable": True,
                                   "allow_carrier": False, "require_self_contained": True, "require_native_transfers": False, "allow_non_native": True})
    stale_recipe = replace(recipe, DocumentUnits=UnitInput("m", recipe.DocumentUnits.AngleUnit, "mks", recipe.DocumentUnits.DecimalPlaces),
                           SystemValue=replace(recipe.SystemValue, PlaneNames=tuple((axis, "stale support" if axis == "z" else name) for axis, name in recipe.SystemValue.PlaneNames)),
                           OutputValue=SelfFileInput(r"C:\unused recipe" + "\\" + basename(final_path), recipe.OutputValue.SavedAt))
    candidate = PreparePart(document, staged, stale_recipe, options)
    direct = MakeBlindPart(document, recipe)
    require(candidate.BytesValue == direct.BytesValue and candidate.StreamsValue == direct.StreamsValue,
            "internal adapter bridge changed the complete proven construction bytes")
    raw_options = WriteOptions(configuration=document.configurations[0].name, destination_format="sldprt", validate=False)
    direct_path = PreparePart(document, final_path, recipe, raw_options)
    memory = BytesIO()
    buffered = PreparePart(document, memory, recipe, options)
    require(direct_path.BytesValue == buffered.BytesValue == candidate.BytesValue and memory.getvalue() == b"",
            "preparation changed the byte contract or mutated a destination")
    file = candidate.HeaderValue.FieldsValue["f38"].FieldsValue["shared"]["h18"].FieldsValue["value"].TextValue
    require(file == final_path and file != staged, "native header published a temporary staging identity")
    adapter = REGISTRY.GetReader("solidworks.sldprt")
    require(not hasattr(adapter, "write") and not hasattr(adapter, "supports"), "read-only adapter acquired a write entry point")
    destination = BytesIO()
    try:
        WriteDocument(document, destination, DestFormat="solidworks.sldprt")
    except NotFoundError:
        pass
    else:
        raise ValueError("normal public save admitted an unqualified writer")
    require(destination.getvalue() == b"" and not any(value.info.format_id in ("solidworks.sldprt", "solidworks.sldasm", "solidworks.slddrw") for value in REGISTRY.GetWriters()),
            "normal writer discovery changed or public save mutated the destination")
    readback = public_reader(candidate)
    rejections = malformed(document, recipe, final_path, options)
    imported = sorted(name for name, module in tuple(sys.modules.items())
                      if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                      and name not in ("__main__", "SdkBlindPartSettings"))
    require(not imported, "SDK preparation imported research implementation")
    return {"passed": True, "scope": "unregistered ordinary WriteOptions to complete SDK-only plain part preparation",
            "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(), "blob": b64encode(candidate.BytesValue).decode("ascii"),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in candidate.StreamsValue.items()},
            "exact_direct_candidate": True, "exact_named_configuration": True, "exact_configuration_id": True,
            "derived_neutral_units_and_support": True, "encoded_final_path": final_path, "staging_path_not_encoded": True,
            "caller_destinations_unchanged": True, "public_writer_available": False, "public_save_rejected": True,
            "public_read": readback, "malformed": rejections,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imported),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
