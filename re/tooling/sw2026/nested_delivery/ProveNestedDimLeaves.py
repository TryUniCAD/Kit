from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from hashlib import sha256
from io import BytesIO
from math import isclose, sqrt
from os import getpid
from pathlib import Path
from struct import pack
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parents[1]), str(HERE.parent)]

from NestedRequest import checked, require
from ReadNestedEvidence import measured_request, read, TERMINALS
from convert import open_document
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface

CASES = {
    "SdkNestedDimensionedNative01": ("plate",),
    "SdkRepeatedDimensionedNative01": ("plate", "gauge"),
    "SdkNestedNeutralNative03": ("plate",),
}
NEGATIVES = {
    "display_slot": "does not own its selected sketch value",
    "shared_parameter": "shared or incomplete owners",
    "point_reference_count": "unqualified entity ownership or geometry",
    "axis_role": "axes do not cover every owned line",
    "draft": "unsupported start or end state",
}


class DataReadAudit:
    def __init__(self):
        self.input_files = 0
        self.cad_processes = 0
        self.format_schema_reads = 0

    def guard(self, event, arguments):
        if event == "open":
            name = arguments[0]
            if type(name) is str and name.endswith((".py", ".pyc")):
                return
            if name == str(ROOT / "src/convert/adapters/solidworks/Config/RootLayout.json"):
                self.format_schema_reads += 1
                return
            self.input_files += 1
            raise AssertionError(f"unrequested file access in the pure read boundary: {name}")
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "ctypes.dlopen"}:
            self.cad_processes += 1
            raise AssertionError(f"runtime launch or native library load: {event}")


def derived_area(model):
    require(all(isinstance(surface, PlaneSurface) for surface in model.surfaces), "nonplanar prism")
    vertices = {vertex.id: vertex.point for vertex in model.vertices}
    edges = {edge.id: edge for edge in model.edges}
    coedges = {coedge.id: coedge for coedge in model.coedges}
    loops = {loop.id: loop for loop in model.loops}
    area = 0.0
    for face in model.faces:
        loop_id, = face.loop_ids
        loop = loops[loop_id]
        witnesses = [
            vertices[edge.end_vertex_id if coedge.reversed else edge.start_vertex_id]
            for key in loop.coedge_ids for coedge in (coedges[key],) for edge in (edges[coedge.edge_id],)
        ]
        require(loop.outer and len(witnesses) == 4, "nonrectangular prism face")
        crossed = [0.0, 0.0, 0.0]
        for first, second in zip(witnesses, witnesses[1:] + witnesses[:1]):
            crossed[0] += first.y * second.z - first.z * second.y
            crossed[1] += first.z * second.x - first.x * second.z
            crossed[2] += first.x * second.y - first.y * second.x
        area += sqrt(sum(value * value for value in crossed)) / 2
    return area


def rebuild_resolved(link):
    value = link.ResolvedValue
    return WriteResolMut(value.RootsValue, value.ExtraFields, value.VersionValue,
                         link.ConfigValue.MapValue, value.ContextValue, RectangleDims=True)


def changed_data(archive, link, contrast):
    features = IndexFeatures(link)
    profile, = [value for value in features.values() if value.ClassValue.NameValue == "moProfileFeature_c"]
    boss, = [value for value in features.values() if value.ClassValue.NameValue == "moExtrusion_c"]
    sketch = profile.FieldsValue["pd_f80"].FieldsValue
    dims = sketch["dims"]
    if contrast == "display_slot":
        display = dims["f118"].FieldsValue["items"][0]["o"].FieldsValue
        display["f850"][0]["o"].FieldsValue["ff8"] = 1
    elif contrast == "shared_parameter":
        first, second = [row["d"].FieldsValue for row in dims["val_g2"]]
        second["f28"] = first["f28"]
        display = dims["f118"].FieldsValue["items"][1]["o"].FieldsValue
        display["f5b0"]["data"] = pack("<d", first["f28"].FieldsValue["f58"])
    elif contrast == "point_reference_count":
        sketch["points"][0]["point"]["f20"] += 1
    elif contrast == "axis_role":
        dims["log_g1"][0]["d"]["f80"] = 5
    elif contrast == "draft":
        boss.FieldsValue["f818"].FieldsValue["fa0"] = 0.125
    else:
        raise ValueError("unknown diagnostic contrast")
    changed, _ = rebuild_resolved(link)
    require(changed != archive.require(link.StreamName), "contrast did not change the typed stream")
    return BuildSldprt(archive.streams | {link.StreamName: changed})


