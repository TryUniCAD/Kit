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
SHAPE = HERE.parent.parent / "twostockshape"
BASE = "758c9f1ca1e75e6e00af40d83bdd75965dd78c54"
DISCLOSED = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
KEYWORDS = "swXmlContents/KeyWords"
FILES = (
    HERE,
    HERE.with_name("BuildTwoStockGraph.py"),
    HERE.with_name("LinkTwoStockGraph.py"),
    *(
        SHAPE / name
        for name in ("BuildTwoStockShape.py", "ShapeIntent.py", "ProofModels.py")
    ),
)
REFUSALS = {
    "joined-second": "independent extrusion requires its actual new solid mode",
    "crossed-depth": "independent stocks share an actual driving depth owner",
    "crossed-stock": "cut atom identity does not agree with its solid producer",
    "crossed-selection": "cut selection wrapper differs from the consumed boss atom",
    "premature-chooser": "pre-rebuild cut has an unproven result or chooser owner",
    "negative-support": "two stock archive graph requires canonical positive Front and Right supports",
    "reversed-stock": "two stock archive graph requires forward blind stock ends",
    "explicit-body-name": "two stock owner graph requires implicit feature-derived body names",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def make_document(values, mode):
    from ProofModels import authored_document

    document = authored_document(values)
    names = (
        ("AlphaSolid", "IndependentRightPrism", "RightScopeCut")
        if mode == "second-selected"
        else (
            "SteadyStock",
            "MovingStock",
            "ThroughFeature",
        )
    )
    labels = tuple(
        replace(owner, name=name)
        for owner, name in zip(document.feature_timeline, names, strict=True)
    )
    names_by_id = {owner.id: owner.name for owner in labels}
    bodies = tuple(
        replace(body, name=names_by_id[body.final_feature_id])
        for body in document.bodies
    )
    if mode == "explicit-body-name":
        bodies = (replace(bodies[0], name="Independent custom body label"), bodies[1])
    return replace(
        document,
        metadata={"name": "IndependentStockOwnerGraph"},
        feature_timeline=labels,
        bodies=bodies,
    )


def alter_roles(link, mode):
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
        ReadStockAtom,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
        ReadStockOps,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
        ReadStockRoots,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
        ReadSingleNode,
    )
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId

    first, second, cut = ReadStockOps(link, ReadStockRoots(link))
    if mode == "joined-second":
        second.NodeValue.FieldsValue["f810"] = 1
    elif mode == "crossed-depth":
        second.EndValue.FieldsValue["f18"] = first.EndValue.FieldsValue["f18"]
    elif mode == "crossed-stock":
        second.NodeValue.FieldsValue["f528"] = first.NodeValue.FieldsValue["f528"]
    elif mode == "crossed-selection":
        atom_id = ReadStockAtom(second.NodeValue, False).FieldsValue["f140"]
        wrapper = ReadSingleNode(cut.NodeValue.FieldsValue["f548"], "moCompSolidBody_c")
        wrapper.FieldsValue.update(
            f108=NativeNodeId(second.NodeValue),
            f18=atom_id,
            f1c=atom_id,
            f110=[{"v": atom_id}],
        )
    elif mode == "premature-chooser":
        cut.NodeValue.FieldsValue["has_f4c0"] = 1


def refused(callback, why):
    try:
        callback()
    except ValueError as error:
        require(str(error) == why, f"unexpected refusal: {error}")
        return str(error)
    raise ValueError(f"graph unexpectedly accepted: {why}")


