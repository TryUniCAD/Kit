from argparse import ArgumentParser
from math import dist
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
FAMILY_DIR = HERE.parent.parent
ROOT = HERE.parents[5]
sys.path[:0] = [str(path) for path in (HERE.parent, FAMILY_DIR, FAMILY_DIR.parent / "edge_fillet_source")]

from ChamferModel import predict
from ChamferNeutralIntent import neutral_intent
from ChamferPacket import TOOLS as SOURCE_TOOLS, write_new
from FilletPacket import job_bytes
from RunSealedChamfer import (
    BOUNDARY_REV, BUILD, CONTROL, DISCLOSED_FILE, DISCLOSED_REV, DISCLOSED_SHA, DRIVER_REV, EPOCH, FAMILY, LOCK_REV,
    ORACLE, PREWRITER_FILE, PREWRITER_SHA, PRIOR_FREEZE, PRIOR_RESULT, SOURCE_PATH, TOOLS, WRITER, compiler_bundle, digest,
    generate, hash_bytes, pin_record, require, verify_original_public_evidence,
)
from RunSignedSealedChamfer import (
    ASSETS, PRIOR_CUSTODY02, PRIOR_FREEZE02, PRIOR_RESULT02, SCHEMA, SIGNED_COMPILER_SHA, SIGNED_DISCLOSED_TRIAL,
    SIGNED_EVAL_ROOT, SIGNED_INPUTS, SIGNED_NATIVE_RESULT, SIGNED_SRC_TREE, SIGNED_TREE, SIGNED_WRITER, TRIAL, verified,
    verify_previous_retry, verify_signed_plan, verify_signed_result,
)
from StageSealedChamfer import blob, git, git_python_closure, identity, zip_python

SIGNED_EPOCH = 1795510277


def exact_bytes(path, expected):
    data = path.read_bytes()
    require(hash_bytes(data) == expected, "public measurement or control seal changed")
    return data


def preparation_inputs(signed_packet, control):
    require(signed_packet.is_absolute() and signed_packet.name == "Packet"
            and signed_packet.parent.name == "GeneratedChamferSigned01"
            and not signed_packet.is_relative_to(ROOT), "use the exact external disclosed signed packet")
    share = signed_packet.parents[1]
    prior01 = share / "GeneratedChamferHeldout01"
    prior02 = share / "GeneratedChamferHeldout02"
    require(digest(prior01 / "Packet/Freeze.json") == PRIOR_FREEZE
            and digest(prior02 / "Packet/Freeze.json") == PRIOR_FREEZE02,
            "the two earlier public freezes must remain immutable")
    assets = {
        "PriorEvaluation.json": exact_bytes(prior01 / "Public/Result.json", PRIOR_RESULT),
        "PriorEvaluation02.json": exact_bytes(prior02 / "Public/Result.json", PRIOR_RESULT02),
        "PriorCustody02.json": exact_bytes(prior02 / "Public/Custody.json", PRIOR_CUSTODY02),
        "Control.SLDPRT": exact_bytes(control, CONTROL),
        "SignedTrial.json": exact_bytes(signed_packet / "Trial.json", SIGNED_DISCLOSED_TRIAL),
        "PrewriterLock.json": blob(LOCK_REV, PREWRITER_FILE),
        "DisclosedReceipt.json": blob(DISCLOSED_REV, DISCLOSED_FILE),
    }
    require(hash_bytes(assets["PrewriterLock.json"]) == PREWRITER_SHA
            and hash_bytes(assets["DisclosedReceipt.json"]) == DISCLOSED_SHA,
            "the original published prewriter or native acceptance evidence changed")
    verify_signed_plan(json.loads(assets["SignedTrial.json"]))
    return assets


def write_assets(folder, assets):
    for name, data in assets.items():
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)


def smoke(assets, identities):
    from StageGeneratedChamfer import composed_requests

    legacy = json.loads(assets["DisclosedReceipt.json"])["generated_inputs"]
    signed = json.loads(assets["SignedTrial.json"])
    actual = []
    with TemporaryDirectory(prefix="KitSignedSealedChamfer") as temp:
        root = Path(temp)
        write_assets(root / "Packet", assets)
        prewriter = verify_original_public_evidence(root / "Packet")
        verify_previous_retry(root / "Packet", prewriter)
        entry = compiler_bundle(root / "Packet", root / "Compiler", identities)
        for index, (request, expected) in enumerate(zip(composed_requests(), legacy, strict=True)):
            proof = generate(entry, {"origin_mm": [0.0, 0.0], "request": request},
                             root / f"Legacy{index}.SLDPRT", root / f"Legacy{index}")
            require(proof["archive_sha256"] == expected, "revised compiler changed an already disclosed positive-side container")
            actual.append(proof["archive_sha256"])
        for index, (case, row) in enumerate(zip(signed["spec"]["cases"], signed["cases"], strict=True)):
            wire = neutral_intent(case, row["branch"], row["locator"], SIGNED_EPOCH + index * 61)
            require(hash_bytes(job_bytes(wire)) == row["writer_proof"]["intent_sha256"],
                    "signed smoke input differs from the independently frozen disclosed neutral input")
            proof = generate(entry, wire, root / f"Signed{index}.SLDPRT", root / f"Signed{index}")
            require(proof["archive_sha256"] == SIGNED_INPUTS[index]
                    and all(dist(source, expected) <= 1e-12 for source, expected in
                            zip(proof["selected_endpoints_m"], predict(case)["source_edge"], strict=True)),
                    "frozen compiler does not reproduce its calibrated signed native candidate")
            actual.append(proof["archive_sha256"])
    return {"compiler_sha256": SIGNED_COMPILER_SHA, "compiler_members": len(identities),
            "disclosed_archive_sha256": actual, "guarded_writer_processes": 8,
            "runtime_accesses": 0, "native_processes": 0, "protected_reads": 0}