def registry_read(data, expected, brep=True):
    return open_document(BytesIO(data), source_format="solidworks.sldprt",
                         configuration=expected["configuration"], include_brep=brep)


def native_close(actual, expected, label):
    require(isclose(actual, expected, rel_tol=5e-7, abs_tol=1e-13), f"{label} differs from native observation")


def verify_document(document, expected, dimensions):
    sketch, = document.sketches
    body, = document.bodies
    configurations = [value.name for value in document.configurations if value.active]
    steps = {value.id: value for value in document.feature_timeline}
    parameters = {
        f"{value.name}@{steps[value.owner_id].name}": value.value.value / 1000.0
        for value in document.parameters
    }
    owners = [value.attributes["typed_archive_owner"] for value in document.parameters]
    live = {name: value for name, value in expected["parameters_m"].items() if value is not None}
    require(set(parameters) == set(live) and configurations == [expected["configuration"]]
            and len({row["object_index"] for row in owners}) == len(owners)
            and all(row["value_field"] == "f58" for row in owners)
            and all(value.role.value == "driving" and value.value.unit == "mm" for value in document.parameters),
            "configuration or distinct live parameter ownership changed")
    for key, value in parameters.items():
        native_close(value, live[key], key)
    if dimensions:
        axes = ("horizontal", "vertical", "horizontal", "vertical")
        require(tuple(relation.kind for relation in sketch.constraints) == (*axes, "distance", "distance")
                and tuple(value.parameter_id for value in sketch.constraints[-2:]) == sketch.parameter_ids
                and all(value.driving and not value.suppressed for value in sketch.constraints), "lost live sketch constraints")
        width, height = (parameters[f"{name}@{sketch.name}"] for name in ("D1", "D2"))
        for relation, expected_point in zip(sketch.constraints[-2:], ((0., -.75 * height, 0.), (.75 * width, 0., 0.)), strict=True):
            require(tuple(ref.point for ref in relation.references) == ("start", "end"), "lost point selector roles")
            for actual, target in zip(relation.attributes["native_display_text_point_m"], expected_point, strict=True):
                native_close(actual, target, "annotation point")
    else:
        require(not sketch.constraints and not sketch.parameter_ids, "plain control acquired sketch drivers")
    model = document.brep
    require(model is not None, "cold leaf has no analytic body")
    summary = body.topology
    topology = [summary.solid_count, summary.shell_count, summary.face_count, summary.edge_count, summary.vertex_count]
    require(topology == [expected["body_count"], 1, 6, 12, 8], "body topology differed")
    volume = summary.volume / 1e9
    area = derived_area(model) / 1e6
    centre = tuple(value / 1000 for value in body.attributes["solidworks.body_centroid_mm"])
    native = expected["mass_properties"]
    native_close(volume, native["volume"], "volume")
    native_close(area, native["area"], "surface area")
    for actual, target in zip(centre, native["com"], strict=True):
        native_close(actual, target, "centre of mass")
    final = steps[body.final_feature_id]
    native_owner_rows = expected["tree"][-2:]
    require((steps[final.input_feature_ids[0]].name, final.name) == tuple(row["name"] for row in native_owner_rows)
            and final.sketch_id == sketch.id and final.operation.value == "create"
            and len(final.parameter_ids) == 1 and document.plane(sketch.support_plane_id).name == "Front Plane",
            "lost the actual body, profile or support role")
    return {"parameters_m": parameters, "topology": topology, "volume_m3": volume,
            "area_m2": area, "centre_m": centre, "relation_kinds": [row.kind for row in sketch.constraints]}


