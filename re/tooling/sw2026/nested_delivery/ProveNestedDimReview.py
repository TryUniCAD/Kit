from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import inf, isclose, nextafter
from pathlib import Path, PureWindowsPath
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[4] / "src"), str(HERE.parent)]

from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks import SldprtAdapter
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import PrepNestedAsm
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Behavior.DocumentIo import ToJson
from NestedRequest import authored_document, checked, require
from NestedWriteAudit import Audit, snapshot
from ProveMeasuredNested import run_worker
from ProveNestedDimLeaves import DataReadAudit, rebuild_resolved
from ReadNestedEvidence import TERMINALS, measured_request

CIRCLE = "RadialConcentricDisplay02/Frozen/DisclosedRadialSceneProbe.SLDPRT"
CIRCLE_SHA = "9772dfdc9cbbfa6d48277d0466e208aefabbf947bb59d539b96cec33ed772d26"


def worker_precision(job, area):
    request = job["request"]
    envelope = job["envelope"]
    document, output = authored_document(request)
    candidates = document.assembly.documents
    part, = (entry.document for entry in candidates if len(entry.document.parameters) == 3)
    parameter = part.parameter(part.sketches[0].parameter_ids[job["index"]])
    before = parameter.value.value * 0.001
    document_parameters = next(
        row["request"]["document"]["parameters"]["$tuple"]
        for row in request["definitions"] if row["id"] == job["member"]
    )
    authored, = (row["value"] for row in document_parameters if row["id"] == parameter.id)
    authored["value"] = nextafter(authored["value"], inf)
    after = authored["value"] * 0.001
    require(before != after and isclose(before, after, rel_tol=1e-12, abs_tol=1e-14), "contrast missed old tolerance")
    document, output = authored_document(request)
    document.assert_valid()
    members = envelope["receipt"]["members"]
    target = area / PureWindowsPath(output["path_name"]).name
    audit = Audit(area, target, area / members[-2]["name"], [row["name"] for row in members], "precision")
    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    sys.addaudithook(audit.inspect)
    measured = next(row for row in members if row["id"] == job["member"])
    changed = next(value.BytesValue for path, value in PrepNestedAsm(document, output["path_name"], envelope["written_at"])
                   if path.name == measured["name"])
    changed_hash = sha256(changed).hexdigest()
    audit.active = False
    reopened = open_document(BytesIO(changed), source_format="solidworks.sldprt", include_brep=False)
    audit.active = True
    restored_id = reopened.sketches[0].parameter_ids[job["index"]]
    require(changed_hash != measured["sha256"] and reopened.parameter(restored_id).attributes["native_value"] == after,
            "adjacent authored driver failed to change and survive the generated native word")
    opts = {"native_destination": output["path_name"], "require_native_transfers": True,
            "solidworks_native_measurement": envelope}
    try:
        for route in ("registry", "adapter"):
            try:
                if route == "registry":
                    write_document(document, target, destination_format="solidworks.sldasm", allow_carrier=False, values=opts)
                else:
                    SldprtAdapter().write(document, target, WriteOptions(values=opts))
            except ValueError as caught:
                require("does not match the exact member" in str(caught), str(caught))
            else:
                raise AssertionError(f"{route} published a changed sketch driver")
    finally:
        audit.active = False
    require(not any((audit.attempts, audit.published, audit.staged_write_attempts, snapshot(area))), "refused scalar edit touched output")
    return {"driver": parameter.name, "original_m": before.hex(), "edited_m": after.hex(), "generated_sha256": changed_hash,
            "both_routes_refused": True, "staged_writes": 0, "final_writes": 0, "runtime_input_file_reads": 0}


