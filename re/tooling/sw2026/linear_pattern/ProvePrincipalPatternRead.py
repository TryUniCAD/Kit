from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from contextlib import contextmanager
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveColdPatternRead import design_summary
from ProvePrincipalPatternContainer import build_input
from ProvePrincipalPatternDirection import MEASUREMENTS, ROOT, VERSION, expect, pinned, wire
from ProvePrincipalPatternDrivers import vector
from convert import open_document, write_document
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.IsPatRead import IsPatRead
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.CheckPrinc import CheckPrincPat
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatOwner import ReadPatOwner
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.Features.FeatureKinds import LinearPattern
from interchange.serialization import dumps, loads

BASE = "bd3ab078476c403e5615fc1f0eca6b29dd770747"
FORMAT = "solidworks.sldprt"
STATE = "solidworks.typed_linear_pattern"
ORIGIN_PIN = "060b399b345a7b89f5b1e64cd059eb1261d094f8db4c94b0465fe54312725197"
PLACED_PIN = "6081b4f4014738b6e403a9a10a1b7c0bfedca708e30aa71c5dbe53516c2f13fd"
EXACT_FIELDS = ("units", "configurations", "parameters", "support_planes", "sketches",
                "feature_timeline", "selections", "bodies", "brep", "brep_payloads")


@contextmanager
def boundary(path=None):
    requests = []
    active = True

    def audit(event, items):
        if not active:
            return
        if event == "open" and path is not None and items[0] == str(path) and items[1] == "r":
            requests.append(items[0])
            return
        if event in ("open", "os.listdir", "os.scandir", "subprocess.Popen", "os.system", "os.posix_spawn",
                     "os.fork", "os.forkpty", "ctypes.dlopen") or event.startswith(("os.exec", "os.spawn", "socket.")):
            raise PermissionError("unexpected input or runtime access during principal pattern read: " + event)

    sys.addaudithook(audit)
    try:
        yield requests
    finally:
        active = False


