from argparse import ArgumentParser
from base64 import b64decode
from hashlib import sha256
import json
from math import dist
from pathlib import Path
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
FAMILY = HERE.parent.parent
sys.path[:0] = [str(path) for path in (HERE.parent, FAMILY, FAMILY / "sealed", FAMILY.parent / "edge_fillet_source")]

from ChamferComparison import compare_state, driver_roles
from ChamferModel import predict, values_si
from ChamferNeutralIntent import neutral_intent
from ChamferPacket import TOOLS, write_new
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest, job_bytes
from RunNativeChamferProbe import SCHEMA, SIGNED_PACKET, SIGNED_SOURCE_LOCK, verified

AUDIT = "f1f841e2c6851522ce7c10bf5c469c92ded68db0fd50e1f3caed98a334aa89d7"
BASELINE = "re/solidworks/measurements/2026/EdgeChamferColdOwners01.json"
BASELINE_SHA = "cba1af0781a45a4374b46a202438440ed67d3726fd93d7143eb0c018a2ea6526"
SOURCE_SPEC = HERE.with_name("ChamferSignedSideInputs.json")


def warm_sources(disclosed):
    from AuditChamferSignedSides import CD_LOCK, CD_PHASES, cd_source, checked_json

    require(CD_LOCK == SIGNED_SOURCE_LOCK, "different reference and generated source lock")
    lock, cases = cd_source(disclosed)
    for kind, phase in lock["controls"].items():
        require(phase["passed"] and checked_json(disclosed / f"control-{kind}" / "Record.json",
                                                phase["receipt_sha256"])["passed"],
                "source comparisons require both healthy controls")
    rows = []
    for slot, (case, choice) in enumerate(zip(cases, lock["sources"], strict=True)):
        folder = disclosed / f"Slot{slot + 1:02d}"
        phases = choice["phases"]
        require(choice["passed"] and choice["tree_rows"] == 26 and tuple(row["phase"] for row in phases) == CD_PHASES
                and all(row["passed"] and row["checks"] == row["checks_passed"] > 0 for row in phases),
                "native source states have an incomplete or wrong lifecycle")
        authored, changed, reopened = [checked_json(folder / row["phase"] / "Record.json", row["receipt_sha256"])
                                     for row in phases]
        require(all(row["passed"] and row["writer_output_count"] == 0 for row in (authored, changed, reopened))
                and authored["native_sha256"] == choice["original_sha256"]
                and changed["native_sha256"] == reopened["native_sha256"] == choice["edited_sha256"],
                "native source phase records disagree with the locked artifacts")
        initial, edited = changed["reopened"], reopened["reopened"]
        authored_state = authored["authored"]
        require(driver_roles(authored_state, "Part1", case, False) == driver_roles(initial, case["name"], case, False)
                and authored_state["tree"] == initial["tree"], "source authoring lost its actual transient qualifier or tree")
        edits = compare_state(changed["edited"], edited, case, edited=True, actual_saved=False)
        require(initial["branch"] == edited["branch"] == choice["orientation"], "measured native source select side changed")
        rows.append({"name": case["name"], "source_artifacts": [choice["original_sha256"], choice["edited_sha256"]],
                     "source_phases": [row["receipt_sha256"] for row in phases], "initial": initial, "edited": edited,
                     "authoring_document_qualifier": "Part1.Part", "prior_native_numeric_comparisons": edits})
    return {"source_lock_sha256": CD_LOCK, "cases": rows}, cases


def guarded_worker(wire):
    process = run((sys.executable, "-I", "-B", str(HERE.with_name("CompileSignedChamferTrial.py"))),
                  input=wire, capture_output=True, timeout=90, check=False)
    require(process.returncode == 0 and not process.stderr, process.stderr.decode())
    return process.stdout


def previous_parity():
    from ProveChamferEdgeOwners import canonical, composed_requests, invoke

    baseline = (ROOT / BASELINE).read_bytes()
    require(digest_bytes(baseline) == BASELINE_SHA, "previous constructed archive receipts differ")
    frozen = json.loads(baseline)["generated_containers_in_memory"]
    results = []
    for request, expected in zip(composed_requests(), frozen, strict=True):
        proof = json.loads(invoke("--model", data=canonical(request)))
        require(all(proof[key] == expected[key] for key in (
            "case", "intent_sha256", "container_sha256", "streams", "face_roles", "dimension_ids",
        )) and proof["guarded_runtime_reads"] == 0 and "longitudinal_distance_side" in proof["rejection_reasons"],
                "the legacy positive-side graph no longer reproduces its exact candidate or refuses categorically invalid sides")
        results.append({"case": proof["case"], "archive_sha256": proof["container_sha256"],
                        "identical_streams": len(proof["streams"]), "guarded_runtime_reads": 0,
                        "rejection_reasons": proof["rejection_reasons"]})
    return results


