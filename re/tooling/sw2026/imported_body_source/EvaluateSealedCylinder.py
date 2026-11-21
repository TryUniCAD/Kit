from argparse import ArgumentParser
from base64 import b64decode
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
from math import isclose, isfinite
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
from time import time


def parse_arguments():
    parser = ArgumentParser(
        description="Verify, build or evaluate the frozen guest-private periodic import packet"
    )
    parser.add_argument("mode", choices=("verify", "build", "measure"))
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--build-lock-sha256")
    return parser.parse_args()


def verify_bootstrap(args):
    if args.mode != "verify" and os.name != "nt":
        raise ValueError("private evaluation uses the Windows guest")
    if args.job.is_symlink() or args.job.name != "Job.json":
        raise ValueError("choose the exact regular packet job")
    path = args.job.resolve(strict=True)
    tools = path.parent / "Tools"
    if tools.is_symlink() or Path(__file__).resolve().parent != tools:
        raise ValueError("run the staged evaluator")
    data = path.read_bytes()
    if sha256(data).hexdigest() != args.job_sha256:
        raise ValueError("frozen evaluation job changed")
    inventory = json.loads(data)["files_sha256"]
    for name in ("EvaluateSealedCylinder.py", "SealedCylinderPacket.py"):
        tool = tools / name
        if (
            tool.is_symlink()
            or sha256(tool.read_bytes()).hexdigest() != inventory["Tools/" + name]
        ):
            raise ValueError("frozen evaluator bootstrap changed")


if __name__ == "__main__":
    arguments = parse_arguments()
    try:
        verify_bootstrap(arguments)
    except Exception as error:
        print(
            json.dumps(
                {
                    "passed": False,
                    "stage": arguments.mode,
                    "failure_type": type(error).__name__,
                }
            )
        )
        raise SystemExit(2)


from SealedCylinderPacket import (
    CONSTRUCTION_SHA256,
    CONTROL,
    FEATURE,
    GAUGE,
    LOCK_SCHEMA,
    LOCK_SHA256,
    LOCK_TRANSPORT_SHA256,
    OMITTED,
    ORACLE,
    RESULT_SCHEMA,
    SLOTS,
    SOURCE_ROOT,
    VERSION,
    atomic_receipt,
    checked,
    digest,
    encode,
    is_digest,
    parse,
    require,
    verify_packet,
)

PHASES = (
    "ControlBefore",
    *(slot + lane for slot in SLOTS for lane in ("Original", "Candidate", "Reopen")),
    "ControlAfter",
)
SOURCE_SPEC_SCHEMA = "kit.sw2026.sealed-cylinder-author-specification.v1"
SOURCE_PROFILE = "single_closed_periodic_cylinder"
MAX_CANDIDATE = 1024**2


def source_specification(lock):
    source = Path(SOURCE_ROOT)
    require(
        source.is_dir() and not source.is_symlink(),
        "locked original source directory is missing",
    )
    document = parse(
        checked(source / "SourceSpecifications.json", lock["specifications_sha256"])
    )
    require(
        set(document) == {"schema", "profile", "source_author", "nonce", "cases"}
        and document["schema"] == SOURCE_SPEC_SCHEMA
        and document["profile"] == SOURCE_PROFILE
        and document["source_author"]
        == "SOLIDWORKS IModeler::CreateBodyFromCyl and IPartDoc::CreateFeatureFromBody3"
        and is_digest(document["nonce"])
        and tuple(document["cases"]) == SLOTS,
        "locked author specification differs",
    )
    for spec in document["cases"].values():
        require(
            type(spec) is dict
            and set(spec) == {"axis", "face_center_m", "radius_m", "height_m"},
            "private specification carries unexpected domains",
        )
    return document["cases"]


def destination(root, slot):
    return root / "Candidates" / (slot + ".SLDPRT")


