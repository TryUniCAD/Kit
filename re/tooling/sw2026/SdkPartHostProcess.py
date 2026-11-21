from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
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
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Core.Preparation.PreparePart import PreparePart
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def rejected(document, recipe, host):
    name = basename(recipe.OutputValue.PathName)
    cases = (
        ("unmeasured_locator_parent", document, host, replace(recipe, OutputValue=SelfFileInput(r"C:\unproved" + "\\" + name, recipe.OutputValue.SavedAt)), WriteOptions()),
        ("other_locator_basename", document, host, replace(recipe, OutputValue=SelfFileInput(r"C:\KitSdkCandidates\other.SLDPRT", recipe.OutputValue.SavedAt)), WriteOptions()),
        ("assembly_locator", document, host, replace(recipe, OutputValue=SelfFileInput(recipe.OutputValue.PathName[:-7] + ".SLDASM", recipe.OutputValue.SavedAt)), WriteOptions()),
        ("renamed_host_target", document, "/tmp/other.SLDPRT", recipe, WriteOptions()),
        ("case_changed_neutral_basename", document, "/tmp/" + name.upper(), recipe, WriteOptions()),
        ("relative_host_target", document, "relative/" + name, recipe, WriteOptions()),
        ("host_parent_traversal", document, "/tmp/../" + name, recipe, WriteOptions()),
        ("unnamed_memory_target", document, BytesIO(), recipe, WriteOptions()),
        ("linked_option", document, host, recipe, WriteOptions(values={"linked": True})),
        ("bundle_option", document, host, recipe, WriteOptions(values={"component_documents": {}})),
        ("multiple_bodies", replace(document, bodies=(*document.bodies, replace(document.bodies[0], id="body/second", name="second"))), host, recipe, WriteOptions()),
        ("additional_configuration", replace(document, configurations=(*document.configurations, replace(document.configurations[0], id="configuration/second", name="second", active=False))), host, recipe, WriteOptions()),
        ("external_support", replace(document, support_planes=(replace(document.support_planes[0], support_selection_id="external/face"),)), host, recipe, WriteOptions()),
    )
    rows = []
    for label, model, target, supplied, options in cases:
        try:
            PreparePart(model, target, supplied, options)
        except (ValueError, TypeError, KeyError) as error:
            rows.append({"case": label, "rejected": True, "exception": type(error).__name__, "diagnostic": str(error)})
        else:
            raise ValueError("unsupported standalone host preparation accepted: " + label)
    return rows


def main():
    document = FromData(REQUEST["document"])
    recipe = settings(REQUEST["settings"])
    filename = basename(recipe.OutputValue.PathName)
    final_path = "/tmp/kit-standalone-host/" + filename
    staged_path = "/unused/kit-host-staging/" + filename
    options = WriteOptions(configuration=document.configurations[0].id, destination_format="solidworks.sldprt", values={"final_destination": final_path})
    candidate = PreparePart(document, staged_path, recipe, options)
    baseline = MakeBlindPart(document, recipe)
    require(candidate.BytesValue == baseline.BytesValue and candidate.StreamsValue == baseline.StreamsValue,
            "standalone host preparation changed the complete explicit locator candidate")
    direct = PreparePart(document, final_path, recipe)
    memory = BytesIO()
    buffered = PreparePart(document, memory, recipe, options)
    windows = PreparePart(document, recipe.OutputValue.PathName, recipe)
    require(direct.BytesValue == buffered.BytesValue == windows.BytesValue == candidate.BytesValue and memory.getvalue() == b"",
            "host staging direct binary and Windows preparations changed bytes or mutated the sink")
    locator = candidate.HeaderValue.FieldsValue["f38"].FieldsValue["shared"]["h18"].FieldsValue["value"].TextValue
    require(locator == recipe.OutputValue.PathName and locator not in (final_path, staged_path),
            "neutral native self locator was confused with a host output path")
    failures = rejected(document, recipe, final_path)
    imported = sorted(name for name, module in tuple(sys.modules.items())
                      if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/") and name not in ("__main__", "SdkBlindPartSettings"))
    require(not imported, "standalone host preparation imported research implementation")
    return {"passed": True, "scope": "standalone absolute POSIX final destination with an authored neutral self locator",
            "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(), "blob": b64encode(candidate.BytesValue).decode("ascii"),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in candidate.StreamsValue.items()},
            "final_host_path": final_path, "native_self_locator": locator, "neutral_name": candidate.PlanValue.NameValue,
            "exact_basename": True, "exact_direct_candidate": True, "windows_bytes_preserved": True,
            "staging_and_memory_bytes_equal": True, "memory_sink_unchanged": True, "no_filesystem_mapping_claim": True,
            "depth_m": candidate.PlanValue.DepthValue, "vertices_m": candidate.PlanValue.VerticesValue,
            "malformed": failures, "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imported),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
