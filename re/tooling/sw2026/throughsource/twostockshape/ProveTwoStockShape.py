from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from math import isclose
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
BASE = "41a1fa2fa0d303a2cd0c923a8eef7f54670b82fa"
DISCLOSED = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
NATIVE_MEASURES = "d669f3ff61b7ece7ddc5ab50069ccb4ed7dbbb923abe9931db22806697f61ac4"
FILES = (
    "ShapeIntent.py",
    "BuildTwoStockShape.py",
    "MeasureCap.py",
    "ProofModels.py",
    HERE.name,
)
REFUSALS = {
    "cached-model": "cold shape refuses cached geometry or native payloads",
    "cached-payload": "cold shape refuses cached geometry or native payloads",
    "missing-selection": "cold shape needs exactly two stocks and one explicitly selected cut",
    "crossed-selection": "ordinary extrusion requires active unextended features with the admitted dependency order",
    "crossed-result-body": "final bodies must retain the untouched and cut-result producers",
    "split-driver": "stock D1 disagrees with its live blind length",
    "away-direction": "through direction does not cover the selected stock",
    "unknown-direction": "through direction does not cover the selected stock",
    "overlapping-stocks": "the two original stocks must have positive separation",
    "side-tangency": "circular through cut requires one enclosed hole or one proper exterior side notch",
    "crossed-corner": "circular notch crosses a corner, touches a wall or cuts multiple stock sides",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected):
    if isinstance(expected, (tuple, list)):
        return len(actual) == len(expected) and all(
            close(a, b) for a, b in zip(actual, expected, strict=True)
        )
    return isclose(actual, expected, rel_tol=5e-9, abs_tol=5e-7)


def changed_cut(document, **fields):
    cut = document.feature_timeline[-1]
    return replace(
        document,
        feature_timeline=(*document.feature_timeline[:2], replace(cut, **fields)),
    )


def changed_definition(document, **fields):
    return changed_cut(
        document, definition=replace(document.feature_timeline[-1].definition, **fields)
    )


def altered_document(document, source, mode):
    from BuildTwoStockShape import build_two_stock_shape
    from ProofModels import authored_document
    from interchange.geometry.Models.Selection import SelectPathElem
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from interchange.Payloads.PayloadRecord import BrepPayload

    if mode == "cached-model":
        return replace(document, brep=build_two_stock_shape(document).brep)
    if mode == "cached-payload":
        synthetic = b"independent payload sentinel"
        record = BrepPayload(
            "cached-input",
            "parasolid",
            "partition",
            "synthetic",
            sha256(synthetic).hexdigest(),
            synthetic,
            "synthetic",
        )
        return replace(document, brep_payloads=(record,))
    if mode == "missing-selection":
        return replace(changed_cut(document, selection_ids=()), selections=())
    if mode == "crossed-selection":
        wrong = SelectPathElem("feature", document.feature_timeline[1].id, "body")
        return replace(
            document, selections=(replace(document.selections[0], path=(wrong,)),)
        )
    if mode == "crossed-result-body":
        body = replace(
            document.bodies[0], final_feature_id=document.feature_timeline[0].id
        )
        return replace(document, bodies=(body, document.bodies[1]))
    if mode == "split-driver":
        first, last = document.parameters
        return replace(
            document,
            parameters=(replace(first, value=replace(first.value, value=9.75)), last),
        )
    if mode == "away-direction":
        return changed_definition(document, direction=SpaceVector(0, 0, -1))
    if mode == "unknown-direction":
        return changed_definition(document, direction=None)
    first, second = source["stocks"]
    if mode == "overlapping-stocks":
        pose, _, _, reverse = second
        return authored_document(
            {**source, "stocks": (first, (pose, (-16, -7, -2, 2), 29, reverse))}
        )
    if mode == "side-tangency":
        return authored_document({**source, "circle": (21, 4, 8)})
    if mode == "crossed-corner":
        return authored_document({**source, "circle": (13, 0, 8)})
    raise ValueError("unknown cold shape contrast")


