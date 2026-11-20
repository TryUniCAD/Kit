from argparse import ArgumentParser
from hashlib import sha256
from importlib import import_module
from math import isclose
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
SHAPE = HERE.parent.parent / "twostockshape"
GENERATED = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"
NATIVE_SAVED = "236865bd1e13e246199429ad635da99a737b6280802c61df252c92d613275452"
NATIVE_RECEIPT = "d672ec1f8d427844410a7e2d809bfbcf0d130ecaf1df1bb78cefdd1f5f64e187"
SCHEMA = "kit.sw2026.disclosed-cache-free-stock-rebuild.v1"


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def identity(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def pinned(path, digest):
    require(path.is_file() and not path.is_symlink(), "missing or redirected disclosed input")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, "disclosed input changed")
    return raw


def reconstruct(raw):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from ReadColdStockOwners import read_cold_stock_owners
    from RebuildColdStockShape import rebuild_cold_stock_shape

    ownership = read_cold_stock_owners(SldprtArchive.from_bytes(raw))
    shape = rebuild_cold_stock_shape(ownership)
    require(
        len(shape.brep.bodies) == 2
        and not shape.brep.validate(frozenset(body.id for body in shape.bodies)),
        "both independently reconstructed body owners are required",
    )
    return {
        "archive": identity(raw),
        "selected_index": ownership.SelectedIndex,
        "selected_atom": ownership.SelectedAtomId,
        "selected_producer": shape.selected_producer,
        "untouched_producer": shape.untouched_producer,
        "result_producer": shape.result_producer,
        "selection_id": shape.selection_id,
        "untouched_intersects_tool": shape.untouched_cutter_overlap,
        "bodies": {
            body.name: {
                "id": body.id, "final_feature_id": body.final_feature_id,
                "volume_mm3": body.topology.volume, "area_mm2": body.topology.surface_area,
                "centre_mm": [solid.center_mm.x, solid.center_mm.y, solid.center_mm.z],
                "faces": len(solid.brep.faces), "solid_count": body.topology.solid_count,
            }
            for body, solid in zip(shape.bodies, shape.solids, strict=True)
        },
    }


def independent_input(mode):
    from BuildTwoStockGraph import build_owner_graph
    from LinkTwoStockGraph import link_graph
    from ProofModels import AUTHORED, FRONT, RIGHT
    from ProveTwoStockGraph import make_document

    values = AUTHORED["disclosed-depth-edit"] if mode == "edited" else {
        "stocks": (
            (FRONT, (-12, 3, 3, 11), 7.5, False),
            (RIGHT, (-14, -20, -3, -6), 9.5, False),
        ),
        "circle": (2, -13, 7), "selected": 1, "result_first": True,
    }
    document = make_document(values, "second-selected" if mode == "second" else mode)
    return link_graph(build_owner_graph(document, 1765500071)).payload


def worker(mode):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(SHAPE)]
    for module in (
        "ReadColdStockOwners", "RebuildColdStockShape", "BuildTwoStockGraph",
        "LinkTwoStockGraph", "ProofModels", "ProveTwoStockGraph",
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    attempts = []

    def audit(event, _):
        if event in {
            "open", "os.listdir", "os.scandir", "os.system", "os.exec",
            "os.fork", "os.posix_spawn", "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError("cold stock reconstruction attempted " + event)

    sys.addaudithook(audit)
    raw = sys.stdin.buffer.read()
    if mode in ("edited", "second"):
        require(not raw, "fresh authored input cannot use archive bytes")
        raw = independent_input(mode)
    if mode == "saved":
        try:
            reconstruct(raw)
        except ValueError as error:
            require(str(error) == "provisional two-stock ownership excludes stored body caches", str(error))
            value = {"archive": identity(raw), "refusal": str(error)}
        else:
            raise ValueError("native-saved cached bodies reached the cold path")
    else:
        value = reconstruct(raw)
    require(not attempts, "cold stock reconstruction attempted external access")
    return {**value, "runtime_access_attempts": len(attempts)}


def compare_measures(rebuilt, native, names):
    for generated, reached in names:
        actual, expected = rebuilt["bodies"][generated], native["bodies"][reached]
        require(
            actual["solid_count"] == 1
            and all(
                isclose(actual[key], expected[key], rel_tol=2e-7, abs_tol=1e-10)
                for key in ("volume_mm3", "area_mm2")
            )
            and all(
                isclose(left, right, rel_tol=2e-7, abs_tol=1e-7)
                for left, right in zip(actual["centre_mm"], expected["centre_mm"], strict=True)
            ),
            "analytically reconstructed stock differs from native geometry",
        )


def prove(packet):
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    inputs = {
        "initial": pinned(packet / "GeneratedTwoStockGraph01.SLDPRT", GENERATED),
        "edited": b"",
        "second": b"",
        "saved": pinned(packet / "NativeAfterEdit.SLDPRT", NATIVE_SAVED),
    }
    observed = {}
    for mode, raw in inputs.items():
        worker_result = run(
            (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
            input=raw, capture_output=True, timeout=90,
        )
        require(worker_result.returncode == 0, worker_result.stderr.decode())
        observed[mode] = json.loads(worker_result.stdout)
    receipt_path = ROOT / "re/solidworks/measurements/2026/TwoStockColdNative01.json"
    native = json.loads(pinned(receipt_path, NATIVE_RECEIPT))["snapshots"]
    initial, edited, second = (observed[mode] for mode in ("initial", "edited", "second"))
    names = (("MovingStock", "MovingStock"), ("ThroughFeature", "SteadyStock"))
    compare_measures(initial, native["initial"], names)
    compare_measures(edited, native["fresh_reopen"], names)
    require(
        initial["selected_index"] == edited["selected_index"] == 0
        and second["selected_index"] == 1
        and initial["selected_atom"] == edited["selected_atom"] != second["selected_atom"]
        and not initial["untouched_intersects_tool"] and edited["untouched_intersects_tool"]
        and initial["bodies"]["ThroughFeature"] == edited["bodies"]["ThroughFeature"]
        and set(second["bodies"]) == {"AlphaSolid", "RightScopeCut"},
        "the actual cut selector or stock edit changed reconstructed ownership",
    )
    tool_files = (
        HERE, HERE.with_name("ReadColdStockOwners.py"),
        HERE.with_name("RebuildColdStockShape.py"), SHAPE / "BuildTwoStockShape.py",
    )
    return {
        "schema": SCHEMA, "source_revision": revision, "native_receipt_sha256": NATIVE_RECEIPT,
        "tool_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in tool_files},
        "guarded_processes": len(observed), "phases": observed,
        "native_oracle_processes": 0, "held_out_cases": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--packet", type=Path)
    mode.add_argument("--worker", choices=("initial", "edited", "second", "saved"))
    args = parser.parse_args()
    result = worker(args.worker) if args.worker else prove(args.packet)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
