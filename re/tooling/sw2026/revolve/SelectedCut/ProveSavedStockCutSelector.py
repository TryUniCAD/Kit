from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "EndModes"), str(ROOT / "src")]

from AuditStockCutSelectorSave import ORACLE, RESULT_PIN, TRIAL_PIN, measured
from ProveSelectedRevCut import dispatch, need


BASELINE = "2bc7a06403c001f7464786872debaed0bda77d40479a7ac3faf277aa0b489fdb"
FAULTS = {
    "producer": "wrapper does not alias",
    "face-cache": "wrapper does not alias",
    "epoch": "different feature creation owner",
    "missing-chooser": "no active owner",
    "mirrored-order": "mirrored surface ownership",
}
SOURCE_PATH = Path(
    "src/convert/adapters/solidworks/Core/TypedResolved/Revolves/SelectedCut"
)


def change_selector(lineage, fault):
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId

    wrapper = lineage.WrapperValue.FieldsValue
    cut = lineage.CutValue.NodeValue.FieldsValue
    if fault == "producer":
        wrapper["f108"] = NativeNodeId(lineage.UntouchedValue.NodeValue)
    elif fault == "face-cache":
        wrapper["f104"] = lineage.AtomsValue.ResultAtom.FieldsValue["f140"]
    elif fault == "epoch":
        choice = cut["f4a8"]["f48"]["items"][0]["o"]
        face = choice.FieldsValue["f08"]["items"][0]["o"].FieldsValue
        rep = face["f10"][0]["f08"].FieldsValue
        rep["f10"]["f10"].FieldsValue["f10"]["f08"] += 1
    elif fault == "missing-chooser":
        cut["has_f4a8"], cut["f4a8"] = 0, None
    elif fault == "mirrored-order":
        choice = cut["f4c0"]["f48"]["items"][0]["o"]
        choice.FieldsValue["f08"]["items"].reverse()
    else:
        raise ValueError("unrecognized direct selector guard")


def fault_worker(request):
    from AuditPrincipalReader import make_guard
    from ProveTwoDirectionRevolves import warm
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadSelRevCut import (
        ReadSelRevCut,
    )

    fault = request["fault"]
    raw = measured(Path(request["path"]), request["sha256"])
    warm()
    state, guard = make_guard(ROOT / "src")
    state["enabled"] = True
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    lineage = ReadSelRevCut(link, top)
    need(lineage.WrapperValue.FieldsValue["ff0"] is None, "direct selector required")
    change_selector(lineage, fault)
    try:
        ReadSelRevCut(link, top)
    except ValueError as error:
        reason = str(error)
        need(FAULTS[fault] in reason, "wrong guard refusal: " + reason)
    else:
        raise ValueError("unexpected acceptance: " + fault)
    state["enabled"] = False
    need(not guard["unexpected_attempts"], "the reader accessed external data")
    return {"reason": reason, "external_runtime_reads": 0}


def fault_run(path, pin, fault):
    request = {"path": str(path), "sha256": pin, "fault": fault}
    child = run((sys.executable, "-I", "-B", __file__, "--worker"),
                input=json.dumps(request).encode(), capture_output=True, timeout=120)
    need(child.returncode == 0 and not child.stderr, child.stderr.decode())
    return json.loads(child.stdout)


def prove(packet):
    need(packet.name == "RevolveCutSelector01", "the disclosed selector packet is required")
    baseline = ROOT / "re/solidworks/measurements/2026/SelectedRevolveCutSelectorSavedOwner01.json"
    before = json.loads(measured(baseline, BASELINE))
    native = json.loads(measured(packet / "Inspection/Result.json", RESULT_PIN))
    need(native["trial_sha256"] == TRIAL_PIN and native["oracle_sha256"] == ORACLE
         and native["control_brackets_healthy"] and native["distinct_processes"] == 6,
         "the original native contrast lacks independent controls")
    cases = {}
    for label in ("producer", "sentinel"):
        old = before["arms"][label]
        native_case = native["arms"][label]
        pin = native_case["edited_sha256"]
        directory = packet / "Inspection" / label
        reopen = json.loads(measured(directory / "FreshReopen.json", native_case["phases"][1]["sha256"]))
        need(old["native_lifecycle_matches"] and old["saved_native_sha256"] == pin
             and old["current_sdk_saved_read"]["decoded_body_count"] == 1
             and reopen["passed"] and reopen["oracle_identity"]["sha256"] == ORACLE,
             "the phase-bound comparison or pre-change result is inconsistent")
        state = dispatch(directory / "Saved.SLDPRT", pin, observed=reopen)
        need([body["atom_id"] for body in state["bodies"]] == [102, 103]
             and state["owners"]["consumed_atom_id"] == 101
             and state["unexpected_runtime_reads"] == 0,
             "strict path must distinguish the consumed and two surviving atoms")
        cases[label] = state
    trial = packet / "Inspection/producer/Saved.SLDPRT"
    refused = {fault: fault_run(trial, cases["producer"]["sha256"], fault) for fault in FAULTS}
    return {
        "schema": "kit.sw2026.direct-selected-revolve-saved-read.v1",
        "source_revision": check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
        "changed_source_sha256": {
            str(SOURCE_PATH / name): sha256((ROOT / SOURCE_PATH / name).read_bytes()).hexdigest()
            for name in ("ReadRevWrapper.py", "CheckRevPick.py")
        },
        "pre_change_receipt_sha256": BASELINE,
        "native_result_sha256": RESULT_PIN,
        "cases": cases,
        "refused": refused,
        "guarded_processes": len(cases) + len(refused),
        "new_native_processes": 0,
        "new_heldout_credit": 0,
        "public_writer": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(fault_worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        raw = (json.dumps(prove(args.packet.resolve(strict=True)), indent=2,
                          sort_keys=True, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as stream:
            stream.write(raw)
        print(sha256(raw).hexdigest())