def measure(solid, stock):
    from MeasureCap import topology_measure
    from ShapeIntent import xyz

    topology = solid.topology
    measured = topology_measure(solid, stock)
    expected = (topology.volume, topology.surface_area, xyz(solid.center_mm))
    require(
        close(measured[:3], expected),
        "actual boundary integrals differ from generated physical measures",
    )
    points = sorted(
        tuple(round(value, 9) for value in xyz(vertex.point))
        for vertex in solid.brep.vertices
    )
    require(
        len(points) == len(set(points)), "generated prism has repeated vertex positions"
    )
    return {
        "brep_sha256": sha256(repr(solid.brep).encode()).hexdigest(),
        "body_id": solid.brep.bodies[0].design_body_id,
        "brep_body_id": solid.brep.bodies[0].id,
        "counts_solid_shell_face_edge_vertex": [
            topology.solid_count,
            topology.shell_count,
            topology.face_count,
            topology.edge_count,
            topology.vertex_count,
        ],
        "euler": measured[3],
        "volume_mm3": topology.volume,
        "area_mm2": topology.surface_area,
        "center_mm": xyz(solid.center_mm),
        "bounds_mm": (
            *xyz(topology.bounding_box.minimum),
            *xyz(topology.bounding_box.maximum),
        ),
        "points_mm": points,
        "integral_errors": [
            abs(measured[0] - expected[0]),
            abs(measured[1] - expected[1]),
            max(abs(a - b) for a, b in zip(measured[2], expected[2], strict=True)),
        ],
    }


def evaluate_model(values, mode):
    from BuildTwoStockShape import build_two_stock_shape
    from ProofModels import authored_document
    from ShapeIntent import project_intent, xyz

    document = authored_document(values)
    if mode in REFUSALS:
        document = altered_document(document, values, mode)
        try:
            build_two_stock_shape(document)
        except ValueError as error:
            require(str(error) == REFUSALS[mode], f"unexpected {mode} refusal: {error}")
            return {"refusal": str(error)}
        raise ValueError(f"unsupported {mode} geometry unexpectedly qualified")
    require(
        document.brep is None and not document.brep_payloads,
        "authored request already carries geometry",
    )
    result = build_two_stock_shape(document)
    intent = project_intent(document)
    compare = {
        result.untouched_producer: intent.untouched,
        result.result_producer: intent.selected,
    }
    require(
        tuple(body.final_feature_id for body in result.bodies)
        == tuple(body.final_feature_id for body in document.bodies),
        "body order or producer identity changed",
    )
    require(
        tuple(body.id for body in result.bodies)
        == tuple(body.design_body_id for body in result.brep.bodies)
        and len(result.brep.bodies)
        == len(result.brep.regions)
        == len(result.brep.shells)
        == 2,
        "composed B-rep no longer matches its two body and region roles",
    )
    measured = {
        body.final_feature_id: measure(solid, compare[body.final_feature_id])
        for body, solid in zip(result.bodies, result.solids, strict=True)
    }
    stock, untouched, cut = (
        measure(result.selected_stock, intent.selected),
        measured[result.untouched_producer],
        measured["cut"],
    )
    require(
        untouched["counts_solid_shell_face_edge_vertex"] == [1, 1, 6, 12, 8]
        and untouched["euler"] == stock["euler"] == 2,
        "independent box topology changed",
    )
    require(
        (cut["counts_solid_shell_face_edge_vertex"], cut["euler"])
        == (
            ([1, 1, 7, 14, 10], 0)
            if mode == "interior-tunnel"
            else ([1, 1, 8, 18, 12], 2)
        ),
        "cut topology differs from the authored branch",
    )
    require(
        result.untouched_cutter_overlap == (mode == "disclosed-depth-edit"),
        "actual ray intersection with the untouched stock changed",
    )
    return {
        "untouched": untouched,
        "selected_before_cut": stock,
        "cut_result": cut,
        "selected_producer": result.selected_producer,
        "untouched_producer": result.untouched_producer,
        "result_producer": result.result_producer,
        "selection_id": result.selection_id,
        "body_order": [body.id for body in result.bodies],
        "directions": {
            "selected_normal": xyz(intent.selected.frame.z_axis),
            "untouched_normal": xyz(intent.untouched.frame.z_axis),
            "through_world": xyz(intent.cutter_direction),
        },
        "untouched_cutter_overlap": result.untouched_cutter_overlap,
        "combined_mm": [result.volume_mm3, result.area_mm2, xyz(result.center_mm)],
        "combined_brep_sha256": sha256(repr(result.brep).encode()).hexdigest(),
    }


