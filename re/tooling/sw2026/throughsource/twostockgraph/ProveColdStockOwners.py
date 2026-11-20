from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from math import isclose
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import codecs
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
SHAPES = HERE.parent.parent / "twostockshape"
PIN = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"
PACKET = "GeneratedTwoStockGraph01"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def guard():
    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    attempts = []

    def audit(event, _arguments):
        if event in {
            "open", "os.listdir", "os.scandir", "os.system", "os.exec",
            "os.fork", "os.posix_spawn", "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError("two-stock owner worker attempted " + event)

    sys.addaudithook(audit)
    return attempts


def generate():
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(SHAPES)]
    from BuildTwoStockGraph import build_owner_graph
    from LinkTwoStockGraph import link_graph
    from ProofModels import FRONT, RIGHT
    from ProveTwoStockGraph import make_document

    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Models.DocumentProvenance",
    ):
        import_module(name)
    attempts = guard()
    values = {
        "stocks": (
            (FRONT, (-14, 4, 1, 13), 8.75, False),
            (RIGHT, (-18, -24, -5, -4), 11.25, False),
        ),
        "circle": (1, -15, 8),
        "selected": 1,
        "result_first": True,
    }
    document = make_document(values, "second-selected")
    document = replace(document, metadata={"name": "TwoStockOwnershipContrast"})
    graph = build_owner_graph(document, 1795300000)
    part = link_graph(graph)
    require(len(part.streams) == 10 and not attempts, "contrast generation is not isolated")
    sys.stdout.buffer.write(part.payload)


def xyz(vector):
    return [vector.x, vector.y, vector.z]


def index_map(graph):
    return [graph.MapBase, graph.MapValue.CounterValue]


def observe(decoded):
    owners = []
    for owner, frame in zip(decoded.OwnerValues, decoded.ProfileFrames, strict=True):
        node, profile = owner.NodeValue, owner.ProfileValue
        support = profile.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]
        depth = owner.DepthValue
        owners.append({
            "feature_id": node.FieldsValue["f08"],
            "profile_id": profile.FieldsValue["f08"],
            "support_id": support,
            "storage_indices": [node.IndexValue, profile.IndexValue, owner.EndValue.IndexValue],
            "feature_class": node.ClassValue.NameValue,
            "operation_mode": node.FieldsValue["f810"],
            "selection_scope": node.FieldsValue["f544"],
            "reversed": owner.IsReversed,
            "signed_frame": [xyz(value) for value in (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis)],
            "driver": None if depth is None else {
                "name": depth.DepthValue.name,
                "depth_m": depth.DepthValue.native_value,
                "native_owner": dict(depth.DepthValue.TypedOwner),
                "name_index": depth.Parameter.FieldsValue["f18"].IndexValue,
                            "modeled_owner_fields": [
                                "owner" in item.FieldsValue
                                for item in (
                                    depth.DisplayValue, depth.HandleValue,
                                    depth.Dimension, depth.Parameter,
                                )
                            ],
                            "retaining_handles_field": "retaining_handles" in depth.Dimension.FieldsValue,
            },
        })
    link = decoded.LinkValue
    manager = link.ConfigValue.RootValue.FieldsValue["fd88"]
    wrapper = decoded.WrapperValue.FieldsValue
    return {
        "owners": owners,
        "selected_index": decoded.SelectedIndex,
        "selected_atom_id": decoded.SelectedAtomId,
        "manager": {
            "next_word": manager["f260"],
            "rows": [
                {key: atom.FieldsValue[key] for key in ("f140", "f12c", "f130", "f144", "body_kind")}
                | {"index": atom.IndexValue}
                for atom in decoded.StockAtoms
            ],
        },
        "selection": {
            **{key: wrapper[key] for key in ("f108", "f18", "f1c", "f110", "f100", "f104")},
            "wrapper_index": decoded.WrapperValue.IndexValue,
            "component_index": wrapper["f58"].IndexValue,
            "face_carrier_present": wrapper["ff0"] is not None,
        },
        "cut_result_present": decoded.OwnerValues[2].NodeValue.FieldsValue["has_f528"] != 0,
        "consumed_atom_present": decoded.OwnerValues[2].NodeValue.FieldsValue["has_f530"] != 0,
        "config_map": index_map(link.ConfigValue),
        "resolved_map": index_map(link.ResolvedValue),
    }