def run_producer(packet, private_root, request):
    command = [
        sys.executable,
        "-I",
        "-S",
        "-B",
        str(packet / "Tools" / "ProduceSealedCylinder.py"),
    ]
    replies = []
    for _ in range(2):
        result = subprocess.run(
            command,
            input=encode(request),
            capture_output=True,
            timeout=120,
            cwd=private_root,
        )
        require(
            result.returncode == 0
            and not result.stderr
            and 0 < len(result.stdout) <= 2 * MAX_CANDIDATE,
            "guarded producer failed or emitted unqualified output",
        )
        replies.append(result.stdout)
    require(replies[0] == replies[1], "independent guarded producers disagreed")
    reply = parse(replies[0])
    require(
        set(reply)
        == {
            "slot",
            "sha256",
            "bytes",
            "native_path",
            "feature",
            "feature_id",
            "payload_base64",
            "runtime_input_file_reads",
            "native_calls",
            "stream_count",
        }
        and reply["slot"] == request["slot"]
        and reply["runtime_input_file_reads"] == reply["native_calls"] == 0
        and reply["stream_count"] == 12
        and reply["feature"] == FEATURE
        and reply["feature_id"] == 18
        and is_digest(reply["sha256"]),
        "deterministic guarded producer evidence is incomplete",
    )
    data = b64decode(reply.pop("payload_base64"), validate=True)
    require(
        len(data) == reply["bytes"]
        and 0 < len(data) <= MAX_CANDIDATE
        and digest(data) == reply["sha256"],
        "generated file digest differs",
    )
    return reply, data


def build(path, checksum, job, lock):
    packet, root = path.parent, Path(job["guest_root"])
    require(
        not (packet / "Result.json").exists() and not root.is_symlink(),
        "use a new evaluation job",
    )
    root.mkdir()
    (root / "Candidates").mkdir()
    cases = source_specification(lock)
    rows = {}
    for slot, case in cases.items():
        request = {
            "slot": slot,
            "guest_root": job["guest_root"],
            "epoch": job["writer_committed_at"],
            "specification": case,
        }
        metadata, payload = run_producer(packet, root, request)
        target = destination(root, slot)
        require(
            PureWindowsPath(metadata["native_path"]) == PureWindowsPath(target),
            "guarded producer used an unintended logical locator",
        )
        with target.open("xb") as output:
            output.write(payload)
        checked(target, metadata["sha256"])
        rows[slot] = metadata
    require(
        len({row["sha256"] for row in rows.values()}) == 2,
        "distinct sealed inputs produced equal files",
    )
    require(
        verify_packet(path, checksum) == (job, lock),
        "packet changed during guarded production",
    )
    require(
        source_specification(lock) == cases,
        "private recipes changed during guarded production",
    )
    value = {
        "schema": LOCK_SCHEMA,
        "job_sha256": checksum,
        "writer_revision": job["writer_revision"],
        "specifications_sha256": lock["specifications_sha256"],
        "locked_at_unix_s": time(),
        "private_build_processes": 4,
        "runtime_input_file_reads": 0,
        "native_calls": 0,
        "original_files_opened_during_build": 0,
        "cases": rows,
    }
    file = root / "BuildLock.json"
    atomic_receipt(file, value)
    print(
        json.dumps(
            {
                "stage": "generated_hashes_frozen",
                "build_lock_sha256": digest(file.read_bytes()),
                "generated_files": len(rows),
                "guarded_build_processes": 4,
            }
        )
    )
    return 0


def verify_build_lock(root, identity, checksum, job, lock):
    value = parse(checked(root / "BuildLock.json", identity))
    require(
        set(value)
        == {
            "schema",
            "job_sha256",
            "writer_revision",
            "specifications_sha256",
            "locked_at_unix_s",
            "private_build_processes",
            "runtime_input_file_reads",
            "native_calls",
            "original_files_opened_during_build",
            "cases",
        }
        and value["schema"] == LOCK_SCHEMA
        and value["job_sha256"] == checksum
        and value["writer_revision"] == job["writer_revision"]
        and value["specifications_sha256"] == lock["specifications_sha256"]
        and value["locked_at_unix_s"] > job["writer_committed_at"]
        and value["private_build_processes"] == 4
        and value["runtime_input_file_reads"]
        == value["native_calls"]
        == value["original_files_opened_during_build"]
        == 0
        and tuple(value["cases"]) == SLOTS,
        "private build lock differs",
    )
    for slot, row in value["cases"].items():
        target = destination(root, slot)
        require(
            set(row)
            == {
                "slot",
                "sha256",
                "bytes",
                "native_path",
                "feature",
                "feature_id",
                "runtime_input_file_reads",
                "native_calls",
                "stream_count",
            }
            and row["slot"] == slot
            and row["feature"] == FEATURE
            and row["feature_id"] == 18
            and row["stream_count"] == 12
            and row["runtime_input_file_reads"] == row["native_calls"] == 0
            and PureWindowsPath(row["native_path"]) == PureWindowsPath(target)
            and len(checked(target, row["sha256"])) == row["bytes"],
            "part differs from the pre-original build lock",
        )
    return value


