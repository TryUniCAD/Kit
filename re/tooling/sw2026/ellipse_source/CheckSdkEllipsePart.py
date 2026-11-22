from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import cos, dist, radians, sin
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import Element, fromstring
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent)]
from CheckScopedPlainWriter import WriterAudit
from ColdEllipseModel import make_document
from EllipseMeasuredReceipt import NATIVE_SHA, TRIAL_SHA, load_phase, load_pin, normalize
from EllipseModel import predict, require
from VerifyEllipseBoundary import check_measures
from convert import open_document, write_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileMut import MakeProfileMut
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import PolygonInput
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Container.Format import KeywordsStream, KResolvedFeaturesStream
from convert.adapters.solidworks.Core.Adapter import DecodePartModel, SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import PrepareEllipse
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.GeometryConics import EllipseGeometry

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
RECEIPT_SHA = "e590ced10e6286c0637ea9b1bf9b8f44d041ef1b9aab454d61af0d99ec2066e3"


def digest(raw):
    return sha256(raw).hexdigest()


def reject(action, why, error_type=ValueError):
    try:
        action()
    except error_type as exc:
        require(why in str(exc), f"unexpected refusal {exc}")
    else:
        raise ValueError("unexpected admission: " + why)


def warm_imports():
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for encoding in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)


def check_semantics(model, case, with_brep):
    restored = CadDocument.from_json(model.to_json())
    require(restored.to_json() == model.to_json() and not restored.validate()
            and (model.brep is not None) == with_brep and not model.brep_payloads and not model.diagnostics,
            "strict neutral round trip, geometry option or diagnostics differ")
    feature, = (row for row in model.feature_timeline if row.kind == FeatureKind.KExtrusion)
    sketch, = model.sketches
    entity, = sketch.entities
    driver, = model.parameters
    body, = model.bodies
    geometry = entity.geometry
    require(type(geometry) is EllipseGeometry and not entity.construction and not entity.fixed
            and sketch.closed_profile_entity_ids == ((entity.id,),) and not sketch.constraints
            and not sketch.parameter_ids and sketch.attributes["ellipse_point_ids"] == (2, 1, 3, 4, 5, 6)
            and len(entity.provenance.spans) == 1, "ellipse conic or mapped seam owners differ")
    actual = ((geometry.center.x, geometry.center.y), (geometry.major_axis.x, geometry.major_axis.y),
              (geometry.major_radius, geometry.minor_radius))
    expected = (case["center_mm"], predict(case)["unit_axes"][0][:2], case["radii_mm"])
    require(all(dist(left, right) < 1e-11 for left, right in zip(actual, expected, strict=True)),
            "ellipse angles or dimensions differ from independent intent")
    require(type(feature.definition) is ExtrudeFeature and feature.definition.end_condition == ExtrudeEnd.KBlind
            and not feature.definition.reversed and feature.definition.second_length is None
            and feature.operation == BooleanOp.KCreate and feature.sketch_id == sketch.id
            and feature.parameter_ids == (driver.id,) and feature.definition.length == driver.value
            and (driver.name, driver.role, driver.owner_id) == ("D1", ParameterRole.KDriving, feature.id)
            and driver.attributes["typed_archive_owner"]["slot"] == "f818.f18"
            and driver.value.value == case["depth_mm"]
            and body.final_feature_id == feature.id and body.name == feature.name == "EllipseBoss"
            and len(model.feature_timeline) == 19
            and next(plane.name for plane in model.support_planes if plane.id == sketch.support_plane_id) == "Front Plane",
            "ordinary support, boss, solid or physical D1 owner differs")


def public_write(document, sink, values):
    return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=values)


def direct_write(document, sink, values):
    return SldprtWriter().write(document, sink, WriteOptions(values=values))


