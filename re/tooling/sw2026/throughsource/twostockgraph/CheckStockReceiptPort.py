from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path.insert(0, str(HERE.parent))

from ProveStockRegistration import FORMAT, load_runtime, require

RECEIPT = ROOT / "re/solidworks/measurements/2026/TwoStockWriterHoldoutNative02.json"
RECEIPT_SHA = "6b39921b4959e3662f886def026c55240227f8aab37d3246206bcf02ab8cbb7a"
EPOCH = 1765500071
OPTION = "solidworks_native_measurement"


def paths_for(slot):
    name = "TwoStockHoldout" + slot.upper()
    locator = rf"C:\KitSdkCandidates\TwoStockWriterEvaluation02\{name}.SLDPRT"
    return name, locator


def rejected_routes(folder, slot, receipt, other_receipt):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.Stocks.ReadStockMeas import ReadStockMeas
    from ProveSdkStockWriter import authored, read_generated
    from VerifySdkCircleEndRegistration import OutputGuard, refuses

    name, locator = paths_for(slot)
    _, other_locator = paths_for("b" if slot == "a" else "a")
    model = replace(authored("disclosed"), metadata={"name": name})
    target = folder / (name + ".SLDPRT")
    sentinel = b"previous stage content"
    target.write_bytes(sentinel)
    clean = {"final_destination": locator, "require_native_transfers": True}
    evidence = {"written_at": EPOCH, "receipt": receipt}
    settings = {**clean, OPTION: evidence}
    tampered = deepcopy(receipt)
    tampered["native"]["controls_passed"] = False
    paths = (
        ("missing_receipt", model, clean, "offline native measurement receipt"),
        ("wrong_receipt", model, {**settings, OPTION: {**evidence, "receipt": other_receipt}},
         "exact controlled native receipt"),
        ("failed_control", model, {**settings, OPTION: {**evidence, "receipt": tampered}},
         "exact controlled native receipt"),
        ("wrong_epoch", model, {**settings, OPTION: {**evidence, "written_at": EPOCH + 1}},
         "different native run"),
        ("wrong_slot_name", replace(model, metadata={"name": "OtherStock"}), settings,
         "exact native measurement for its authored basename"),
        ("wrong_slot_locator", model, {**settings, "final_destination": other_locator},
         "exact measured locator"),
        ("changed_geometry", model, settings, "regenerated selected stock part has no exact native measurement"),
    )
    adapter = SldprtAdapter()
    audit = OutputGuard(folder, target.name)
    sys.addaudithook(audit.audit)
    with audit.active("memory"):
        selection, options = ReadStockMeas(WriteOptions(values=settings), name)
        stage = receipt["staged"]["slots"][slot]
        require((selection.LocatorValue, selection.SizeValue, selection.CandidateSha)
                == (locator, stage["bytes"], stage["sha256"])
                and OPTION not in options.values,
                "transport did not bind the exact held-out slot and neutral generation options")
        sink = BytesIO()
        generated = PrepareNative(model, sink, EPOCH, options)
        derived = read_generated(generated.BytesValue, model)
        require(len(generated.StreamsValue) == 10 and len(derived["bodies"]) == 2
                and not sink.getvalue(), "guarded independent solid construction changed")
        independent_hash = sha256(generated.BytesValue).hexdigest()
        require(independent_hash != selection.CandidateSha,
                "the independent disclosed contrast must differ from the measured slot")
        outcomes = {}
        for label, incoming, values, reason in paths:
            stream = BytesIO()
            calls = (
                lambda: write_document(incoming, stream, destination_format=FORMAT, values=values),
                lambda: adapter.write(incoming, stream, WriteOptions(values=values)),
            )
            outcomes[label] = tuple(refuses(call, (ValueError,)) for call in calls)
            require(all(reason in text for text in outcomes[label])
                    and stream.getvalue() == b"" and stream.tell() == 0,
                    "a refusal took the wrong route: " + label)
    with audit.active("path"):
        reasons = (
            refuses(lambda: write_document(model, target, overwrite=True, values=settings), (ValueError,)),
            refuses(lambda: adapter.write(model, target, WriteOptions(overwrite=True, values=settings)), (ValueError,)),
        )
        require(all("actual measured final path" in text for text in reasons),
                "a caller option acquired physical destination authority")
    require(not audit.denied and target.read_bytes() == sentinel and tuple(folder.iterdir()) == (target,),
            "the refused writes left staging state or changed the caller output")
    return {
        "slot": slot,
        "exact_measured_sha256": selection.CandidateSha,
        "independent_generated_sha256": independent_hash,
        "independent_logical_streams": len(generated.StreamsValue),
        "independent_sdk_bodies": len(derived["bodies"]),
        "public_refusals": 2 * len(outcomes) + len(reasons),
        "runtime_input_file_reads": len(audit.denied),
    }


def main():
    load_runtime(ROOT / "src")
    for module in ("ProofModels", "ProvePublicColdStocks", "ProveRebuiltColdStocks"):
        import_module(module)
    raw = RECEIPT.read_bytes()
    require(sha256(raw).hexdigest() == RECEIPT_SHA, "the approved corrected receipt changed")
    receipt = json.loads(raw)
    other_receipt = json.loads(RECEIPT.with_name("TwoStockColdNative01.json").read_bytes())
    with TemporaryDirectory(prefix="KitExactStockReceipt") as scratch:
        root = Path(scratch).resolve()
        cases = []
        for slot in ("a", "b"):
            folder = root / slot
            folder.mkdir()
            cases.append(rejected_routes(folder, slot, receipt, other_receipt))
    print(json.dumps({
        "schema": "kit.sw2026.selected-stock-receipt-port.v1",
        "receipt_sha256": RECEIPT_SHA, "cases": cases,
        "new_native_processes": 0, "protected_inputs_read": 0, "publication_successes": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
