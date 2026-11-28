from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
RECORDS = ROOT / "re/solidworks/measurements/2026"
COLD_PIN = "3adeb0742ae622ac383bf6b7cd5c577cf9bb050731bbcbdcbdffd08b99304228"
SAVED_PIN = "59b119f300de22a92c5f3eb0decaf89db77dfe8a44ec83bc3385fdfe15c623e3"


def prove(workspace):
    sys.path.insert(0, str(HERE.parent))
    from ProvePublicColdStocks import FAULTS, ORDINARY, SAVED_CONTROL, run_worker, verify
    from ProveRebuiltColdStocks import GENERATED, NATIVE_SAVED, pinned, require
    from ProveSavedStockReadback01 import prove as prove_saved

    prior_cold = json.loads(pinned(RECORDS / "TwoStockColdSdkRead01.json", COLD_PIN))
    prior_saved = json.loads(pinned(RECORDS / "TwoStockSavedSdkRead01.json", SAVED_PIN))
    packet = workspace / "GeneratedTwoStockGraph01"
    initial = pinned(packet / "GeneratedTwoStockGraph01.SLDPRT", GENERATED)
    controls = {
        "saved": pinned(
            workspace / "ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT",
            SAVED_CONTROL,
        ),
        "ordinary": pinned(
            ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT", ORDINARY
        ),
    }
    payloads = {mode: b"" for mode in ("edited", "second", "bore", *FAULTS)}
    payloads.update(initial=initial, raw=initial, **{"no-brep": initial}, **controls)
    sdk = ROOT / "src"
    cold = {mode: run_worker(mode, raw, sdk) for mode, raw in payloads.items()}
    for mode, value in cold.items():
        require(value == prior_cold["phases"][mode], f"cold SDK phase {mode} changed")
    verify(cold)
    saved = prove_saved(workspace)
    for mode in ("strict_reads", "no_brep", "refusals"):
        require(saved[mode] == prior_saved[mode], f"saved SDK phase {mode} changed")
    derivative = pinned(packet / "NativeAfterEdit.SLDPRT", NATIVE_SAVED)
    strict_derivative = run_worker("saved-derivative", derivative, sdk)
    require(
        strict_derivative["body_binding"] == saved["strict_reads"]["moving"]["lineage"]
        and strict_derivative["tree_status"] == cold["saved"]["tree_status"]
        and len(strict_derivative["brep_ids"]) == 2
        and strict_derivative != prior_cold["phases"]["saved-derivative"],
        "the integrated saved derivative lost its typed provenance",
    )
    files = {HERE.relative_to(ROOT).as_posix(), *prior_cold["source_sha256"],
             *saved["implementation_sha256"]}
    return {
        "schema": "kit.sw2026.combined-two-stock-sdk-read.v1",
        "before_integration": saved["base_revision"],
        "implementation_sha256": {
            name: sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(files)
        },
        "cold_receipt_sha256": COLD_PIN,
        "saved_receipt_sha256": SAVED_PIN,
        "unchanged_cold_phases": sorted(cold),
        "unchanged_saved_groups": ["strict_reads", "no_brep", "refusals"],
        "saved_derivative": strict_derivative,
        "guarded_processes": len(cold) + saved["guarded_processes"] + 1,
        "runtime_access_attempts": 0,
        "native_launches": 0,
        "held_out_cases": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    result = prove(parser.parse_args().workspace)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