def write_refusals(emit, document, values, slot):
    envelope = values[OPTION]
    wrong_build, bad_control, wrong_path = (deepcopy(envelope) for _ in range(3))
    wrong_build["receipt"]["oracle"]["build"] = "other"
    bad_control["receipt"]["phases"][0]["passed"] = False
    wrong_path["receipt"]["cases"][slot]["locator"] = "wrong"
    length, = document.parameters
    feature, = document.feature_timeline
    depth = replace(length.value, value=length.value.value + 1)
    changed = replace(document, parameters=(replace(length, value=depth),),
                      feature_timeline=(replace(feature, definition=replace(feature.definition, length=depth)),))
    variants = {
        "absent_measurement": (document, {"final_destination": values["final_destination"]}, "offline native measurement"),
        "wrong_epoch": (document, values | {OPTION: envelope | {"written_at": envelope["written_at"] + 1}}, "no unique exact native measurement"),
        "unmeasured_locator": (document, values | {"final_destination": f"C:\\Unmeasured\\{document.metadata['name']}.SLDPRT"}, "no unique exact native measurement"),
        "wrong_oracle": (document, values | {OPTION: wrong_build}, "exact passing SOLIDWORKS"),
        "unhealthy_control": (document, values | {OPTION: bad_control}, "failed or unowned native phase"),
        "unbound_receipt_locator": (document, values | {OPTION: wrong_path}, "generated scope or locator"),
        "unmeasured_geometry": (changed, values, "no unique exact native measurement"),
    }
    for field in ("volume_m3", "area_m2", "com_m"):
        wrong = deepcopy(envelope)
        cases = wrong["receipt"]["cases"]
        cases[slot]["states"][0][field] = cases[1 - slot]["states"][0][field]
        variants["foreign_initial_" + field] = document, values | {OPTION: wrong}, "disagrees with the generated swept solid"
    edited_pair = deepcopy(envelope)
    for record in edited_pair["receipt"]["cases"][slot]["states"][1:]:
        record["area_m2"] *= 1.125
    variants["consistent_wrong_edits"] = document, values | {OPTION: edited_pair}, "disagrees with the generated swept solid"
    formerly_consistent = deepcopy(envelope)
    reopened = formerly_consistent["receipt"]["cases"][slot]["states"][2]
    reopened["depth_m"] *= 1.00000045
    reopened["volume_m3"] *= 0.99999955
    variants["reopen_mass_at_own_depth"] = document, values | {OPTION: formerly_consistent}, "disagrees with the generated swept solid"
    for model, opts, why in variants.values():
        sink = BytesIO()
        reject(lambda: emit(model, sink, opts), why)
        require(sink.tell() == 0 and not sink.getvalue(), "unmeasured publication changed the caller stream")
    sink = BytesIO(b"existing stream")
    reject(lambda: emit(document, sink, values), "empty seekable binary stream")
    require(sink.tell() == 0 and sink.getvalue() == b"existing stream", "caller content changed on refusal")
    return len(variants) + 1


def read_refusals(raw):
    reject(lambda: SldprtAdapter().read(BytesIO(raw), ReadOptions(extract_raw_brep=True)),
           "no readable Parasolid payload", SldprtFormat)
    archive = SldprtArchive.from_bytes(raw)
    for label in ("different_seam_end", "unsupported_axis_role", "alternate_boss"):
        link = ReadNativeLink(archive, 0, ReadEllipses=True)
        profile, boss = link.ResolvedValue.RootsValue[-2:]
        item = profile.FieldsValue["pd_f80"].FieldsValue["ellipses"][0]["ellipse"]
        if label == "different_seam_end":
            item["fcc_s"] = item["fe0_s"]
        elif label == "unsupported_axis_role":
            item["fe0_s"], item["fe4_s"] = item["fe4_s"], item["fe0_s"]
        else:
            boss.FieldsValue["f818"].FieldsValue["f8c"] = 1
        graph = link.ResolvedValue
        changed, _ = WriteResolMut(graph.RootsValue, graph.ExtraFields, 19000, link.ConfigValue.MapValue,
                                   graph.ContextValue, ReplayEllipses=True)
        changed_streams = dict(archive.streams)
        changed_streams[link.StreamName] = changed
        contrast = BuildSldprt(changed_streams, FormatVersion=4)
        for included in (True, False):
            reject(lambda: open_document(contrast, source_format=FORMAT, include_brep=included),
                   "full ellipse lacks its verified cold owners", SldprtFormat)
        partial = open_document(contrast, source_format=FORMAT, include_brep=False, strict=False)
        require(any("full ellipse lacks its verified cold owners" in row.message for row in partial.diagnostics),
                "permissive malformed-ellipse inspection lost the scoped diagnostic")
    return 7


