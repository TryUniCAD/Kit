from argparse import ArgumentParser
from copy import copy
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
BASE = "7f3111e101a0e1a83b3177de7b5c6e4af9024e6f"
SOURCE_SHA = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
SOURCE_SUFFIX = ("ThroughMultiStock03", "DisclosedNative", "ThroughMultiStock.SLDPRT")
TYPED = REPO / "src/convert/adapters/solidworks/Core/TypedResolved"
REFUSALS = {
    "reselect-untouched": "cut selection wrapper differs from the consumed boss atom",
    "cross-face-producer": "two stock face carrier does not resolve to its selected producer",
    "detached-managed-atom": "cut body atom manager contains missing or additional ownership",
    "consume-cut-output": "two stock cut does not consume an actual independent stock",
    "lose-new-solid-mode": "independent extrusion requires its actual new solid mode",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reject(action, expected):
    try:
        action()
    except ValueError as error:
        require(str(error) == expected, f"unexpected refusal {error}")
        return str(error)
    raise ValueError("altered ownership incorrectly qualified")


def mutate(link, positive, mode):
    first, second = positive.StockValues
    cut = positive.CutValue.NodeValue
    atoms = positive.AtomsValue
    wrapper = positive.WrapperValue.FieldsValue
    if mode == "reselect-untouched":
        atom_id = atoms.UntouchedAtom.FieldsValue["f140"]
        wrapper.update(f18=atom_id, f1c=atom_id, f108=second.NodeValue.FieldsValue["f08"], f110=[{"v": atom_id}])
    elif mode == "cross-face-producer":
        rep = wrapper["ff0"].FieldsValue["f10"][0]["f08"]
        ref = rep.FieldsValue["f10"]["f10"]
        ref.FieldsValue["f10"]["f00"] = second.NodeValue.FieldsValue["f08"]
    elif mode == "detached-managed-atom":
        rows = link.ConfigValue.RootValue.FieldsValue["fd88"]["atoms"]
        (owner,) = [row for row in rows if row["o"] is atoms.UntouchedAtom]
        owner["o"] = copy(atoms.UntouchedAtom)
    elif mode == "consume-cut-output":
        cut.FieldsValue["f530"]["items"][0]["o"] = atoms.ResultAtom
    elif mode == "lose-new-solid-mode":
        second.NodeValue.FieldsValue["f810"] = first.NodeValue.FieldsValue["f810"]
    else:
        raise ValueError("unknown multistock proof mode")


def worker(mode):
    sys.path.insert(0, str(REPO / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import CheckCutScope
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut import ReadTwoStockCut
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    for encoding in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(encoding)
    for dependency in (
        "interchange.brep.Curves.BrepCurves",
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(dependency)
    attempts = []

    def protect(event, _):
        if (event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.fork", "os.posix_spawn", "os.startfile"}
                or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))):
            attempts.append(event)
            raise PermissionError("multistock lineage attempted external access: " + event)

    sys.addaudithook(protect)
    payload = sys.stdin.buffer.read()
    require(sha256(payload).hexdigest() == SOURCE_SHA, "worker received a different disclosed source")
    link = ReadNativeLink(SldprtArchive.from_bytes(payload), 0)
    lineage = ReadTwoStockCut(link)
    if mode != "original":
        mutate(link, lineage, mode)
        result = {"refusal": reject(lambda: ReadTwoStockCut(link), REFUSALS[mode])}
    else:
        first, second = lineage.StockValues
        cut = lineage.CutValue
        atoms = lineage.AtomsValue
        ids = [value.NodeValue.FieldsValue["f08"] for value in (first, second, cut)]
        body_ids = [value.FieldsValue["f140"] for value in (atoms.ConsumedAtom, atoms.UntouchedAtom, atoms.ResultAtom)]
        require(ids == [32, 40, 47] and body_ids == [101, 102, 103] and atoms.SelectedIndex == 0,
                "the typed result is not the observed operation and body lineage")
        depths = [stock.RequireDepth().DepthValue for stock in lineage.StockValues]
        dimension_ids = [value.TypedOwner["dimension_id"] for value in depths]
        require([value.native_value for value in depths] == [.012, .010] and dimension_ids == [27, 34],
                "the two blind drivers differ")
        normals = [[frame.z_axis.x, frame.z_axis.y, frame.z_axis.z] for frame in lineage.ProfileFrames]
        require(normals == [[0, 0, 1], [1, 0, 0], [0, 0, 1]], "signed native support frames differ")
        choices = {
            "default_new_solid_refusal": reject(lambda: ReadExtrude(link, second.NodeValue, IndexFeatures(link)),
                                                 "typed model expected concrete schema one moExtrusion_c"),
            "default_unequal_scope_refusal": reject(
                lambda: CheckCutScope(link.ConfigValue.RootValue, first.NodeValue, cut.NodeValue, 101),
                "cut body scope is outside the witnessed saved profiles"),
        }
        document = open_document(payload, source_format="solidworks.sldprt", strict=True,
                                 include_brep=False, include_tessellation=False)
        typed = document.metadata["solidworks.typed_resolved_semantics"]
        require(typed["status"] == "unsupported" and typed["diagnostic"] == "multiple operation histories are outside typed blind topology",
                "public typed geometry unexpectedly admitted the multistock source")
        result = {"feature_ids": ids, "atom_ids_consumed_untouched_result": body_ids, "selected_stock_index": atoms.SelectedIndex,
                  "stock_dimensions": dimension_ids, "stock_depths_m": [value.native_value for value in depths],
                  "profile_normals": normals, "public_typed_geometry": typed["status"], **choices}
    require(not attempts, "worker tried to read external data")
    return {**result, "external_access_attempts": len(attempts)}


def prove(path):
    source = path.resolve(strict=True)
    require(source.parts[-3:] == SOURCE_SUFFIX and not path.is_symlink(), "pass the exact disclosed packet 03 source")
    payload = source.read_bytes()
    require(sha256(payload).hexdigest() == SOURCE_SHA, "disclosed source hash differs")
    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    members = [TYPED / "ReadExtrude.py", TYPED / "Cuts/CheckSavedCutScope.py",
               *sorted((TYPED / "Cuts/MultiStock").glob("*.py"))]
    phases = {}
    for mode in ("original", *REFUSALS):
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode), input=payload, capture_output=True)
        require(result.returncode == 0, result.stderr.decode())
        phases[mode] = json.loads(result.stdout)
    require(sha256(source.read_bytes()).hexdigest() == SOURCE_SHA, "disclosed source changed")
    return {"schema": "kit.sw2026.multistock-typed-lineage.v1", "baseline_revision": BASE,
            "worktree_head": head, "source_sha256": SOURCE_SHA, "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
            "reader_sha256": {str(item.relative_to(REPO)): sha256(item.read_bytes()).hexdigest() for item in members},
            "independent_processes": len(phases), "phases": phases, "native_processes_started": 0,
            "generated_native_files": 0, "heldout_read_count": 0, "public_writer_qualified": False}


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--source", type=Path)
    modes.add_argument("--worker", choices=("original", *REFUSALS))
    args = parser.parse_args()
    result = worker(args.worker) if args.worker else prove(args.source)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
