from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from io import BytesIO
from math import isclose
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from PrepareAttachedAxisTrial import GUEST_ROOT
from VerifyOriginalFcstdAttachedBox import CASE, FORMAT, NATIVE_SHA, ROOT, digest, guarded, locked, prewarm, refusal, require, source_proof, xyz
from VerifyAttachedBoxAxes import SOURCE_SHA, intake, visibility_source
from BoxIncidence import box_incidence
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import ReadOriginAxes
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadAxisGeom import ReadAxisGeom
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import ReadColdOutput
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.document.Models.DocumentModel import CadDocument


BASE = "1098e2076a788434c64ac63fbbcd7d850c52a926"
CANDIDATE_MANIFEST = "93189f21691fc1cd3ba0f26beb62541f85ac3f814ae68444d178f639099efe60"
NATIVE_TRIAL = "0ac0c750cd671a2f4c5dcc7e3459d79a51199c3c0cd7220ba8cc2dd6a953ac38"
SENTINEL = b"existing stream must survive"
ABSENT = "SLDPRT contains no readable Parasolid payload"


def checked_read(payload, request, *, candidate):
    document = open_document(payload, source_format=FORMAT, strict=True)
    require(CadDocument.from_json(document.to_json()) == document, "strict read did not survive neutral JSON")
    (body,) = document.bodies
    shape, incidence = box_incidence(document.brep, request["source_corners"], body.id)
    require(json.dumps(incidence, sort_keys=True) == json.dumps(request["source_incidence"], sort_keys=True),
            "computed analytic body incidence differs from the three original FreeCAD shape owners")
    require(body.name == "Body" and body.topology.volume == 6000.0 and body.topology.surface_area == 2200.0
            and xyz(body.topology.bounding_box.minimum) == (0.0, -10.0, 0.0)
            and xyz(body.topology.bounding_box.maximum) == (20.0, 0.0, 30.0)
            and body.attributes["solidworks.authored_output_name"]["native_kernel_identity"] is False,
            "strict signed geometry or owned body atom differs")
    require(document.metadata["custom_properties"] == request["properties"]["file"]
            and document.metadata["document_summary"] == request["properties"]["summary"],
            "literal FreeCAD source properties changed")
    archive = SldprtArchive.from_bytes(payload)
    link = ReadNativeLink(archive, 0)
    roots = IndexFeatures(link)
    history = tuple((feature.id, feature.name) for feature in document.feature_timeline)
    archive_order = tuple((f"sldprt:feature:{identity}", ReadNativeName(node)) for identity, node in roots.items())
    expected_order = (archive_order if candidate else
                      archive_order[:6] + archive_order[12:13] + archive_order[6:12] + archive_order[13:])
    require(history == expected_order, "strict read differs from linked axis order or legacy annotations placement")
    require(body.final_feature_id == "sldprt:feature:21" and document.brep.bodies[0].design_body_id == body.id,
            "generated solid no longer binds its actual boss and body")
    owners = {param.name: [param.value.value, param.owner_id] for param in document.parameters if str(param.role) == "driving"}
    require(owners == {"Length": [20.0, "sldprt:feature:18"], "Width": [30.0, "sldprt:feature:18"],
                       "Height": [10.0, "sldprt:feature:21"]}, "the signed box lost its independent driving owners")
    axes = check_axes(document, request["axes"] if candidate else [])
    return document, {"axes": axes, "feature_count": len(history), "body": body.name, "body_shape_id": shape,
                      "body_incidence_matches": True, "solid_count": body.topology.solid_count,
                      "volume_mm3": body.topology.volume, "area_mm2": body.topology.surface_area,
                      "bounds_mm": [xyz(body.topology.bounding_box.minimum), xyz(body.topology.bounding_box.maximum)],
                      "centroid_mm": [10, -5, 15], "drivers": owners, "ordinary_neutral_json_roundtrip": True}