def extra_sketch_refusal(candidate):
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    config, graph = candidate.ConfigValue, candidate.ResolvedValue
    front, = (row for row in graph.RootsValue if ReadNodeName(row) == "Front Plane")
    ids = PersistentIds(config.HeaderValue.FieldsValue["f08"])
    extra = MakeProfileMut("ExtraProfile", config.RootValue, front, "z",
                           PolygonInput(((.002, .001), (.012, .002), (.005, .013)), 19000),
                           FeatureTarget(2026306, 370108), ids).ProfileValue
    roots = (*graph.RootsValue[:-1], extra, graph.RootsValue[-1])
    compiled, _ = WriteResolMut(roots, graph.ExtraFields, 19000, config.MapValue,
                                graph.ContextValue, ReplayEllipses=True)
    keywords = fromstring(archive.require(KeywordsStream)[1:])
    keywords.insert(len(keywords) - 1, Element("Sketch", {"id": str(extra.FieldsValue["f08"]),
                    "Name": "ExtraProfile", "Type": "moProfileFeature_c"}))
    contrast = BuildSldprt(dict(archive.streams) | {KResolvedFeaturesStream: compiled, KeywordsStream: FrameKeywords(keywords, False)},
                           FormatVersion=4)
    parsed = SldprtArchive.from_bytes(contrast)
    extra_link = ReadNativeLink(parsed, 0, ReadEllipses=True)
    active, _, _ = DecodePartModel(parsed, None)
    require(len(extra_link.ResolvedValue.RootsValue) == len(graph.RootsValue) + 1
            and tuple(value.name for value in active.sketches) == ("EllipseProfile", "ExtraProfile"),
            "contrast failed to create two physically resolved sketches")
    for included in (True, False):
        reject(lambda: open_document(contrast, source_format=FORMAT, include_brep=included),
               "full ellipse is outside the verified cold archive profile", SldprtFormat)
    partial = open_document(contrast, source_format=FORMAT, strict=False, include_brep=False)
    require(len(partial.sketches) == 2 and any("full ellipse is outside the verified cold archive profile" in row.message
                                             for row in partial.diagnostics), "permissive inspection dropped the extra sketch or diagnostic")
    return {"sha256": digest(contrast), "resolved_sketches": len(partial.sketches), "strict_refusals": 2, "permissive_inspection": True}


def verify_roundtrip(document, raw, scope, entrypoints):
    restored = CadDocument.from_json(document.to_json())
    for emit in entrypoints:
        for model in (document, restored):
            sink = BytesIO()
            outcome = emit(model, sink, scope)
            require(sink.getvalue() == raw and outcome.native_capabilities == model.capabilities
                    and not outcome.dropped and outcome.vendor_loadable and outcome.application_usable,
                    "reopened conic lost exact bytes or semantic transfers")
        for source, meta in ((document.source, document.metadata | {"unowned_attribute": "keep"}),
                             (replace(document.source, sha256="3" * 64), document.metadata)):
            sink = BytesIO()
            changed = replace(document, source=source, metadata=meta)
            reject(lambda: emit(changed, sink, scope), "differs from its regenerated part")
            require(not sink.getvalue() and sink.tell() == 0, "changed readback reached the recipient")
    return {"exact_routes": len(entrypoints) * 2, "native_transfers": len(document.capabilities),
            "altered_source_refusals": len(entrypoints) * 2}


def verify_translated(scope, entrypoints):
    name = "EllipseTranslated"
    angle = radians(33)
    alternate = {"name": name, "center_mm": [70, 70], "radii_mm": [40, 30],
                 "angle_deg": 33, "depth_mm": 15.0, "edited_depth_mm": 19.0}
    model = make_document({key: alternate[key] for key in ("name", "center_mm", "radii_mm", "depth_mm")}
                          | {"major_xy": [cos(angle), sin(angle)]})
    options = scope | {"final_destination": rf"C:\KitSdkCandidates\{name}.SLDPRT"}
    candidate = PrepareEllipse(model, BytesIO(), scope[OPTION]["written_at"], WriteOptions(values=options))
    document = open_document(candidate.BytesValue, source_format=FORMAT)
    check_semantics(document, alternate, True)
    for emit in entrypoints:
        sink = BytesIO()
        reject(lambda: emit(model, sink, options), "no unique exact native measurement")
        require(not sink.getvalue() and sink.tell() == 0, "unmeasured translated output was published")
    return {"sha256": digest(candidate.BytesValue), "strict_read": True, "publication_refusals": len(entrypoints)}