def evaluate_model(values, mode):
    from BuildTwoStockGraph import build_owner_graph
    from LinkTwoStockGraph import link_graph, read_link, verify_link
    from ShapeIntent import xyz
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut import (
        ReadTwoStockCut,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.FindColdAtom import (
        FindColdAtom,
    )

    document = make_document(values, mode)
    if mode in {"negative-support", "reversed-stock", "explicit-body-name"}:
        return {
            "refusal": refused(
                lambda: build_owner_graph(document, 1795100000), REFUSALS[mode]
            )
        }
    graph = build_owner_graph(document, 1795100000)
    wire = link_graph(graph)
    link = read_link(wire)
    if mode in REFUSALS:
        alter_roles(link, mode)
        return {
            "refusal": refused(
                lambda: verify_link(graph, link, wire.keywords), REFUSALS[mode]
            )
        }
    stocks, cut = verify_link(graph, link, wire.keywords)
    cut_solid = next(
        solid
        for body, solid in zip(graph.shape.bodies, graph.shape.solids, strict=True)
        if body.final_feature_id == graph.shape.result_producer
    )
    return {
        "neutral_document_sha256": sha256(document.to_json().encode()).hexdigest(),
        "archive": [len(wire.payload), sha256(wire.payload).hexdigest()],
        "linked_round_trip": [
            "Contents/Config-0-ModelHeader",
            "Contents/CMgr",
            "Contents/Config-0",
            RESOLVED,
        ],
        "streams": {
            name: [len(value), sha256(value).hexdigest()]
            for name, value in wire.streams.items()
        },
        "stock_owners": stocks,
        "cut_owner": cut,
        "root_count": len(graph.ordered_roots),
        "body_order": [(body.id, body.final_feature_id) for body in graph.shape.bodies],
        "body_face_counts": [solid.topology.face_count for solid in graph.shape.solids],
        "cut_brep_sha256": sha256(repr(cut_solid.brep).encode()).hexdigest(),
        "combined_volume_area_com_mm": [
            graph.shape.volume_mm3,
            graph.shape.area_mm2,
            xyz(graph.shape.center_mm),
        ],
        "cut_intersects_untouched_stock": graph.shape.untouched_cutter_overlap,
        "ordinary_cold_reader_refusal": refused(
            lambda: FindColdAtom(link),
            "cold name requires one fresh actual atom manager member",
        ),
        "saved_lineage_refusal": (
            refused(
                lambda: ReadTwoStockCut(link),
                "two stock operation has alternate body collections",
            )
            if values["selected"] == 0
            else None
        ),
    }


def evaluate_saved(raw):
    from ShapeIntent import xyz
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut import (
        ReadTwoStockCut,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )

    require(
        sha256(raw).hexdigest() == DISCLOSED,
        "comparison received a different disclosed save",
    )
    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    saved = ReadTwoStockCut(link)
    result = []
    for position, owner in enumerate((*saved.StockValues, saved.CutValue)):
        node = owner.NodeValue
        values = node.FieldsValue
        dim = owner.RequireDepth().DepthValue if position < 2 else None
        result.append(
            {
                "feature_id": values["f08"],
                "profile_id": owner.ProfileValue.FieldsValue["f08"],
                "native_class": node.ClassValue.NameValue,
                "f810": values["f810"],
                "scope": values["f544"],
                "d1_id": dim.TypedOwner["dimension_id"] if dim else None,
                "depth_m": dim.native_value if dim else None,
                "signed_normal": xyz(saved.ProfileFrames[position].z_axis),
                "end_f158": owner.EndValue.FieldsValue["f158"],
                "owners_f4a8_f4b0_f4c0_f528_f530_f548": [
                    values[f"has_{key}"]
                    for key in ("f4a8", "f4b0", "f4c0", "f528", "f530", "f548")
                ],
            }
        )
    atoms = saved.AtomsValue
    wrapper = saved.WrapperValue.FieldsValue
    return {
        "owners": result,
        "selected_index": atoms.SelectedIndex,
        "realized_atoms": [
            [atom.FieldsValue[key] for key in ("f140", "f12c", "f144")]
            for atom in (atoms.ConsumedAtom, atoms.UntouchedAtom, atoms.ResultAtom)
        ],
        "wrapper": {
            "face_class": wrapper["ff0"].ClassValue.NameValue,
            "f108": wrapper["f108"],
            "f100": wrapper["f100"],
            "f104": wrapper["f104"],
        },
    }


def worker(mode):
    for entry in (REPO / "src", HERE.parent, SHAPE):
        sys.path.insert(0, str(entry))
    dependencies = (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Models.DocumentProvenance",
        "convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut",
    )
    task = (
        (
            "convert.adapters.solidworks.Container.Container",
            "convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink",
            "ShapeIntent",
        )
        if mode == "saved"
        else (
            "ProofModels",
            "BuildTwoStockGraph",
            "LinkTwoStockGraph",
            "convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.FindColdAtom",
        )
    )
    for dependency in (*dependencies, *task):
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
            raise PermissionError(f"owner graph worker attempted {event}")

    sys.addaudithook(guard)
    raw = sys.stdin.buffer.read()
    result = (
        evaluate_saved(raw)
        if mode == "saved"
        else evaluate_model(json.loads(raw), mode)
    )
    require(not attempts, "owner graph worker attempted external access")
    return {"result": result, "external_access_attempts": len(attempts)}


def run_worker(mode, data):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
        input=data,
        capture_output=True,
    )
    require(child.returncode == 0, f"{mode}: {child.stderr.decode()}")
    return json.loads(child.stdout)


def changed_streams(first, second):
    return {name for name, value in first.items() if value != second[name]}