def evaluate_saved(raw):
    from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from ReadTwoStockHistory import read_history

    require(
        sha256(raw).hexdigest() == DISCLOSED,
        "comparison got a different disclosed file",
    )
    states, _, _, scope = read_history(SldprtArchive.from_bytes(raw))
    require(scope == 1, "comparison requires the actual saved selected scope")
    actual = {}
    for state in states:
        bodies = {}
        for body in state.bodies:
            edges = WalkXmtChain(
                state.nodes, state.nodes[body.slot].Integer("edge"), 16
            )
            bodies[body.label] = {
                "atom": body.atom,
                "feature": body.feature,
                "counts_face_edge_vertex": [
                    len(body.faces),
                    len(edges),
                    len(body.points),
                ],
                "points_mm": body.points,
            }
        actual[str(state.mark_id)] = bodies
    return actual


def worker(mode):
    for entry in (REPO / "src", HERE.parent, HERE.parent.parent):
        sys.path.insert(0, str(entry))
    common = (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Models.DocumentProvenance",
    )
    task = (
        (
            "ReadTwoStockHistory",
            "convert.adapters.solidworks.Container.Container",
            "convert.adapters.solidworks.Archive.Partition.WalkXmtChain",
        )
        if mode == "saved-geometry"
        else ("BuildTwoStockShape", "MeasureCap", "ProofModels")
    )
    for dependency in (*common, *task):
        import_module(dependency)
    for encoding in (
        "ascii",
        "latin-1",
        "utf-8",
        "utf-8-sig",
        "utf-16-le",
        "utf-16-be",
    ):
        codecs.lookup(encoding)
    attempts = []

    def guard(event, _):
        if event in {
            "open",
            "os.listdir",
            "os.scandir",
            "os.system",
            "os.exec",
            "os.fork",
            "os.posix_spawn",
            "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError(f"cold shape worker attempted {event}")

    sys.addaudithook(guard)
    raw = sys.stdin.buffer.read()
    if mode == "saved-geometry":
        result = evaluate_saved(raw)
    else:
        result = evaluate_model(json.loads(raw), mode)
    require(not attempts, "cold shape worker attempted external access")
    return {"result": result, "external_access_attempts": len(attempts)}


def compare_disclosed(initial, edited, observed, native_path):
    def check_shape(shape, body):
        require(
            shape["counts_solid_shell_face_edge_vertex"][2:]
            == body["counts_face_edge_vertex"]
            and close(shape["points_mm"], body["points_mm"]),
            "model-only solid differs from actual saved owner dimensions or topology",
        )

    check_shape(initial["untouched"], observed["21"]["MovingStock"])
    check_shape(initial["cut_result"], observed["21"]["ThroughFeature"])
    check_shape(initial["selected_before_cut"], observed["18"]["SteadyStock"])
    check_shape(initial["untouched"], observed["18"]["MovingStock"])
    check_shape(initial["selected_before_cut"], observed["16"]["SteadyStock"])
    require(
        not observed["3"] and not observed["1"],
        "unexpected prior solid before both bosses",
    )
    require(
        initial["cut_result"] == edited["cut_result"]
        and initial["selected_before_cut"] == edited["selected_before_cut"],
        "editing the untouched stock changed selected cut geometry",
    )
    measured = native_path.read_bytes()
    require(
        sha256(measured).hexdigest() == NATIVE_MEASURES,
        "disclosed native measurements differ",
    )
    native = json.loads(measured)["automatic_geometry"]
    require(
        native["source_sha256"] == DISCLOSED and native["source_unchanged"],
        "native receipt is from another source",
    )
    for shape, phase in ((initial, "before_edit"), (edited, "after_edit")):
        for role, name in (("untouched", "MovingStock"), ("cut_result", "SteadyStock")):
            record = native["reopen"][phase]["bodies"][name]
            physical = shape[role]
            actual = (
                physical["volume_mm3"],
                physical["area_mm2"],
                physical["center_mm"],
                physical["bounds_mm"],
            )
            expected = (
                record["volume_m3"] * 1e9,
                record["area_m2"] * 1e6,
                [v * 1000 for v in record["com_m"]],
                [v * 1000 for v in record["box_m"]],
            )
            require(
                close(actual, expected),
                f"independent native body measures differ at {phase}/{name}",
            )


def run_worker(mode, data):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
        input=data,
        capture_output=True,
    )
    require(child.returncode == 0, f"{mode}: {child.stderr.decode()}")
    return json.loads(child.stdout)