def worker(request):
    model = make_document(request["model"])
    scope = {"final_destination": request["locator"], OPTION: request["evidence"], "require_native_transfers": True}
    warm_imports()
    with TemporaryDirectory(prefix="KitScopedEllipse-") as folder:
        target = Path(folder).resolve() / (request["model"]["name"] + ".SLDPRT")
        target.write_bytes(b"existing target")
        if sys.platform != "win32":
            reject(lambda: write_document(model, target, overwrite=True, values=scope, allow_carrier=False),
                   "actual final filesystem locator")
            reject(lambda: SldprtWriter().write(model, target, WriteOptions(overwrite=True, values=scope)),
                   "actual final filesystem locator")
            require(target.read_bytes() == b"existing target" and tuple(target.parent.iterdir()) == (target,),
                    "path refusal left a publication or staging state")
        audit = WriterAudit(ROOT / "src", target)
        sys.addaudithook(audit.observe)
        audit.phase = "write"
        try:
            internal = PrepareEllipse(model, BytesIO(), request["epoch"], WriteOptions(values=scope))
            raw = internal.BytesValue
            require(digest(raw) == request["measured_sha256"] and len(raw) == request["measured_bytes"],
                    "model-only generation differs from actual native-tested cold archive")
            entrypoints = (public_write, direct_write)
            for emit in entrypoints:
                sink = BytesIO()
                result = emit(model, sink, scope)
                require(sink.getvalue() == raw and result.vendor_loadable and result.application_usable
                        and not result.dropped and result.bytes_written == len(raw)
                        and result.metadata[OPTION]["generated_sha256"] == request["measured_sha256"],
                        "measured publication or directed sink differs")
            refusals = sum(write_refusals(emit, model, scope, request["slot"]) for emit in entrypoints)
            full = open_document(raw, source_format=FORMAT, configuration="Default")
            design = open_document(raw, source_format=FORMAT, include_brep=False)
            check_semantics(full, request["case"], True)
            check_semantics(design, request["case"], False)
            require(full.sketches == design.sketches and full.parameters == design.parameters
                    and full.feature_timeline == design.feature_timeline, "geometry option changed editable history")
            geometric, observed = check_measures(full, request["case"], request["cold_native"])
            roundtrips = verify_roundtrip(full, raw, scope, entrypoints)
            design_roundtrips = verify_roundtrip(design, raw, scope, entrypoints)
            translated = verify_translated(scope, entrypoints)
            require(not audit.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
                    "preparation, publication or typed readback escaped the offline guard")
        finally:
            audit.phase = "done"
    return {"name": request["model"]["name"], "archive_sha256": digest(raw), "archive_bytes": len(raw),
            "clear_stream_hashes": {name: digest(data) for name, data in internal.StreamsValue.items()},
            "map_counters": [internal.ConfigValue.MapValue.CounterValue, internal.ResolvedValue.MapValue.CounterValue],
            "scope": ["direct", "registry", "strict_readback"], "depth_mm": full.parameters[0].value.value,
            "write_refusals": refusals + (2 if sys.platform != "win32" else 0), "read_refusals": read_refusals(raw),
            "filesystem_reads_after_import": len(audit.denied), "trim_surface_evaluations": geometric,
            "native_measure_comparisons": observed, "cold_readback_to_write": roundtrips,
            "unmeasured_translated_contrast": translated, "design_only_readback_to_write": design_roundtrips,
            "extra_sketch_contrast": extra_sketch_refusal(internal)}


def cold_summary(phase):
    body = phase["cold"]["body"]
    return body["mass"] | {"solid_count": body["solid_count"], "faces": body["faces"], "bounds_m": body["bounds_m"],
                           "seams_m": [cap["trim"]["seam_points_m"][0] for cap in sorted(body["caps"], key=lambda cap: cap["station"])]}


