from __future__ import annotations

from base64 import b64encode
import codecs
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(TOOLS), str(TOOLS / "serial")]

from DrawingFrontBundleProcess import AUDIT, check_bundle, digest, require
from Classes import registry
from SheetWriteBridge import install_sheet_writer
from builders.DrawingDocument import construct_blank_drawing
from builders.DrawingFrontBundle import construct_front_bundle
from DrawingPublicScope import refuse_research_drawing
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Drawing.Definition.ReadConcept import ReadConcept
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinConcept import JoinConcept
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadOwnedNodes import ReadOwnedNodes
from convert.api import open_document


def sheet_projection(archive, request):
    model = ReadConcept(archive, 19000)
    sheet, = [node for node in ReadOwnedNodes(model) if node.ClassValue.NameValue == "moDrSheet"]
    fields = sheet.FieldsValue
    owned = ReadOwnedNodes(sheet)
    require(any(node is fields["f408"] for node in owned)
            and any(node is fields["f390"] for node in owned), "sheet writer lost a real inherited child alias")
    spec = request["drawing"] if "drawing" in request else request
    require(fields["f3f8"] == spec["sheet"]["scale_numerator"]
            and fields["f400"] == spec["sheet"]["scale_denominator"]
            and fields["f3e8"] == 8.5 * 0.0254 and fields["f3f0"] == 11 * 0.0254
            and fields["f3d0"] == spec["sheet"]["custom_property_view"]
            and fields["n_ink_views"] == 0 and fields["ink_views"] == (),
            "SDK sheet readback differs from its independent authored request")
    return {"class": sheet.ClassValue.NameValue, "width_m": fields["f3f0"], "height_m": fields["f3e8"],
            "scale": [fields["f3f8"], fields["f400"]], "property_view": fields["f3d0"],
            "profile_alias_preserved": True, "detail_folder_alias_preserved": True,
            "own_list_class": fields["f438"].ClassValue.NameValue}


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-sheet-writer-process.v1" and job["kind"] in ("blank", "front"),
            "sheet writer process job differs")
    require(job.get("qualification_probe") in (None, "archive_version", "archive_conditions", "runtime_schema",
            "annotation_presence", "annotation_marker", "ink_view", "missing_presence"), "unknown sheet writer qualification probe")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    normal, shared = registry(), registry()
    observations = []
    install_sheet_writer(shared, observations, job.get("qualification_probe"))
    AUDIT.BeginBuild()
    constructor = construct_blank_drawing if job["kind"] == "blank" else construct_front_bundle
    canonical = constructor(registry=normal, request=deepcopy(job["request"]))
    candidate = constructor(registry=shared, request=deepcopy(job["request"]))
    require(canonical.streams == candidate.streams, "SDK sheet field writer changed a generated logical stream")
    require(len(observations) == (1 if job["kind"] == "blank" else 2)
            and all(row["map_identity_preserved"] and not row["usage"]["native_byte_fields"]
                    and not row["usage"]["missing_schemas"] for row in observations),
            "SDK sheet field writer did not own every constructed sheet body")
    payload = build_sldprt(candidate.streams)
    archive = SldprtArchive.from_bytes(payload)
    report = sheet_projection(archive, job["request"])
    parsed = open_document(payload, source_format=KDrawingFormatId, strict=False)
    require(parsed.drawing is not None and len(parsed.drawing.Sheets) == 1, "public drawing reader lost the generated sheet")
    if job["kind"] == "front":
        require(canonical.part.streams == candidate.part.streams, "drawing sheet emission changed the independent child")
        child = build_sldprt(candidate.part.streams)
        report["front_bundle"] = check_bundle(drawing_data=payload, part_data=child, bundle=candidate,
                                               request=job["request"], rules=normal)
    public_refusals = refuse_research_drawing(parsed, linked=job["kind"] == "front")
    require(not AUDIT.DeniedReads, "SDK sheet writer attempted runtime input access")
    result = {"schema": "kit.sw2026.sdk-sheet-writer-result.v1", "kind": job["kind"], "passed": True,
              "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "public_reader_passed": True,
              "logical_streams_identical": True, "sheet": report, "sdk_write_observations": observations,
              "artifact_sha256": digest(payload), "artifact_bytes": len(payload),
              "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(candidate.streams.items())},
              "artifact_base64": b64encode(payload).decode("ascii"), "vendor_runtime_executed": False,
              "native_acceptance": False, "heldout_inputs_read": 0, "public_write_refusals": public_refusals}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