def check_axes(document, expected):
    features = {row.id: row for row in document.feature_timeline}
    planes = {plane.id: plane for plane in document.support_planes}
    selections = {row.id: row for row in document.selections}
    axes = [row for row in document.feature_timeline if isinstance(row.definition, PlaneAxis)]
    require(len(axes) == len(expected), "strict SDK count of editable axis definitions differs")
    reports = []
    used = set()
    for axis, wanted in zip(axes, expected, strict=True):
        value = axis.definition
        require(axis.id == f"sldprt:feature:{wanted['id']}" and axis.name == wanted["name"]
                and axis.selection_ids == (value.FirstPlaneSelectionId, value.SecondPlaneSelectionId)
                and xyz(value.StartMm) == tuple(point*1000 for point in wanted["start_m"])
                and xyz(value.EndMm) == tuple(point*1000 for point in wanted["end_m"])
                and axis.provenance.spans[0].stream == "Contents/Config-0-ResolvedFeatures"
                and axis.attributes["solidworks.native_axis_data"]["class"] == "moPlaneInterAxisData_c"
                and axis.attributes["solidworks.native_axis_hidden"] is False, "axis identity, geometry or source span differs")
        parent_labels, wrappers = [], []
        for selected, parent in zip(axis.selection_ids, axis.input_feature_ids, strict=True):
            require(selected not in used, "portable axis selectors share an identity")
            used.add(selected)
            pick = selections[selected]
            (path,) = pick.path
            target = planes[path.entity_id]
            feature = features[parent]
            require(feature.name == target.name and pick.name == target.name and path.entity_kind == "support_plane"
                    and pick.query["native_owner_id"] == wanted["id"]
                    and pick.query["native_target_id"] == feature.attributes["native_object_id"]
                    and pick.provenance.spans[0].stream == "Contents/Config-0-ResolvedFeatures",
                    "axis selection does not identify its actual typed parent")
            wrappers.append([pick.provenance.native_id, pick.provenance.spans[0].offset])
            parent_labels.append(target.name)
        require(parent_labels == wanted["parents"], "axis changed actual parent order")
        reports.append({"id": axis.id, "name": axis.name, "parents": parent_labels, "wrappers": wrappers,
                        "start_mm": xyz(value.StartMm), "end_mm": xyz(value.EndMm)})
    return reports


def recollect(payload):
    archive = SldprtArchive.from_bytes(payload)
    return archive, ReadNativeLink(archive, 0)


def changed_payload(payload, change):
    archive, link = recollect(payload)
    extents = [root.FieldsValue for root in link.ResolvedValue.RootsValue[-3:]]
    x, y, z = (owner["f700"].FieldsValue for owner in extents)
    streams = dict(archive.streams)
    if change == "crossed_wrappers":
        x["f80"], x["f88"] = x["f88"], x["f80"]
    elif change == "aliased_component":
        x["f88"].FieldsValue["f58"].FieldsValue["f58"] = x["f80"].FieldsValue["f58"].FieldsValue["f58"]
    elif change == "coherent_old_endpoint":
        x["f10"] -= 0.001
        x["f30"] = {**x["f30"], "x": x["f10"]}
    elif change == "coherent_old_display":
        top = [row for row in IndexFeatures(link).values() if ReadNativeName(row) == "Top Plane"][0]
        top.FieldsValue["f6f8"].FieldsValue["b0"] += 0.001
        for wrapper in (x["f80"], z["f88"]):
            wrapper.FieldsValue["fb0"] = top.FieldsValue["f6f8"].FieldsValue["b0"]
    elif change == "hidden_axis":
        extents[1]["hidden"] = 1
    elif change == "foreign_creation":
        top_header = ReadHeaderGraph(streams["Header2"], 19000)
        rows = ReadLogItems(top_header.FieldsValue["f20"], "moLogs_c")
        rows[-1].FieldsValue["f48"] += 100
        streams["Header2"] = WriteHeadGraph(top_header, 19000)
        return BuildSldprt(streams, FormatVersion=4)
    else:
        raise ValueError("unknown scoped ownership probe")
    resolved = link.ResolvedValue
    streams[link.StreamName] = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000,
                                            link.ConfigValue.MapValue, resolved.ContextValue)[0]
    return BuildSldprt(streams, FormatVersion=4)


