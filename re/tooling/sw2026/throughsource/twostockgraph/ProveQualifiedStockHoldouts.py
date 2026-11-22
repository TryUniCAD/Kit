from argparse import ArgumentParser
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from pathlib import Path
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
DATA = ROOT / "re/solidworks/measurements/2026"
NATIVE_PIN = "6b39921b4959e3662f886def026c55240227f8aab37d3246206bcf02ab8cbb7a"
ROUTE_PIN = "b3842104ec22b9397015ba4da73b0297babb14229d4741eb280f591323dec657"


def read_record(path, pin):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != pin:
        raise ValueError("the exact comparison receipt changed")
    return json.loads(raw)


def worker(slot, measured):
    from EvaluateTwoStockHoldout01 import (
        BASE,
        PACKET,
        SOURCE_AUTHOR,
        SOURCE_AUTHOR_PIN,
        WRITTEN_AT,
        checked,
        imports,
        neutral_document,
        part_name,
    )
    from ProveStockRegistration import FORMAT, load_runtime, policy_result, require

    _, stock, _, _ = imports()
    load_runtime(ROOT / "src")
    sys.path.insert(0, str(HERE.parent.parent.parent))
    checked(ROOT / SOURCE_AUTHOR, SOURCE_AUTHOR_PIN)
    from ThroughAllSourcePlan import PLANES
    from ProofModels import authored_document
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.api.ApiContext import GetRegistry
    from ProveQualifiedStocks import NATIVE_CAPS
    from ProveSdkStockWriter import armed_guard, read_generated

    require(
        callable(authored_document), "the independent neutral author is unavailable"
    )
    for module in ("ProvePublicColdStocks", "ProveRebuiltColdStocks"):
        import_module(module)
    receipt = (
        read_record(DATA / "TwoStockWriterHoldoutNative02.json", NATIVE_PIN)
        if measured else None
    )
    attempts = armed_guard()
    raw_request = sys.stdin.buffer.read()
    document = neutral_document(
        slot, json.loads(raw_request), stock, (PLANES["front"], PLANES["right"])
    )
    final = str(BASE / PACKET / (part_name(slot) + ".SLDPRT"))
    options = {"final_destination": final, "require_native_transfers": True}
    if receipt is not None:
        options["solidworks_native_measurement"] = {
            "written_at": WRITTEN_AT, "receipt": receipt,
        }
    framework_out, direct_out = BytesIO(), BytesIO()
    result = write_document(
        document,
        framework_out,
        destination_format=FORMAT,
        allow_carrier=False,
        values=options,
    )
    direct = (
        GetRegistry()
        .GetWriter(FORMAT)
        .write(document, direct_out, WriteOptions(values=options))
    )
    raw = framework_out.getvalue()
    require(
        raw == direct_out.getvalue(),
        "ordinary and direct SDK generated different bytes",
    )
    policy_result(direct, raw, True, None)
    transfers = policy_result(result, raw, True, None, NATIVE_CAPS)
    typed = read_generated(raw, document)
    archive = SldprtArchive.from_bytes(raw)
    require(
        len(archive.streams) == 10 and len(typed["bodies"]) == 2 and not attempts,
        "the registered held-out output lost its ten streams or required external data",
    )
    return {
        "request_sha256": sha256(raw_request).hexdigest(),
        "candidate_sha256": sha256(raw).hexdigest(),
        "bytes": len(raw),
        "streams": len(archive.streams),
        "strict_sdk_bodies": len(typed["bodies"]),
        "routes": 2,
        "native_transfers": sorted(transfers),
        "runtime_input_file_reads": len(attempts),
    }


def prove(measured):
    from EvaluateTwoStockHoldout01 import imports, win_call, wire
    from ProveQualifiedStocks import LEGACY, launch, require

    _, stock, _, _ = imports()
    native = read_record(DATA / "TwoStockWriterHoldoutNative02.json", NATIVE_PIN)
    prior = (
        read_record(DATA / "SdkTwoStockQualifiedRegistration01.json", ROUTE_PIN)
        if not measured else None
    )
    results = {}
    for slot, expected in native["staged"]["slots"].items():
        raw = wire(
            json.loads(
                win_call(stock, native["native"]["freeze_sha256"], slot + "-export")
            )
        )
        result = run(
            (sys.executable, "-I", "-B", str(HERE), "--worker", slot,
             *(("--measured-only",) if measured else ())),
            input=raw,
            capture_output=True,
            timeout=90,
        )
        if measured and result.returncode != 0:
            known = (
                "regenerated selected stock part has no exact native measurement",
                "ordinary and direct SDK generated different bytes",
                "selected stock stream requires its exact measured locator",
                "the registered held-out output lost its ten streams or required external data",
            )
            error = result.stderr.decode(errors="replace")
            reason = next((item for item in known if item in error), "guarded worker failed")
            raise ValueError("held-out slot " + slot + ": " + reason)
        require(result.returncode == 0, result.stderr.decode())
        part = json.loads(result.stdout)
        require(
            part["request_sha256"] == expected["request_sha256"]
            and part["candidate_sha256"] == expected["sha256"]
            and part["bytes"] == expected["bytes"],
            "the public writer did not reproduce the exact native-tested locked output",
        )
        results[slot] = part
    for mode in (() if prior is None else ("disclosed", "independent", "refusals", *LEGACY)):
        expected = (
            prior["legacy_parity"][mode] if mode in LEGACY else prior["results"][mode]
        )
        require(
            launch(mode, ROOT / "src") == expected,
            "registered comparison changed: " + mode,
        )
    return {
        "schema": "kit.sw2026.qualified-stock-writer-integration.v1",
        "base_revision": check_output(
            ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True
        ).strip(),
        "source_patch_sha256": sha256(
            check_output(("git", "diff", "--binary", "HEAD", "--", "src"), cwd=ROOT)
        ).hexdigest(),
        "native_receipt_sha256": NATIVE_PIN,
        "disclosed_route_receipt_sha256": ROUTE_PIN if prior is not None else None,
        "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
        "disclosed_and_legacy_guarded_processes": 7 if prior is not None else 0,
        "unchanged_legacy_routes": sorted(LEGACY) if prior is not None else [],
        "new_native_launches": 0,
        "heldout_exact_public_output": results,
    }


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parent))
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("a", "b"))
    parser.add_argument("--measured-only", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            worker(args.worker, args.measured_only) if args.worker else prove(args.measured_only),
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
    )