def worker_read(job):
    raw = b64decode(job["data"], validate=True)
    require(sha256(raw).hexdigest() == job["sha256"], "read identity differs")
    archive = SldprtArchive.from_bytes(raw)
    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    audit = DataReadAudit()
    sys.addaudithook(audit.guard)
    kind = job["kind"]
    if kind == "other_relation_inventory":
        require(KPartitionStream not in archive.streams, "expected a cold scope contrast")
        link = ReadNativeLink(archive, 0, RectangleDims=True)
        profile, = (row for row in IndexFeatures(link).values() if row.ClassValue.NameValue == "moProfileFeature_c")
        fields = profile.FieldsValue["pd_f80"].FieldsValue
        require(fields["dims"]["ng2"] == 2 and fields["dims"]["nlog1"] == 4, "contrast expects two valued and four logical rows")
        fields["dims"]["log_g1"] = ()
        fields["dims"]["nlog1"] = 0
        for line in fields["lines"]:
            line["line"]["f20"] = 0
        resolved, _ = rebuild_resolved(link)
        raw = BuildSldprt(archive.streams | {link.StreamName: resolved})
        changed = SldprtArchive.from_bytes(raw)
        ReadNativeLink(changed, 0, RectangleDims=True)
    part = open_document(BytesIO(raw), source_format="solidworks.sldprt", include_brep=kind != "other_relation_inventory")
    sketch, = part.sketches
    if kind == "endpoints":
        loop, = sketch.closed_profile_entity_ids
        distances = [row for row in sketch.constraints if row.kind == "distance"]
        observed = [(r.parameter_id, [(ref.entity_id, ref.point) for ref in r.references]) for r in distances]
        expected = [(param, [(edge, "start"), (edge, "end")]) for param, edge in zip(sketch.parameter_ids, loop[:2], strict=True)]
        require(observed == expected and len(observed) == 2 and expected[0][0] != expected[1][0], "width or height endpoint did not round trip")
        mapped = {row.id: row for row in sketch.entities}
        values = []
        for relation in distances:
            first, second = relation.references
            edge = mapped[first.entity_id].geometry
            driver = part.parameter(relation.parameter_id)
            length_mm = abs(edge.end.x - edge.start.x) + abs(edge.end.y - edge.start.y)
            require(driver.value.value == length_mm and length_mm * 0.001 == driver.attributes["native_value"],
                    "displayed driver, endpoints and stored metre word disagree")
            values.append(length_mm)
        result = {"checked_ordered_endpoint_pairs": observed, "matched_endpoint_lengths_mm": values}
    elif kind == "circle":
        require(len(sketch.entities) == 1 and sketch.entities[0].kind.value == "circle"
                and part.brep is not None and [value.value.value for value in part.parameters] == [7.19, 31.37],
                "existing circular source lost its radius, depth or body")
        result = {"circle_radius_mm": 7.19, "boss_depth_mm": 31.37, "body_count": len(part.bodies)}
    else:
        owner = import_module("convert.adapters.solidworks.Core.Adapter")
        owner.WithTypedNative = lambda model, archive: model
        legacy = open_document(BytesIO(raw), source_format="solidworks.sldprt", include_brep=False)
        require(ToJson(part, IndentSize=None) == ToJson(legacy, IndentSize=None), "out-of-scope dimensioned part diverged from the legacy reader")
        require(sketch.attributes.get("typed_line_dimensions") is not True, "alternate relation inventory was incorrectly bound")
        result = {"legacy_semantics_identical": True, "value_rows": 2, "axis_rows": 0, "semantic_archive_sha256": sha256(raw).hexdigest()}
    require(not any(name.startswith(("pythoncom", "win32com", "FreeCAD")) for name in sys.modules), "CAD runtime loaded")
    return {"kind": kind, "input_sha256": job["sha256"], "runtime_input_file_reads": audit.input_files, **result}


def run_data(job, area):
    response = run([sys.executable, "-I", "-B", str(HERE), "--worker", str(Path(area).resolve())],
                   input=json.dumps(job), text=True, capture_output=True, check=False)
    require(response.returncode == 0 and not response.stderr, response.stderr)
    return json.loads(response.stdout)


def prove(workspace):
    cases, directions, edits = {}, [], []
    with TemporaryDirectory(prefix="KitDimReview.") as area:
        for case in TERMINALS:
            request, envelope = measured_request(workspace, case)
            ordered = [run_worker(request, envelope, route, "measured") for route in ("registry", "adapter")]
            require(ordered[0] == ordered[1], "published direct and registry contracts differ")
            cases[case] = ordered[0]
            production = {row["id"]: row for row in envelope["receipt"]["members"]}
            for member in (row for row in request["definitions"] if row["kind"] == "part"
                           and len(row["request"]["document"]["parameters"]["$tuple"]) == 3):
                tracked = production[member["id"]]
                raw = checked(workspace / case / "FrozenGenerated" / tracked["name"], tracked["sha256"])
                job = {"data": b64encode(raw).decode("ascii"), "sha256": tracked["sha256"], "kind": "endpoints"}
                directions.append({"case": case, "member": member["id"], **run_data(job, area)})
                if case == "SdkNestedDimensionedNative01":
                    alternate = run_data({**job, "kind": "other_relation_inventory"}, area)
                    for index in (0, 1):
                        edits.append(run_data({"request": request, "envelope": envelope, "index": index,
                                               "member": member["id"], "kind": "precision"}, area))
        circle = checked(workspace / CIRCLE, CIRCLE_SHA)
        observed = run_data({"data": b64encode(circle).decode("ascii"), "sha256": CIRCLE_SHA, "kind": "circle"}, area)
    return {"passed": True, "native_processes_started": 0, "protected_inputs_read": 0,
            "publication_cases": cases, "real_endpoint_checks": directions, "edited_driver_refusals": edits,
            "alternate_cold_relation_inventory": alternate, "circular_control": observed}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker is not None:
        job = json.load(sys.stdin)
        result = worker_precision(job, args.worker) if job["kind"] == "precision" else worker_read(job)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
    else:
        raw = (json.dumps(prove(args.workspace), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as output:
            output.write(raw)
        print(sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