def checked_refusal(payload, label, diagnostic):
    changed = changed_payload(payload, label)
    archive, link = recollect(changed)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    model = NativePartModel(archive, None)
    direct = refusal(lambda: ReadAxisGeom(archive, link, manager, model, ReadColdOutput(link), "sldprt:body:1"), diagnostic)
    public = refusal(lambda: open_document(changed, source_format=FORMAT, strict=True), ABSENT)
    return {"owner_refusal": direct, "strict_sdk_refusal": public}


def publication_guard(document):
    stream = BytesIO(SENTINEL)
    stream.seek(4)
    settings = {"final_destination": str(GUEST_ROOT / "F14c.SLDPRT")}
    outcomes = {}
    for name, action in (
        ("registry", lambda: write_document(document, stream, destination_format=FORMAT, allow_carrier=False, values=settings)),
        ("adapter", lambda: SldprtWriter().write(document, stream, WriteOptions(values=settings))),
    ):
        try:
            action()
        except (ValueError, NotFoundError) as error:
            outcomes[name] = str(error)
        else:
            raise ValueError("a cold read qualified unmeasured ordinary publication")
    require(stream.getvalue() == SENTINEL and stream.tell() == 4, "refused publication modified caller bytes")
    return outcomes


def worker(request):
    lookup("utf-8-sig")
    prewarm()
    candidate = b64decode(request["candidate"], validate=True)
    baseline = b64decode(request["baseline"], validate=True)
    with guarded():
        document, result = checked_read(candidate, request, candidate=True)
        _, control = checked_read(baseline, request, candidate=False)
        without = open_document(candidate, source_format=FORMAT, strict=True, include_brep=False)
        require(without.brep is None and len(without.feature_timeline) == 22 and len(without.parameters) == 3,
                "ordinary history-only options changed")
        negative = {label: checked_refusal(candidate, label, message) for label, message in (
            ("crossed_wrappers", "cache free origin axis has crossed or nonprincipal supports"),
            ("aliased_component", "cache free origin axes contain shared exclusive owners"),
            ("coherent_old_endpoint", "cache free origin axis endpoints disagree with their finite support"),
            ("coherent_old_display", "cache free axis datum display disagrees with its stock"),
            ("hidden_axis", "cache free origin axis has unsupported feature state"),
            ("foreign_creation", "cache free origin axes lack complete creation ownership"),
        )}
        denied = publication_guard(document)
    return {"strict_candidate": result, "strict_axis_free_control": control, "history_only_preserved": True,
            "targeted_refusals": negative, "publication_refusals": denied, "runtime_input_file_reads": 0}


def isolate(request):
    task = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=json.dumps(request, allow_nan=False),
                          capture_output=True, text=True, timeout=120)
    require(task.returncode == 0 and not task.stderr, task.stderr or "strict axis read worker failed")
    return json.loads(task.stdout)