def stage(output, control, disclosed, audit_path):
    require(output.is_absolute() and output.name == "Packet" and output.parent.name == "GeneratedChamferSigned01"
            and not output.exists() and not output.resolve().is_relative_to(ROOT),
            "stage only at the unused managed external GeneratedChamferSigned01/Packet")

    def git(*args):
        return check_output(("git", "-C", str(ROOT), *args))

    revision = git("rev-parse", "HEAD").decode().strip()
    require(not git("status", "--porcelain", "--untracked-files=no"), "freeze the exact committed construction first")
    require(digest(control) == CONTROL and digest(audit_path) == AUDIT, "exact control or signed owner calibration differs")
    source_audit = json.loads(audit_path.read_bytes())
    require(source_audit["raw_source_lock_sha256"] == SIGNED_SOURCE_LOCK
            and source_audit["guarded_source_processes"] == 4, "wrong frozen native side audit")
    reference, cases = warm_sources(disclosed)
    legacy = previous_parity()
    assets = {f"Tool/{name}": git("show", f"{revision}:{path}/{name}") for path, names in TOOLS.items() for name in names}
    for name, source in (
        ("RunNativeChamferProbe.py", FAMILY / "RunNativeChamferProbe.py"),
        ("ChamferComparison.py", FAMILY / "sealed/ChamferComparison.py"),
    ):
        assets[f"Tool/{name}"] = git("show", f"{revision}:{source.relative_to(ROOT).as_posix()}")
    assets.update({"Control.SLDPRT": control.read_bytes(), "Reference.json": job_bytes(reference)})
    staged = []
    for index, (case, expected) in enumerate(zip(cases, reference["cases"], strict=True)):
        branch = expected["initial"]["branch"]
        relative = f"Candidates/{case['name']}.SLDPRT"
        locator = str(SIGNED_PACKET / relative)
        wire = job_bytes(neutral_intent(case, branch, locator, 1795510277 + index * 61))
        first, second = (guarded_worker(wire) for _ in range(2))
        require(first == second, "isolated neutral workers generated different complete byte payloads")
        proof = json.loads(first)
        data = b64decode(proof.pop("model_base64"), validate=True)
        calibrated = source_audit["disclosed"][2 * index:2 * index + 2]
        rows = calibrated[0]["native_support_order"]
        orders = [[row["normal_axis"], row["face_ordinal"]] for row in rows]
        roles = [["moEndFaceSurfIdRep_c", ordinal, 0] if axis == "z" else ["moFromSktEntSurfIdRep_c", ordinal, None]
                 for axis, ordinal in orders]
        require(all(row["case"] == case["name"] and row["exact_linked_replay"] and not row["guarded_external_accesses"]
                    and [[entry["normal_axis"], entry["face_ordinal"]] for entry in row["native_support_order"]] == orders
                    for row in calibrated) and proof["face_roles"] == roles
                and proof["intent_sha256"] == digest_bytes(wire) and proof["archive_sha256"] == digest_bytes(data)
                and proof["archive_bytes"] == len(data) and proof["runtime_accesses"] == 0
                and proof["linked_streams_exact"] == proof["driver_count"] == 2
                and proof["streams"] == len(proof["stream_sha256"]) == 10,
                "guarded emission does not preserve the independently calibrated support ownership or exact linked archive")
        shape = predict(case, values_si(case, False), branch)
        require(all(dist(one, two) <= 1e-12 for one, two in zip(proof["selected_endpoints_m"], shape["source_edge"], strict=True)),
                "independent physical edge does not match compiled owner")
        assets[relative] = data
        staged.append({"path": relative, "locator": locator, "archive_sha256": digest_bytes(data),
                       "branch": branch, "writer_proof": proof,
                       "reciprocal": calibrated[0]["requires_reciprocal_modeled_side"]})
    require([row["reciprocal"] for row in staged] == [True, False] and len({row["archive_sha256"] for row in staged}) == 2,
            "candidate pair must discriminate reciprocal and positive native supports")
    proof_paths = (
        FAMILY / "ChamferEdgeOwners.py", FAMILY / "LinkChamferGraph.py",
        FAMILY / "sealed/ChamferNeutralIntent.py", FAMILY / "sealed/CompileSealedChamfer.py",
        HERE.with_name("CompileSignedChamferTrial.py"), HERE, SOURCE_SPEC,
    )
    manifest = {
        "schema": SCHEMA, "oracle_build": BUILD, "oracle_sha256": ORACLE, "construction_revision": revision,
        "construction_src_tree": git("rev-parse", f"{revision}:src").decode().strip(),
        "disclosed_source_lock_sha256": SIGNED_SOURCE_LOCK, "source_audit_sha256": AUDIT, "heldout_credit": 0,
        "guest_packet": str(SIGNED_PACKET), "guest_output": str(SIGNED_PACKET.parent / "Run01"),
        "spec": json.loads(SOURCE_SPEC.read_bytes()), "cases": staged, "guarded_generation_processes": 4,
        "guarded_runtime_reads": 0, "heldout_inputs_read": 0, "legacy_parity": legacy,
        "construction_inputs": {path.relative_to(ROOT).as_posix(): digest(path) for path in proof_paths},
        "files": {name: {"bytes": len(data), "sha256": digest_bytes(data)} for name, data in assets.items()},
    }
    output.mkdir(parents=True)
    for name, data in assets.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    manifest_file = output / "Trial.json"
    write_new(manifest_file, manifest)
    pin = digest(manifest_file)
    verified(manifest_file, pin)
    return {"manifest_sha256": pin, "candidates": staged, "construction_revision": revision,
            "legacy_parity": legacy, "files": len(assets)}


def digest_bytes(value):
    return sha256(value).hexdigest()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--disclosed", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.output, args.control, args.disclosed, args.source_audit), sort_keys=True))
