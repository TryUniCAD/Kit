from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from subprocess import run
from types import SimpleNamespace
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from BuildStockCutSelector import case_document, guard_runtime, inspect, require, warm
from RevolveFamilyModel import validate_specs
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.MakeSelectedRevolvePart import (
    MakeSelRevPart,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.ProjectSelectedRevolve import (
    ProjectSelRev,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.geometry.Models.Selection import SelectPathElem


PACKETS = {
    "ScopedRevolveFrontier02": "fa54b00919aec9116c36b0d16a2a447d59621a2e20118f67bb0a9c1eaea380e0",
    "ScopedRevolveReverse03": "36380d1259581b8594f977ca3970239cd7c2bfdb3d06811dc97afddee4bbe59d",
}


def digest(data):
    return sha256(data).hexdigest()


def checked(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, f"disclosed packet hash differs: {path.name}")
    return data


def worker(request):
    warm()
    blocked = guard_runtime()
    case, locator, epoch = request["case"], request["locator"], request["epoch"]
    document = case_document(case, locator, epoch)
    plan = ProjectSelRev(document)
    inputs = replace(MakePartRecipe(plan.OperationsValue[0], epoch), OutputValue=SelfFileInput(locator, epoch))
    part = MakeSelRevPart(document, inputs)
    other = document.feature_timeline[1 - plan.SelectedIndex].id
    cut = document.feature_timeline[2]
    bad_selection = tuple(replace(pick, path=(SelectPathElem("feature", other, "body"),))
                          if pick.id == cut.selection_ids[1] else pick for pick in document.selections)
    try:
        MakeSelRevPart(replace(document, selections=bad_selection), inputs)
    except ValueError as error:
        require(str(error) == "selected revolve body reference differs from its dependency", str(error))
    else:
        raise ValueError("composer accepted a stock path disconnected from the cut dependency")
    proof = inspect(part.BytesValue, part.StreamsValue, part.ResolvedValue.ContextValue,
                    SimpleNamespace(operations=plan.OperationsValue, selected_index=plan.SelectedIndex), "sentinel")
    require(not blocked and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                                   for name in sys.modules), "composer used host files or a CAD runtime")
    return {"name": case["name"], "reverse": case["reverse"], "plane": case["plane"], "scope": case["scope"],
            "sha256": digest(part.BytesValue), "bytes": len(part.BytesValue), "runtime_reads": 0,
            "wrong_body_path_refused": True, **proof}


def audit(root):
    records = []
    for name, pin in PACKETS.items():
        folder = root / name
        manifest = json.loads(checked(folder / "Packet.json", pin))
        for case in validate_specs(json.loads(checked(folder / "ModelSpecs.json", manifest["files"]["ModelSpecs.json"]))):
            relative = f'Candidates/{case["name"]}.SLDPRT'
            expected = manifest["files"][relative]
            raw = checked(folder / relative, expected)
            locator = str(PureWindowsPath(manifest["guest_workspace"]) / Path(relative).name)
            request = {"case": case, "locator": locator, "epoch": manifest["epoch"]}
            process = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(request),
                          text=True, capture_output=True, timeout=90)
            require(process.returncode == 0 and not process.stderr, process.stderr)
            record = json.loads(process.stdout)
            require(record["sha256"] == expected and record["bytes"] == len(raw),
                    f'composer bytes differ for {case["name"]}: {json.dumps(record, sort_keys=True)}')
            records.append({"packet_sha256": pin, **record})
    return {"schema": "kit.sw2026.selected-revolve-composer-disclosure.v1", "fresh_processes": len(records),
            "identical_streams": sum(len(row["streams"]) for row in records), "cases": records,
            "heldout_writer_acceptance": False, "public_writer": False, "passed": True}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False))
    else:
        require(args.workspace.is_absolute() and args.output.is_absolute(), "use absolute measurement paths")
        report = json.dumps(audit(args.workspace), sort_keys=True, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8") as output:
            output.write(report)
        print(json.dumps({"receipt_sha256": digest(report.encode()), "passed": True}))