def original_binding(slot, lock):
    native = Path(SOURCE_ROOT) / slot
    binding = lock["sources"][slot]
    author = parse(checked(native / "Author.json", binding["author_record_sha256"]))
    reopened = parse(checked(native / "Reopen.json", binding["reopen_record_sha256"]))
    author_result, reopened_result = author["result"], reopened["result"]
    passive = reopened_result["cold"]
    feature = passive["feature"]
    original = native / "Source.SLDPRT"
    require(
        author["passed"] is reopened["passed"] is True
        and author_result["source"] == reopened_result["source"]
        and reopened_result["source"]["sha256"] == binding["source_sha256"]
        and len(checked(original, binding["source_sha256"]))
        == reopened_result["source"]["bytes"]
        and passive["feature"]
        == author_result["post_save"]["feature"]
        == reopened_result["rebuilt"]["feature"]
        and feature["type"] == "BaseBody"
        and bool(feature["name"])
        and feature["native_id"] > 0
        and passive["body_count"] == 1
        and passive["feature_faces"] == 3
        and passive["oldest_owner_face_count"] == 3
        and re.fullmatch(r"[0-9a-f]+", author_result["feature_reference"]),
        "private author custody or BaseBody identity differs",
    )
    return original, feature, author_result["feature_reference"], passive


def tree_signature(observation):
    return tuple(tuple(row) for row in observation["tree_signature"])


def check_original(result, feature, reference, lock_observation):
    require(
        result["passed"]
        and result["open"] == {"returned_document": True, "error": 0, "warning": 0}
        and result["read_only"] is True,
        "pristine original did not reopen read-only",
    )
    expected_tree = tuple(
        (row["name"], row["type"], row["parent"], row["suppressed"])
        for row in lock_observation["tree"]
    )
    for snapshot in (result["cold"], result["rebuilt"]):
        require(
            snapshot["feature"] == feature["name"]
            and snapshot["feature_id"] == feature["native_id"]
            and snapshot["persistent_reference"] == reference
            and snapshot["feature_faces"] == 3
            and tree_signature(snapshot) == expected_tree,
            "live original changed its locked persistent BaseBody or tree",
        )


def compare_scalar(actual, expected, tolerance, *, six_figures=False):
    require(
        isfinite(actual)
        and isfinite(expected)
        and isclose(
            actual, expected, rel_tol=2e-7 if six_figures else 0.0, abs_tol=tolerance
        ),
        "actual native shapes differ",
    )
    if six_figures and max(abs(actual), abs(expected)) > tolerance:
        require(
            format(actual, ".6g") == format(expected, ".6g"),
            "actual native measurements differ at six significant figures",
        )


def compare_components(actual, expected, tolerance, *, six_figures=False):
    for left, right in zip(actual, expected, strict=True):
        compare_scalar(left, right, tolerance, six_figures=six_figures)


def compare_shape(source, candidate, tolerances):
    require(
        tuple(source[key] for key in ("solids", "faces", "edges", "vertices"))
        == tuple(candidate[key] for key in ("solids", "faces", "edges", "vertices"))
        == (1, 3, 2, 0),
        "observed native cylinder topology differs",
    )
    for key in ("volume_m3", "area_m2"):
        compare_scalar(candidate[key], source[key], tolerances[key], six_figures=True)
    position = tolerances["position_m"]
    direction = tolerances["direction"]
    compare_components(candidate["com_m"], source["com_m"], position, six_figures=True)
    for actual, expected in zip(
        candidate["extreme_bounds_m"], source["extreme_bounds_m"], strict=True
    ):
        compare_components(actual, expected, position, six_figures=True)
    for actual, expected in zip(candidate["caps"], source["caps"], strict=True):
        require(
            actual["rim_station"] == expected["rim_station"],
            "actual native cap station differs",
        )
        compare_components(
            actual["outward_normal"], expected["outward_normal"], direction
        )
    for actual, expected in zip(candidate["cap_rims"], source["cap_rims"], strict=True):
        compare_components(actual["center_m"], expected["center_m"], position)
        compare_components(actual["normal"], expected["normal"], direction)
        compare_scalar(actual["radius_m"], expected["radius_m"], position)
        compare_scalar(
            abs(actual["trim"][1] - actual["trim"][0]),
            abs(expected["trim"][1] - expected["trim"][0]),
            tolerances["period_rad"],
        )