def prepare(signed_packet, control):
    assets = preparation_inputs(signed_packet, control)
    require(git("rev-parse", f"{SIGNED_WRITER}^{{tree}}").decode().strip() == SIGNED_TREE
            and git("rev-parse", f"{SIGNED_WRITER}:src").decode().strip() == SIGNED_SRC_TREE,
            "the signed construction must bind its exact frozen Git trees")
    for revision in (BOUNDARY_REV, DRIVER_REV, WRITER, SIGNED_WRITER):
        git("merge-base", "--is-ancestor", LOCK_REV, revision)
    source = git_python_closure(SIGNED_WRITER, writer=SIGNED_WRITER)
    assets["Compiler.zip"] = zip_python(source)
    require(hash_bytes(assets["Compiler.zip"]) == SIGNED_COMPILER_SHA, "the exact revised compiler archive differs")
    identities = {name: identity(value) for name, value in source.items()}
    return assets, identities


def stage(output, control, signed_packet, native, native_pin):
    require(output.is_absolute() and output.name == TRIAL and output.parent == signed_packet.parents[1]
            and not output.exists() and not output.resolve().is_relative_to(ROOT)
            and native_pin == SIGNED_NATIVE_RESULT, "stage only at the unused public root with the measured signed result")
    signed_native = pin_record(native, native_pin)
    verify_signed_result(signed_native)
    head = git("rev-parse", "HEAD").decode().strip()
    git("merge-base", "--is-ancestor", SIGNED_WRITER, head)
    require(not git("status", "--porcelain", "--untracked-files=no"), "freeze the exact committed evaluator source first")
    assets, identities = prepare(signed_packet, control)
    observed = smoke(assets, identities)
    assets.update({f"Tool/{name}": blob(WRITER, f"{folder}/{name}")
                   for folder, names in SOURCE_TOOLS.items() for name in names})
    assets.update({f"Tool/{name}": blob(head, f"{FAMILY}/sealed/{name}") for name in TOOLS | {"RunSignedSealedChamfer.py"}})
    assets.update({
        "Tool/RunNativeChamferProbe.py": blob(WRITER, f"{FAMILY}/RunNativeChamferProbe.py"),
        "SignedNativeResult.json": exact_bytes(native, native_pin),
    })
    require(set(assets) == ASSETS, "signed evaluation public file closure is incomplete")
    freeze = {
        "schema": SCHEMA, "evaluator_revision": head, "construction_revision": SIGNED_WRITER,
        "construction_tree": SIGNED_TREE, "construction_src_tree": SIGNED_SRC_TREE, "prewriter_lock_revision": LOCK_REV,
        "boundary_revision": BOUNDARY_REV, "driver_revision": DRIVER_REV, "oracle_build": BUILD, "oracle_sha256": ORACLE,
        "source_root": SOURCE_PATH, "evaluation_root": str(SIGNED_EVAL_ROOT),
        "prior_freeze_sha256": PRIOR_FREEZE, "prior_result_sha256": PRIOR_RESULT, "prior_freeze02_sha256": PRIOR_FREEZE02,
        "prior_result02_sha256": PRIOR_RESULT02, "prior_custody02_sha256": PRIOR_CUSTODY02,
        "signed_trial_sha256": SIGNED_DISCLOSED_TRIAL, "signed_native_result_sha256": native_pin,
        "complete_fresh_processes": 10, "epochs": [EPOCH, EPOCH + 1],
        "compiler_members": identities, "files": {name: identity(value) for name, value in assets.items()},
    }
    packet = output / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    (output / "Public").mkdir()
    write_assets(packet, assets)
    write_new(packet / "Freeze.json", freeze)
    pin = digest(packet / "Freeze.json")
    verified(packet, pin)
    return observed | {"freeze_sha256": pin, "signed_native_result_sha256": native_pin, "evaluator_revision": head}


if __name__ == "__main__":
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--output", type=Path)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--signed-packet", required=True, type=Path)
    parser.add_argument("--signed-native", type=Path)
    parser.add_argument("--signed-pin")
    args = parser.parse_args()
    if args.preflight:
        require(args.signed_native is None and args.signed_pin is None, "preflight uses only immutable public input bundles")
        result = smoke(*prepare(args.signed_packet, args.control))
    else:
        require(args.signed_native is not None and args.signed_pin is not None, "signed result and root-issued pin are required")
        result = stage(args.output, args.control, args.signed_packet, args.signed_native, args.signed_pin)
    print(json.dumps(result, sort_keys=True))