def worker(job):
    data = b64decode(job["data"], validate=True)
    require(sha256(data).hexdigest() == job["sha256"], "worker received another archive")
    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    audit = DataReadAudit()
    sys.addaudithook(audit.guard)
    archive = SldprtArchive.from_bytes(data)
    require(KPartitionStream not in archive.streams, "expected a genuinely cache-free part")
    link = ReadNativeLink(archive, 0, RectangleDims=True)
    resolved, graph = rebuild_resolved(link)
    require(archive.require(link.StreamName) == resolved and graph.MapValue.CounterValue == link.ResolvedValue.MapValue.CounterValue,
            "strict linked Resolved stream did not round trip")
    expected = job["expected"]
    contrast = job["contrast"]
    if contrast:
        changed = changed_data(archive, link, contrast)
        failures = []
        for brep in (False, True):
            try:
                registry_read(changed, expected, brep)
            except SldprtFormat as caught:
                require(NEGATIVES[contrast] in str(caught), "unrelated native reader refusal")
                failures.append(str(caught))
            else:
                raise ValueError("contradicted typed owner fell back to a public model")
        result = {"contrast": contrast, "refusals": failures}
    else:
        part = registry_read(data, expected)
        result = verify_document(part, expected, sum(value is not None for value in expected["parameters_m"].values()) == 3)
        tree_only = registry_read(data, expected, False)
        require(tree_only.brep is None and tree_only.parameters == part.parameters
                and tree_only.sketches == part.sketches and tree_only.feature_timeline == part.feature_timeline,
                "tree-only read changed supported profile or exposed a body cache")
    require(not any(name.startswith(("win32com", "pythoncom", "FreeCAD")) for name in sys.modules),
            "reader imported a CAD runtime")
    return {"case": job["case"], "member": job["member"], "pid": getpid(),
            "archive_sha256": job["sha256"], "resolved_bytes": len(resolved),
            "resolved_sha256": sha256(resolved).hexdigest(), "runtime_input_file_reads": audit.input_files,
            "packaged_format_schema_reads": audit.format_schema_reads,
            "runtime_process_or_library_launches": audit.cad_processes, **result}


def prove(workspace):
    rows = []
    for case, members in CASES.items():
        _, envelope = measured_request(workspace, case)
        folder = workspace / case
        terminal = read(folder, "Inspection/Result.json", TERMINALS[case])
        by_id = {row["id"]: row for row in envelope["receipt"]["members"]}
        expected = terminal["phases"][1]["initial"]["definitions"]
        for member in members:
            identity = by_id[member]
            path = folder / "FrozenGenerated" / identity["name"]
            data = checked(path, identity["sha256"])
            encoded = b64encode(data).decode("ascii")
            contrasts = (None, *NEGATIVES) if (case, member) == ("SdkNestedDimensionedNative01", "plate") else (None,)
            for contrast in contrasts:
                request = {"data": encoded, "sha256": identity["sha256"], "expected": expected[member],
                           "case": case, "member": member, "contrast": contrast}
                proc = run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                           input=json.dumps(request), text=True, capture_output=True, check=False)
                require(proc.returncode == 0 and not proc.stderr, f"{case} {member} {contrast}: {proc.stderr}")
                rows.append(json.loads(proc.stdout))
    require(len({row["pid"] for row in rows}) == len(rows), "read processes were reused")
    return {"passed": True, "native_processes_started": 0, "protected_inputs_read": 0, "results": rows}


def main():
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    else:
        body = json.dumps(prove(args.workspace), indent=2, sort_keys=True).encode("utf-8") + b"\n"
        with args.output.open("xb") as stream:
            stream.write(body)
        print(sha256(body).hexdigest())


if __name__ == "__main__":
    main()