def measure(path, checksum, job, lock, lock_hash):
    from AuthorRectangleAnchors import control
    from ObserveCylinderExchange import TOLERANCES
    from ObserveLocalCylinderPart import (
        check_lifecycle,
        periodic_shape,
        snapshot_identity,
    )
    from ObserveLocalImportedPart import phase
    from RunImportedBodySources import oracle_identity

    packet, root = path.parent, Path(job["guest_root"])
    public = packet / "Result.json"
    charts = root / "Measurements"
    require(
        not public.exists()
        and not public.is_symlink()
        and root.is_dir()
        and not root.is_symlink(),
        "evaluation result already exists or the private root differs",
    )
    frozen = verify_build_lock(root, lock_hash, checksum, job, lock)
    cases = source_specification(lock)
    started = time()
    require(
        frozen["locked_at_unix_s"] < started,
        "original comparison must follow the build lock",
    )
    charts.mkdir()
    (root / "SavedCopies").mkdir()
    seed = root / "Control.SLDPRT"
    with seed.open("xb") as output:
        output.write(checked(packet / "Control.SLDPRT", CONTROL))
    seen, details, public_rows, saved = set(), {}, [], {}

    def record(label, function, *args, validate=None, **options):
        try:
            result = function(*args, **options)
            if result.get("oracle_identity"):
                identity = oracle_identity(result["oracle_identity"])
                process = identity["process_id"], identity["process_creation_filetime"]
                require(process not in seen, "native process identity repeated")
                seen.add(process)
            require(
                result["passed"]
                and result.get("oracle_identity")
                and is_digest(result.get("record_sha256")),
                "native phase did not complete with exact identity",
            )
            if validate is not None:
                validate(result)
        except Exception as error:
            print(label, repr(error))
            failure_hash = result.get("record_sha256") if "result" in locals() else None
            public_rows.append(
                {
                    "phase": label,
                    "passed": False,
                    "record_sha256": failure_hash if is_digest(failure_hash) else None,
                }
            )
            return False
        public_rows.append(
            {"phase": label, "passed": True, "record_sha256": result["record_sha256"]}
        )
        details[label] = result
        return True

    with (
        (root / "Oracle.log").open("x", encoding="utf-8") as log,
        redirect_stdout(log),
        redirect_stderr(log),
    ):
        try:
            require(
                record("ControlBefore", control, charts, "ControlBefore", seed),
                "pristine control before failed",
            )
            for slot, spec in cases.items():
                source, feature, reference, passive = original_binding(slot, lock)
                expected = {"model": spec, "faces": 3}
                original = slot + "Original"
                candidate = slot + "Candidate"
                reopen = slot + "Reopen"

                def validate_original(result):
                    check_original(result, feature, reference, passive)
                    compare_shape(
                        passive["periodic_body"], result["cold"]["shape"], TOLERANCES
                    )

                require(
                    record(
                        original,
                        phase,
                        charts,
                        original,
                        source,
                        lock["sources"][slot]["source_sha256"],
                        expected,
                        feature["name"],
                        reference=reference,
                        measure_shape=periodic_shape,
                        validate=validate_original,
                    ),
                    "locked original comparison failed",
                )
                native_copy = root / "SavedCopies" / (slot + ".SLDPRT")

                def validate_candidate(result, *, prior=None):
                    identity = (
                        snapshot_identity(prior["rebuilt"])
                        if prior is not None
                        else None
                    )
                    accepted = check_lifecycle(
                        result, identity=identity, saving=prior is None
                    )
                    require(
                        accepted["passed"]
                        and all(
                            result[state]["feature_id"]
                            == frozen["cases"][slot]["feature_id"]
                            for state in ("cold", "rebuilt")
                        ),
                        "generated BaseBody lifecycle differs",
                    )
                    for state in ("cold", "rebuilt"):
                        compare_shape(
                            details[original][state]["shape"],
                            result[state]["shape"],
                            TOLERANCES,
                        )

                require(
                    record(
                        candidate,
                        phase,
                        charts,
                        candidate,
                        destination(root, slot),
                        frozen["cases"][slot]["sha256"],
                        expected,
                        FEATURE,
                        save=native_copy,
                        measure_shape=periodic_shape,
                        validate=validate_candidate,
                    ),
                    "generated native save phase failed",
                )
                opened = details[candidate]
                saved[slot] = opened["saved_sha256"]
                require(
                    record(
                        reopen,
                        phase,
                        charts,
                        reopen,
                        native_copy,
                        saved[slot],
                        expected,
                        FEATURE,
                        reference=opened["rebuilt"]["persistent_reference"],
                        measure_shape=periodic_shape,
                        validate=lambda result: validate_candidate(
                            result, prior=opened
                        ),
                    ),
                    "fresh readonly save reopen failed",
                )
        except Exception as error:
            print(repr(error))
        finally:
            record("ControlAfter", control, charts, "ControlAfter", seed)
        try:
            require(
                verify_packet(path, checksum) == (job, lock), "public packet changed"
            )
            require(
                verify_build_lock(root, lock_hash, checksum, job, lock) == frozen,
                "build custody changed",
            )
            require(source_specification(lock) == cases, "private model recipe changed")
            checked(seed, CONTROL)
            for slot in SLOTS:
                original_binding(slot, lock)
                if slot in saved:
                    checked(root / "SavedCopies" / (slot + ".SLDPRT"), saved[slot])
            custody = True
        except Exception as error:
            print(repr(error))
            custody = False

    controls_ok = all(
        details.get(name, {}).get("passed")
        for name in ("ControlBefore", "ControlAfter")
    )
    distinct = len(seen)
    passed = (
        custody
        and controls_ok
        and tuple(row["phase"] for row in public_rows) == PHASES
        and all(row["passed"] for row in public_rows)
        and distinct == len(PHASES)
    )
    public_receipt = {
        "schema": RESULT_SCHEMA,
        "job_sha256": checksum,
        "build_lock_sha256": lock_hash,
        "writer_revision": job["writer_revision"],
        "protocol_revision": job["protocol_revision"],
        "source_lock_sha256": LOCK_SHA256,
        "source_transport_sha256": LOCK_TRANSPORT_SHA256,
        "construction_sha256": CONSTRUCTION_SHA256,
        "oracle_sha256": ORACLE,
        "oracle_version": VERSION,
        "predictor_sha256": job["files_sha256"]["Tools/ObserveCylinderExchange.py"],
        "neutral_seam_gauge": GAUGE,
        "source_domains_omitted": OMITTED,
        "authored_geometry_only": True,
        "original_source_transfer_qualified": False,
        "public_writer_qualified": False,
        "phase_receipts": public_rows,
        "distinct_native_processes": distinct,
        "native_numeric_checks": sum(
            row.get("numeric_checks", 0) for row in details.values()
        ),
        "guarded_build_processes": 4,
        "runtime_input_file_reads": 0,
        "native_calls_during_construction": 0,
        "original_files_opened_during_build": 0,
        "generated_hashes_frozen_before_original_access": True,
        "custody_unchanged": custody,
        "controls_healthy": controls_ok,
        "private_native_inputs_shared": 0,
        "private_generated_outputs_shared": 0,
        "geometry_lifecycles_passed": len(SLOTS) if passed else 0,
        "cases": {
            slot: {
                "source_sha256": lock["sources"][slot]["source_sha256"],
                "generated_sha256": frozen["cases"][slot]["sha256"],
                "saved_sha256": saved.get(slot),
                "native_lifecycle_passed": passed,
            }
            for slot in SLOTS
        },
        "passed": passed,
    }
    atomic_receipt(public, public_receipt)
    print(
        json.dumps(
            {
                "passed": passed,
                "distinct_native_processes": distinct,
                "geometry_lifecycles_passed": public_receipt[
                    "geometry_lifecycles_passed"
                ],
            }
        )
    )
    return 0 if passed else 3


def main(args):
    try:
        require(
            args.mode == "verify" or os.name == "nt",
            "private evaluation uses the Windows guest",
        )
        require(not args.job.is_symlink(), "choose the exact regular packet job")
        path = args.job.resolve()
        require(
            Path(__file__).resolve().parent == path.parent / "Tools",
            "run the staged evaluator",
        )
        job, lock = verify_packet(path, args.job_sha256)
        if args.mode == "verify":
            print(
                json.dumps(
                    {"verified": True, "native_processes": 0, "original_files_read": 0}
                )
            )
            return 0
        if args.mode == "build":
            return build(path, args.job_sha256, job, lock)
        require(
            is_digest(args.build_lock_sha256),
            "measurement requires the frozen build lock digest",
        )
        return measure(path, args.job_sha256, job, lock, args.build_lock_sha256)
    except Exception as error:
        print(
            json.dumps(
                {
                    "passed": False,
                    "stage": args.mode,
                    "failure_type": type(error).__name__,
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main(arguments))