def native_axes(result, manifest, model, raw):
    expected_axes = manifest["wire"]["axes"]
    phases = result["phases"]
    lifetimes = {(phase["oracle_identity"]["process_id"], phase["oracle_identity"]["process_creation_filetime"])
                 for phase in phases.values()}
    require(result["oracle_build"] == KOraclePart["build"] and result["oracle_sha256"] == KOraclePart["sha256"]
            and result["native_destination"] == str(GUEST_ROOT / "F14c.SLDPRT")
            and result["candidate_sha256"] == manifest["candidate"]["sha256"]
            and result["passed"] and result["controls_healthy"] and result["candidate_unchanged"]
            and set(phases) == {"before", "generated", "reopen", "after"}
            and result["distinct_processes"] == len(lifetimes) == 4
            and all(phase["passed"] for phase in phases.values()), "native evidence does not bind this exact candidate")
    sources = visibility_source(model, raw, ReadOriginAxes(model))["axes"]
    for phase_name in ("generated", "reopen"):
        initial = phases[phase_name]["observations"]["Original"]["axes"]
        require(set(initial) == {row["label"] for row in sources}, "native returned alternate axis labels")
        for wire, source in zip(expected_axes, sources, strict=True):
            axis = initial[source["label"]]
            require(source["label"] == wire["name"] and source["model_visibility"] and axis["selectable"]
                    and axis["parents"] == wire["parents"] and axis["unit"] == wire["direction"]
                    and all(isclose(observed, authored, rel_tol=0.0, abs_tol=1e-14)
                            for observed, authored in zip(axis["unit"], source["direction"], strict=True))
                    and all(isclose(observed, encoded, rel_tol=0.0, abs_tol=1e-16)
                            for point, expected in zip(axis["endpoints_m"], [wire["start_m"], wire["end_m"]], strict=True)
                            for observed, encoded in zip(point, expected, strict=True)),
                    "cold archive does not match independently observed native/source axis")
    return [{"id": source["id"], "role": source["role"], "label": source["label"], "target_id": wire["id"]}
            for source, wire in zip(sources, expected_axes, strict=True)]


def changed_reader_files():
    adapter = ROOT / "src/convert/adapters/solidworks/Core"
    geo = adapter / "TypedResolved/Geometry"
    return (HERE, geo / "ColdOutput/WithColdName.py", *sorted((geo / "Axes").glob("*.py")), geo / "Display/DatumDisplay.py",
            *(geo / f"{name}.py" for name in ("CheckPrismDatum", "CheckPrismPlane", "CheckPrismScope", "ReadPrismPlan",
                                               "PartGeometry", "ReadNoCache")))


def main():
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    parser = ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("axis_candidate", type=Path)
    parser.add_argument("axis_free_control", type=Path)
    parser.add_argument("native_trial", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    measures = ROOT / "re/solidworks/measurements/2026"
    target = json.loads(locked(measures / "AttachedBoxAxesCandidate01.json", CANDIDATE_MANIFEST))
    prior = json.loads(locked(measures / "AttachedTopBoxGeneratedNative01.json", NATIVE_SHA))
    source, raw = intake(args.source, SOURCE_SHA)
    proof = source_proof(source, raw)
    native = json.loads(locked(args.native_trial, NATIVE_TRIAL))
    associations = native_axes(native, target, source, raw)
    candidate_sha, baseline_sha = target["candidate"]["sha256"], prior["cases"][CASE]["output_sha256"]
    request = {"candidate": b64encode(locked(args.axis_candidate, candidate_sha)).decode(),
               "baseline": b64encode(locked(args.axis_free_control, baseline_sha)).decode(),
               "axes": target["wire"]["axes"], "properties": target["source_text"],
               "source_corners": proof["world_corners"], "source_incidence": proof["incidence"]}
    result = isolate(request)
    require(result == isolate(request), "independent guarded strict reads differ")
    _ = locked(args.source, SOURCE_SHA)
    _ = locked(args.axis_candidate, candidate_sha)
    _ = locked(args.axis_free_control, baseline_sha)
    report = {"schema": "kit.sw2026.attached-box-axes-sdk-read.v1", "base": BASE, "passed": True,
              "source_sha256": SOURCE_SHA, "axis_candidate_sha256": candidate_sha, "axis_free_control_sha256": baseline_sha,
              "prior_native_control_receipt_sha256": NATIVE_SHA, "candidate_manifest_sha256": CANDIDATE_MANIFEST,
              "fresh_workers": 2, "new_native_observations": 0, "benchmark_conversion_credits": 0,
              "native_trial_sha256": NATIVE_TRIAL, "freecad_axis_associations": associations,
              "changed_reader_files_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes())
                                                for path in changed_reader_files()}, **result}
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