def inspect_worker(mode):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]
    from ColdStockOwnerFaults import FAULTS, damage
    from ReadColdStockOwners import decode_cold_stock_owners, read_cold_stock_owners
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    attempts = guard()
    raw = sys.stdin.buffer.read()
    archive = SldprtArchive.from_bytes(raw)
    decoded = read_cold_stock_owners(archive)
    if mode != "read":
        try:
            decode_cold_stock_owners(damage(decoded, mode))
        except ValueError as error:
            require(FAULTS[mode] in str(error), f"wrong refusal for {mode}: {error}")
            report = {"refused": str(error)}
        else:
            raise ValueError(f"damaged graph {mode} unexpectedly decoded")
    else:
        link = decoded.LinkValue
        config, resolved = link.ConfigValue, link.ResolvedValue
        header = config.HeaderValue
        version = config.VersionValue
        manager_name = "Contents/CMgr"
        manager = ReadCmgrMut(archive.streams[manager_name], version)
        context = MakeLinkContext(config, manager)
        exact = {
            link.ConfigName + "-ModelHeader": WriteHeadGraph(header, version),
            manager_name: WriteCmgrMut(manager.RootValue, version),
            link.ConfigName: WriteConfigMut(config.RootValue, version, header)[0],
            link.StreamName: WriteResolMut(
                resolved.RootsValue, resolved.ExtraFields, version, config.MapValue, context
            )[0],
        }
        require(all(archive.streams[name] == data for name, data in exact.items()),
                "ownership observation changed a linked stream")
        report = observe(decoded) | {
            "archive": [len(raw), digest(raw)],
            "linked_streams": {name: [len(data), digest(data)] for name, data in exact.items()},
        }
    require(not attempts, "owner observation attempted external access")
    print(json.dumps(report | {"external_access_attempts": len(attempts)}, sort_keys=True, allow_nan=False))


def launch(mode, cwd, data=None):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
        cwd=cwd, input=data, capture_output=True, timeout=120,
    )
    require(child.returncode == 0 and not child.stderr, f"{mode}: {child.stderr.decode()}")
    if mode == "generate":
        return child.stdout
    report = json.loads(child.stdout)
    require(report["external_access_attempts"] == 0, "worker changed external access count")
    return report


def check_behavior(case, index, depths):
    owners = case["owners"]
    atoms, selection = case["manager"]["rows"], case["selection"]
    require(case["selected_index"] == index and case["selected_atom_id"] == atoms[index]["f140"],
            "decoded stock selection differs from the experiment")
    require(selection["f108"] == owners[index]["feature_id"]
            and [selection[key] for key in ("f18", "f1c")] == [case["selected_atom_id"]] * 2
            and owners[2]["support_id"] == owners[index]["support_id"], "report lost actual archive references")
    require(all(isclose(owner["driver"]["depth_m"], depth, rel_tol=1e-15)
                for owner, depth in zip(owners[:2], depths, strict=True)), "typed D1 values differ")
    require(owners[2]["driver"] is None and not (
        selection["face_carrier_present"] or case["cut_result_present"] or case["consumed_atom_present"]
    ), "provisional graph incorrectly reported realized cut state")


def prove(path):
    require(path.name == PACKET + ".SLDPRT" and path.parent.name == PACKET
            and not path.is_symlink(), "pass the disclosed generated candidate")
    with TemporaryDirectory(prefix="KitColdStockOwners-") as folder:
        contrast = launch("generate", folder)
        require(contrast == launch("generate", folder) and digest(contrast) != PIN,
                "the independent contrast failed deterministic generation")
        raw = path.read_bytes()
        require(digest(raw) == PIN, "disclosed generated candidate SHA-256 changed")
        first = launch("read", folder, raw)
        second = launch("read", folder, contrast)
        check_behavior(first, 0, (0.012, 0.010))
        check_behavior(second, 1, (0.00875, 0.01125))
        sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]
        from ColdStockOwnerFaults import FAULTS

        refusals = {name: launch(name, folder, raw) for name in FAULTS}
        require(digest(path.read_bytes()) == PIN and not list(Path(folder).iterdir()),
                "audit changed a disclosed or scratch file")
    return {
        "schema": "kit.sw2026.cold-two-stock-owner-read.v1",
        "disclosed": first,
        "independent_second_selected": second,
        "contrast_generation": {"deterministic_repetitions": 2, "external_access_attempts": 0},
        "corrupt_owners": refusals,
        "fresh_processes": 4 + len(refusals),
        "native_runs": 0,
        "heldout_sources_read": 0,
        "public_sdk_changed": False,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--worker")
    args = parser.parse_args()
    if args.worker == "generate":
        generate()
    elif args.worker:
        inspect_worker(args.worker)
    else:
        require(args.source is not None, "pass the exact disclosed generated archive")
        print(json.dumps(prove(args.source), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