def saved_refusals(folder):
    source = ROOT / "re/solidworks/measurements/2026/EllipseBlindBossArchive01.json"
    evidence = load_pin(source, "fd68df149a85579b40779e829d885698ef6e3dc695c6131570c43597b34de5d4")
    findings = []
    for row in evidence["cases"]:
        raw = (folder / (row["case"] + ".SLDPRT")).read_bytes()
        require(digest(raw) == row["sha256"], "disclosed native saved archive differs")
        archive = SldprtArchive.from_bytes(raw)
        model, _, _ = DecodePartModel(archive, None)
        (sketch,) = model.sketches
        (handle,) = (item for item in model.classes if item.name == "sgEllipseHandle")
        require(sketch.native_offset <= handle.offset < sketch.native_end, "saved ellipse marker lost its active profile")
        reject(lambda: ReadNativeLink(archive, 0, ReadEllipses=True), "moLinkedAtomIdNode_c schema 1")
        for included in (True, False):
            reject(lambda: open_document(raw, source_format=FORMAT, include_brep=included),
                   "full ellipse is outside the verified cold archive profile", SldprtFormat)
        partial = open_document(raw, source_format=FORMAT, strict=False, include_brep=False)
        require(len(partial.sketches) == 1 and len(partial.feature_timeline) == 26
                and any("full ellipse is outside the verified cold archive profile" in item.message for item in partial.diagnostics)
                and not any(type(entity.geometry) is EllipseGeometry for sketch in partial.sketches for entity in sketch.entities),
                "permissive native saved inspection did not retain its available diagnostic history")
        findings.append({"case": row["case"], "sha256": row["sha256"], "streams": len(archive.records),
                         "first_scoped_owner": "moLinkedAtomIdNode_c schema 1", "profile_handle_offset": handle.offset,
                         "explicit_public_refusals": 2, "permissive_tree_rows": len(partial.feature_timeline)})
    return findings


def supervise(folder, output, saved_sources):
    receipt, requests = normalize(folder)
    reference = load_pin(ROOT / "re/solidworks/measurements/2026/SdkColdEllipseReceipt01.json", RECEIPT_SHA)
    require(receipt == reference, "exact normalized disclosure differs")
    trial = load_pin(folder / "Packet/Trial.json", TRIAL_SHA)
    controls = {}
    for label in ("ControlCircle.SLDPRT", "ControlRectangle.SLDPRT"):
        data = (folder / "Packet" / label).read_bytes()
        checksum = digest(data)
        require(checksum == trial["files"][label]["sha256"], "disclosed ordinary read control differs")
        model = open_document(data, source_format=FORMAT)
        require(model.brep is not None and not model.validate(), "ordinary read control no longer yields a valid solid")
        controls[label] = checksum
    result = []
    for slot, (request, row, case) in enumerate(zip(requests, receipt["cases"], trial["spec"]["cases"], strict=True)):
        phase, = (item for item in receipt["phases"] if item["phase"] == "edit" and item["slot"] == slot)
        work = request | {"slot": slot, "case": case, "measured_sha256": row["archive_sha256"],
                          "measured_bytes": row["archive_bytes"], "cold_native": cold_summary(load_phase(folder, phase)),
                          "evidence": {"written_at": row["written_at"], "receipt": receipt}}
        outcome = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"], text=True,
                                 input=json.dumps(work), capture_output=True, timeout=90, check=False)
        require(outcome.returncode == 0 and not outcome.stderr, outcome.stderr)
        result.append(json.loads(outcome.stdout))
    tree = subprocess.check_output(["git", "rev-parse", "HEAD:src"], cwd=ROOT, text=True).strip()
    require(subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src"], cwd=ROOT, check=False).returncode == 0,
            "commit the measured SDK source before recording its custody pin")
    report = {"schema": "kit.sw2026.scoped-measured-ellipse.v1", "native_result_sha256": NATIVE_SHA,
              "src_tree": tree, "python_version": ".".join(map(str, sys.version_info[:3])),
              "deflate_version": ZLIB_RUNTIME_VERSION,
              "native_trial_sha256": TRIAL_SHA, "normalized_receipt_sha256": RECEIPT_SHA,
              "native_phase_sha256": [row["receipt_sha256"] for row in receipt["phases"]],
              "prior_native_processes": receipt["fresh_processes"], "prior_healthy_controls": 4,
              "prior_native_checks": sum(row["checks"] for row in receipt["phases"]),
              "new_native_launches": 0, "heldout_credit": 0, "legacy_read_controls": controls,
              "method_sha256": {path.name: digest(path.read_bytes()) for path in
                                (HERE, *(HERE.with_name(name + ".py") for name in
                                         ("ColdEllipseModel", "EllipseMeasuredReceipt", "EllipseModel", "VerifyEllipseBoundary")))},
              "guarded_workers": len(result), "results": result,
              "native_saved_contrasts": saved_refusals(saved_sources) if saved_sources is not None else []}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--warm-disclosed", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    else:
        require(args.disclosed is not None and args.output is not None, "use the disclosed packet and a fresh output")
        supervise(args.disclosed, args.output, args.warm_disclosed)