def prove(selected):
    sys.path.insert(0, str(REPO / "src"))
    sys.path.insert(0, str(HERE.parent))
    from ProofModels import AUTHORED

    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    fingerprints = {name: sha256((HERE.parent / name).read_bytes()).hexdigest() for name in FILES}
    phases = {}
    requests = {**AUTHORED, **dict.fromkeys(REFUSALS, AUTHORED["disclosed-initial"])}
    for mode, values in requests.items():
        phases[mode] = run_worker(mode, json.dumps(values, sort_keys=True).encode())
    initial, edited = (
        phases[label]["result"]
        for label in ("disclosed-initial", "disclosed-depth-edit")
    )
    repeated = run_worker(
        "disclosed-depth-edit",
        json.dumps(AUTHORED["disclosed-depth-edit"], sort_keys=True).encode(),
    )
    require(
        repeated == phases["disclosed-depth-edit"], "fresh independent builds disagree"
    )
    source = selected.resolve(strict=True)
    require(
        source.parts[-3:]
        == ("ThroughMultiStock03", "DisclosedNative", "ThroughMultiStock.SLDPRT")
        and not selected.is_symlink(),
        "pass only the exact disclosed selected save",
    )
    raw = source.read_bytes()
    require(sha256(raw).hexdigest() == DISCLOSED, "disclosed comparison file differs")
    saved = run_worker("saved-geometry", raw)
    compare_disclosed(
        initial,
        edited,
        saved["result"],
        REPO
        / "re/solidworks/measurements/2026/ThroughAllMultiStockScopeObserved01.json",
    )
    require(
        sha256(source.read_bytes()).hexdigest() == DISCLOSED,
        "disclosed comparison file changed",
    )
    totals = sum(
        value["external_access_attempts"]
        for value in (*phases.values(), repeated, saved)
    )
    for case in AUTHORED:
        for solid in ("untouched", "selected_before_cut", "cut_result"):
            phases[case]["result"][solid].pop("points_mm")
    require(
        check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip() == head
        and all(sha256((HERE.parent / name).read_bytes()).hexdigest() == digest for name, digest in fingerprints.items()),
        "the geometry implementation changed during verification",
    )
    return {
        "schema": "kit.sw2026.cold-two-stock-neutral-shape.v1",
        "baseline": BASE,
        "implementation_head": head,
        "tool_sha256": fingerprints,
        "source_read_after_all_generation": True,
        "selected_comparison_sha256": DISCLOSED,
        "native_receipt_sha256": NATIVE_MEASURES,
        "saved_active_and_rollback_geometry_agrees": True,
        "previous_native_open_and_edit_measures_agree": True,
        "saved_comparison_access_attempts": saved["external_access_attempts"],
        "worker_count": len(phases) + 2,
        "external_access_attempts": totals,
        "fresh_edited_builds_match": True,
        "native_processes_run": 0,
        "native_files_generated": 0,
        "heldout_sources": 0,
        "writer_qualified": False,
        "phases": phases,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--selected", type=Path)
    parser.add_argument("--worker")
    args = parser.parse_args()
    require(
        (args.selected is None) != (args.worker is None),
        "pass the scoped supervisor or worker mode",
    )
    result = worker(args.worker) if args.worker else prove(args.selected)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