def prove(source):
    for entry in (REPO / "src", SHAPE):
        sys.path.insert(0, str(entry))
    from ProofModels import AUTHORED, FRONT, RIGHT

    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    require(head == BASE, "use the exact cold owner graph baseline")
    clean = run(
        ("git", "diff", "--quiet", head, "--", "src", str(SHAPE.relative_to(REPO))),
        cwd=REPO,
    )
    require(
        clean.returncode == 0,
        "baseline production or geometry dependencies are modified",
    )
    initial = AUTHORED["disclosed-initial"]
    inputs = {
        "disclosed-initial": initial,
        "disclosed-depth-edit": AUTHORED["disclosed-depth-edit"],
        "second-selected": {
            "stocks": (
                (FRONT, (-12, 3, 3, 11), 7.5, False),
                (RIGHT, (-14, -20, -3, -6), 9.5, False),
            ),
            "circle": (2, -13, 7),
            "selected": 1,
            "result_first": True,
        },
        **dict.fromkeys(REFUSALS, initial),
        "negative-support": AUTHORED["signed-metre"],
        "reversed-stock": AUTHORED["interior-tunnel"],
    }
    request = {
        name: json.dumps(value, sort_keys=True).encode()
        for name, value in inputs.items()
    }
    phases = {name: run_worker(name, data) for name, data in request.items()}
    repeat = run_worker("disclosed-initial", request["disclosed-initial"])
    require(
        repeat == phases["disclosed-initial"],
        "independent generated archive bytes differ",
    )
    first, edited, second = (
        phases[name]["result"]
        for name in ("disclosed-initial", "disclosed-depth-edit", "second-selected")
    )
    require(
        not first["cut_intersects_untouched_stock"]
        and edited["cut_intersects_untouched_stock"]
        and first["stock_owners"][0] == edited["stock_owners"][0]
        and first["cut_owner"] == edited["cut_owner"]
        and first["cut_brep_sha256"] == edited["cut_brep_sha256"]
        and first["stock_owners"][1]["d1_id"] == edited["stock_owners"][1]["d1_id"]
        and isclose(edited["stock_owners"][1]["depth_m"], 0.029)
        and changed_streams(first["streams"], edited["streams"])
        == {RESOLVED, KEYWORDS},
        "upstream depth changed the selected history or unrelated streams",
    )
    require(
        second["cut_owner"]["selected_feature_id"]
        == second["stock_owners"][1]["feature_id"]
        and second["cut_owner"]["selected_atom_id"]
        == second["stock_owners"][1]["archive_atom_id"]
        and second["body_face_counts"] == [8, 6]
        and second["streams"][RESOLVED][0] != first["streams"][RESOLVED][0]
        and second["streams"][KEYWORDS][0] != first["streams"][KEYWORDS][0],
        "independent request lost its second actual stock selection or variable length",
    )
    path = source.resolve(strict=True)
    require(
        path.parts[-3:]
        == ("ThroughMultiStock03", "DisclosedNative", "ThroughMultiStock.SLDPRT")
        and not source.is_symlink(),
        "pass only the exact disclosed selected save",
    )
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == DISCLOSED, "disclosed comparison file differs")
    saved = run_worker("saved", raw)
    native = saved["result"]
    for generated, disclosed in zip(
        first["stock_owners"], native["owners"][:2], strict=True
    ):
        require(
            all(
                generated[key] == disclosed[key]
                for key in ("native_class", "f810", "signed_normal")
            )
            and isclose(generated["depth_m"], disclosed["depth_m"], rel_tol=1e-12),
            "typed disclosed stock differs from independent authored intent",
        )
    require(
        native["selected_index"] == 0
        and first["cut_owner"]["selected_feature_id"]
        == first["stock_owners"][0]["feature_id"]
        and all(
            first["cut_owner"][key] == native["owners"][2][key]
            for key in ("scope", "f810")
        )
        and sha256(path.read_bytes()).hexdigest() == DISCLOSED,
        "disclosed selected cut or immutable save differs",
    )
    processes = (*phases.values(), repeat, saved)
    return {
        "schema": "kit.sw2026.cold-two-stock-owner-graph.v1",
        "baseline": head,
        "tool_sha256": {
            str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest()
            for path in FILES
        },
        "disclosed_sha256": DISCLOSED,
        "disclosed_read_after_generation": True,
        "guarded_processes": len(processes),
        "external_access_attempts": sum(
            value["external_access_attempts"] for value in processes
        ),
        "independent_repeat_exact": True,
        "typed_refusals": {
            name: phases[name]["result"]["refusal"] for name in REFUSALS
        },
        "generated": {
            name: phases[name]["result"]
            for name in ("disclosed-initial", "disclosed-depth-edit", "second-selected")
        },
        "saved_typed_comparison": native,
        "in_memory_archive_only": True,
        "archive_files_written": 0,
        "native_acceptance_runs": 0,
        "held_out_cases": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--selected", type=Path)
    target.add_argument("--worker")
    args = parser.parse_args()
    result = worker(args.worker) if args.worker else prove(args.selected)
    print(json.dumps(result, indent=2, sort_keys=True))