def typed(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    peer = ReadHeaderGraph(archive.require("Header2"), VERSION)
    return link, ReadPatOwner(link, peer, IsCold=True)


def verify_displays(link, owner, expected):
    CheckPrincPat(link, owner)
    displays = []
    maps = {row.IndexValue: row.EntryValue for row in link.ResolvedValue.MapValue.EntriesValue}
    model = link.ConfigValue.RootValue.FieldsValue
    catalogue = {row["o"].FieldsValue["f360"]: row["o"].FieldsValue["f358"]
                 for row in model["fa48"].FieldsValue["items"]}
    for driver in owner.DriversValue:
        dim_fields = driver.DisplayValue.FieldsValue
        members = tuple(row["v"] for row in dim_fields["f2b0"])
        nodes = (driver.DisplayValue, driver.HandleValue, driver.DimensionValue, driver.ParameterValue)
        indices = tuple(node.IndexValue for node in nodes)
        expect(all(type(index) is int and maps.get(index) is node
                   for index, node in zip(indices, nodes, strict=True)), "driver owner is absent from its physical map")
        displays.append({
            "name": driver.NativeName, "slot": driver.SlotName, "owner_slots": indices,
            "dimension_id": driver.DimensionValue.FieldsValue["f50"], "display_id": dim_fields["f58"],
            "parameter": driver.LiveValue, "cache": driver.CacheValue, "annotation_ids": members,
            "annotation_names": tuple(catalogue[key] for key in members),
            "label": vector(dim_fields["f6a0"]["f38"]),
        })
    expected_fields = expected["drivers"]
    expect([[row["name"], row["parameter"], row["cache"], row["display_id"], row["dimension_id"]] for row in displays]
           == expected_fields["typed_driver_values"] and len({key for row in displays for key in row["owner_slots"]}) == 24,
           "physical six-driver archive differs from the graph reconstruction")
    expect({row["name"]: [row["annotation_names"][0], row["annotation_ids"][0]]
            for row in displays if row["annotation_ids"]} == expected_fields["active_views"],
           "active physical annotation memberships differ and dormant displays must be unassigned")
    return displays


def check_solid(document, expected):
    (body,) = document.bodies
    geometry = document.brep
    topology = body.topology
    expect(geometry is not None and not document.brep_payloads and len(geometry.bodies) == len(geometry.shells) == 1
           and geometry.shells[0].closed and geometry.bodies[0].design_body_id == body.id
           and topology.solid_count == topology.shell_count == 1 and topology.valid,
           "ordinary strict open does not reconstruct the actual closed body")
    uses = Counter((coedge.edge_id, coedge.reversed) for coedge in geometry.coedges)
    expect(len(uses) == 2 * len(geometry.edges) and all(count == 1 for count in uses.values())
           and (topology.face_count, topology.edge_count, topology.vertex_count)
           == tuple(expected[key] for key in ("face_count", "edge_count", "vertex_count")),
           "strict reader changed incidence or the independently modeled topology")
    holes = {loop.id for loop in geometry.loops if not loop.outer}
    expect(len(holes) == expected["plate_hole_loops"]
           and sum(holes.issubset(face.loop_ids) for face in geometry.faces) == 1,
           "strict read no longer retains the shared face and each raised rim")
    box = topology.bounding_box
    bounds = tuple(getattr(point, key) for point in (box.minimum, box.maximum) for key in "xyz")
    center = tuple(body.attributes["solidworks.body_centroid_mm"])
    actual = (*bounds, *center, topology.volume, topology.surface_area)
    reference = (*expected["bounds_mm"], *expected["centroid_mm"], expected["volume_mm3"], expected["area_mm2"])
    expect(all(isclose(value, target, rel_tol=1e-12, abs_tol=1e-10)
               for value, target in zip(actual, reference, strict=True)), "strict open changed signed geometry")
    return {"bounds_mm": bounds, "centroid_mm": center, "face_count": topology.face_count,
            "volume_mm3": topology.volume, "area_mm2": topology.surface_area}


def check_graph(document, owner, displays, expected):
    (pattern,) = (step for step in document.feature_timeline if type(step.definition) is LinearPattern)
    steps = {step.id: step.name for step in document.feature_timeline}
    selection, = (item for item in document.selections if item.id == pattern.definition.direction_selection_id)
    (plane_ref,) = selection.path
    state = document.metadata[STATE]
    (body,) = document.bodies
    datum_name = expected["plane_name"]
    expect(not document.validate() and tuple(config.name for config in document.configurations) == ("Default",)
           and len(document.feature_timeline) == 22 and body.final_feature_id == pattern.id
           and tuple(steps[key] for key in pattern.input_feature_ids) == ("SeedBoss", datum_name)
           and plane_ref.entity_kind == "support_plane" and selection.name == datum_name
           and any(plane.id == plane_ref.entity_id and plane.name == datum_name for plane in document.support_planes)
           and pattern.definition.reversed == expected["reverse"]
           and state["status"] == "projected_cold_principal_direction" and state["physical_body_node"] is None
           and state["public_writer_qualified"] is False and body.attributes["solidworks.native_kernel_identity"] is False
           and list(state["native_atom_lineage"]) == expected["atom_lineage"],
           "normal strict SDK did not publish the actual editable feature or its named prior geometry")
    expect([[row[0], row[1], row[2]] for row in state["driver_roles"]]
           == [[row["name"], row["parameter"], row["cache"]] for row in displays],
           "inactive and live owner state did not survive normal neutral projection")
    params = {parameter.id: parameter for parameter in document.parameters}
    drivers = [params[key] for key in pattern.parameter_ids]
    expect([parameter.name for parameter in drivers] == ["D1", "D3"]
           and all(item.role.value == "driving" and item.owner_id == pattern.id and item.expression is None for item in drivers)
           and pattern.definition.instance_count == drivers[0].value.value == displays[0]["parameter"]
           and pattern.definition.spacing == drivers[1].value
           and drivers[1].value.unit == "mm" and drivers[1].value.value == displays[1]["parameter"] * 1000.0,
           "public editable parameters do not carry live count and pitch")
    for parameter, display, native in zip(drivers, displays[:2], owner.DriversValue[:2], strict=True):
        proof = parameter.attributes["typed_archive_owner"]
        indices = tuple(proof[key] for key in ("display_index", "handle_index", "dimension_index", "object_index"))
        expect(indices == display["owner_slots"] and proof["slot"] == native.SlotName
               and proof["dimension_id"] == display["dimension_id"] and proof["value_field"] == "f58"
               and parameter.attributes["native_display_cache"] == native.CacheValue,
               "portable live parameter detached from the actual native display and handle")
    return {"pattern_id": pattern.id, "parents": [steps[key] for key in pattern.input_feature_ids],
            "selection_id": selection.id, "support_plane_id": plane_ref.entity_id,
            "count": pattern.definition.instance_count, "pitch_mm": pattern.definition.spacing.value,
            "reversed": pattern.definition.reversed, "atoms": state["native_atom_lineage"]}


def refuse_writer(document):
    expect(not IsPatRead(document), "principal read entered the measured oblique write profile")
    output = BytesIO(b"unchanged")
    output.seek(2)
    try:
        write_document(document, output, destination_format=FORMAT, allow_carrier=False)
    except (RuntimeError, TypeError, ValueError) as error:
        expect(output.getvalue() == b"unchanged" and output.tell() == 2, "principal write refusal mutated the destination")
        return type(error).__name__
    raise ValueError("unmeasured principal read published a file")


def positive(path, data, expected):
    with boundary() as stream_reads:
        link, owner = typed(data)
        displays = verify_displays(link, owner, expected)
        full = open_document(BytesIO(data), source_format=FORMAT, strict=True)
        design = open_document(BytesIO(data), source_format=FORMAT, strict=True, include_brep=False)
        design_summary(full, design)
        geometry = check_solid(full, expected["solid"])
        graph = check_graph(full, owner, displays, expected)
        expect(check_graph(design, owner, displays, expected) == graph, "design-only pattern graph differs")
        round_full, round_design = loads(dumps(full)), loads(dumps(design))
        expect(check_graph(round_full, owner, displays, expected) == graph
               and check_solid(round_full, expected["solid"]) == geometry,
               "ordinary neutral JSON changed the editable pattern or reconstructed boundary")
        design_summary(full, round_design)
        write_guard = [refuse_writer(doc) for doc in (full, design)]
    with boundary(path) as path_reads:
        path_full = open_document(path, strict=True)
        path_design = open_document(path, configuration="Default", strict=True, include_brep=False)
        design_summary(path_full, path_design)
        expect(all(getattr(path_full, field) == getattr(full, field)
                   and getattr(path_design, field) == getattr(design, field) for field in EXACT_FIELDS),
               "normal native stream and path strict read interpretations differ")
        expect(path_full.source.sha256 == expected["payload_sha256"] == path_design.source.sha256,
               "opened path did not retain the pinned archive identity")
    return {"geometry": geometry, "graph": graph, "display_owners": displays,
            "stream_file_reads": len(stream_reads), "declared_path_reads": len(path_reads),
            "public_writer_refusals": write_guard}


def change_owner(graph, contrast):
    pattern = graph.PatternValue.FieldsValue
    _, pitch, _, idle, *_ = graph.DriverValues
    model = graph.StockValue.SystemValue.RootValue.FieldsValue
    views = model["fa48"].FieldsValue["items"]
    if contrast == "named_view_frame":
        views[0]["o"].FieldsValue["f368"] = views[-1]["o"].FieldsValue["f368"]
    elif contrast == "wrong_pitch_view":
        pitch.DisplayValue.FieldsValue["f2b0"] = ({"v": views[-1]["o"].FieldsValue["f360"]},)
    elif contrast == "dormant_view":
        idle.DisplayValue.FieldsValue.update(n2b0=1, f2b0=({"v": views[0]["o"].FieldsValue["f360"]},))
    elif contrast == "pitch_witness":
        pitch.DimensionValue.FieldsValue["f80"]["x"] += 0.002
    elif contrast == "stale_line":
        pattern["f1288"].FieldsValue["fc8"]["z"] += 0.002
    else:
        raise ValueError("unknown ordinary pattern ownership contrast")


def negative(contrast, diagnostic):
    case = {"name": "PrincipalReaderContrast", "axis": "x", "epoch": 1795590251, "count": 3, "pitch": 0.028,
            "plate": [[0, 0, 0], [0.161, 0.115, 0.012]], "seed": [[0.021, 0.034, 0], [0.033, 0.046, 0.023]],
            "count_label": [0.052, 0.035, 0.0], "idle_label": [0.021, 0.054, 0.0]}
    with boundary() as reads:
        graph = MakePatGraph(build_input(case))
        change_owner(graph, contrast)
        _, data = EmitPatArchive(graph)
        link, owner = typed(data)
        try:
            CheckPrincPat(link, owner)
        except ValueError as error:
            expect(diagnostic in str(error), "wrong typed refusal for principal owner contrast")
        else:
            raise ValueError("unwitnessed principal pattern owner passed")
        try:
            open_document(BytesIO(data), source_format=FORMAT, strict=True)
        except ValueError as error:
            expect("no readable Parasolid payload" in str(error), "wrong public failure for invalid cache-free history")
        else:
            raise ValueError("full strict open admitted an unsupported principal owner")
        fallback = open_document(BytesIO(data), source_format=FORMAT, strict=True, include_brep=False)
        expect(STATE not in fallback.metadata and fallback.brep is None
               and not any(type(step.definition) is LinearPattern for step in fallback.feature_timeline),
               "design fallback presented unsupported history as a verified pattern")
    return {"typed_refusal": diagnostic, "full_read_rejected": True, "design_pattern_not_projected": True,
            "runtime_reads": len(reads)}


def launch(mode, request, content=b""):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode), cwd=ROOT,
                 input=json.dumps(request, sort_keys=True).encode() + b"\n" + content,
                 capture_output=True, check=False, timeout=60)
    expect(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return json.loads(result.stdout)


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("read", "negative"))
    parser.add_argument("--origin", type=Path)
    parser.add_argument("--placed", type=Path)
    args = parser.parse_args()
    if args.worker:
        request = json.loads(sys.stdin.buffer.readline())
        content = sys.stdin.buffer.read()
        for module in (
            "interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
            "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentAssemblyValidate",
            "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
        ):
            import_module(module)
        for name in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
            lookup(name)
        outcome = (positive(Path(request["path"]), content, request["expected"]) if args.worker == "read"
                   else negative(request["contrast"], request["diagnostic"]))
        sys.stdout.buffer.write(wire(outcome))
        return
    expect(args.origin is not None and args.placed is not None, "both pinned origin and placed directories are needed")
    origins = json.loads(pinned(MEASUREMENTS / "LocalPrincipalPatternContainer01.json", ORIGIN_PIN))
    placed = json.loads(pinned(MEASUREMENTS / "LocalPlacedPrincipalPattern01.json", PLACED_PIN))
    cases = {
        "right_origin": (args.origin / "PrincipalRightOrigin.SLDPRT", origins["model_cases"]["right"]["initial"], "Right Plane", False),
        "top_origin": (args.origin / "PrincipalTopOrigin.SLDPRT", origins["model_cases"]["top"]["initial"], "Top Plane", True),
        "right_placed": (args.placed / "PlacedD01X.SLDPRT", placed["model_cases"]["D01X"]["original"]["generated"], "Right Plane", False),
        "top_placed": (args.placed / "PlacedD02Y.SLDPRT", placed["model_cases"]["D02Y"]["original"]["generated"], "Top Plane", True),
    }
    reports = {}
    for case, (path, reference, name, reverse) in cases.items():
        content = pinned(path, reference["payload_sha256"])
        report = launch("read", {"path": str(path.resolve()), "expected": dict(reference, plane_name=name, reverse=reverse)}, content)
        expect(report["stream_file_reads"] == 0 and report["declared_path_reads"] >= 2,
               "normal strict reads did not use exactly the designated native path")
        reports[case] = dict(report, archive_sha256=reference["payload_sha256"])
    contrasts = {
        "named_view_frame": "requires its canonical annotation frame",
        "wrong_pitch_view": "has a foreign display view or label",
        "dormant_view": "has a foreign display view or label",
        "pitch_witness": "does not match its actual witnesses and frame",
        "stale_line": "requires its actual signed datum line",
    }
    refusals = {name: launch("negative", {"contrast": name, "diagnostic": diagnostic}) for name, diagnostic in contrasts.items()}
    sys.stdout.buffer.write(wire({
        "schema": "kit.sw2026.strict-principal-pattern-read.v1", "base": BASE,
        "origin_model_receipt_sha256": ORIGIN_PIN, "placed_model_receipt_sha256": PLACED_PIN,
        "positive": reports, "refusals": refusals, "guarded_workers": 9,
        "strict_native_reads": 16, "exact_modeled_driver_owners": 24,
        "new_native_launches": 0, "native_writer_scope_changed": False,
        "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
    }))


if __name__ == "__main__":
    main()
