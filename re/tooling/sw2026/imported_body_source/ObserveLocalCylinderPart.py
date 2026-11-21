from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path, PureWindowsPath
import re
from time import time

TOOLS = frozenset(
    (
        "AuthorCurves.py",
        "AuthorImportedBody.py",
        "AuthorRectangleAnchors.py",
        "InspectFresh.py",
        "ObserveCylinderExchange.py",
        "ObserveKernelBodyRestore.py",
        "ObserveKernelExchange.py",
        "ObserveLocalCylinderPart.py",
        "ObserveLocalImportedPart.py",
        "OracleIdentity.py",
        "RunImportedBodySources.py",
        "Swapp.py",
    )
)


def parse_arguments():
    parser = ArgumentParser(
        description="Verify or measure both frozen embedded bare cylinder parts"
    )
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def checked_bootstrap(path, identity):
    if (
        not path.is_file()
        or path.is_symlink()
        or not 0 < path.stat().st_size <= 64 * 1024**2
        or type(identity) is not str
        or not re.fullmatch(r"[a-f0-9]{64}", identity)
    ):
        raise ValueError(f"invalid frozen packet input: {path.name}")
    data = path.read_bytes()
    if sha256(data).hexdigest() != identity:
        raise ValueError(f"packet hash differs: {path.name}")
    return data


def verify_tool_imports(job, checksum):
    if job.is_symlink() or job.name != "Job.json":
        raise ValueError("use the regular embedded cylinder packet job")
    path = job.resolve()
    tools = path.parent / "Tools"
    if tools.is_symlink() or Path(__file__).resolve().parent != tools:
        raise ValueError("run the exact frozen cylinder lifecycle tools")
    frozen = json.loads(checked_bootstrap(path, checksum))["tools_sha256"]
    if type(frozen) is not dict or set(frozen) != TOOLS:
        raise ValueError("embedded cylinder tool inventory differs")
    for name, identity in frozen.items():
        checked_bootstrap(tools / name, identity)


if __name__ == "__main__":
    arguments = parse_arguments()
    try:
        verify_tool_imports(arguments.job, arguments.job_sha256)
    except Exception as error:
        print(json.dumps({"stage": "refused", "failure": repr(error)}))
        raise SystemExit(2)


curves = import_module("AuthorCurves")
rectangles = import_module("AuthorRectangleAnchors")
cylinders = import_module("ObserveCylinderExchange")
local_parts = import_module("ObserveLocalImportedPart")
sources = import_module("RunImportedBodySources")

require, write_json = curves.require, curves.write_json
CONTROL, ORACLE, control = rectangles.CONTROL, rectangles.ORACLE, rectangles.control
GENERATED, NATIVE_RECEIPT = cylinders.GENERATED, cylinders.NATIVE_RECEIPT
STOCK, TOLERANCES = cylinders.STOCK, cylinders.TOLERANCES
checked, known_cases = cylinders.checked, cylinders.known_cases
measure_cylinder, source_receipt = cylinders.measure_cylinder, cylinders.source_receipt
stage_local, stock_phase = cylinders.stage_local, cylinders.stock_phase
unique_object = cylinders.unique_object
part_phase = local_parts.phase
VERSION, oracle_identity = sources.VERSION, sources.oracle_identity

SCHEMA = "kit.sw2026.embedded-bare-cylinder-lifecycle.v1"
GUEST_ROOT = "C:\\KitCylinderPart01"
BUILD_HASH = "0eadab712f6e01deedb106716b27b675ca83788aecaec1fd39fbc998132218fc"
EXCHANGE_HASH = "aa4af60b944359540e694859ee150cb0651e58bf06f776da8d82bc9b59013b11"
PLANAR_BUILD_HASH = "33b377986db581aa64edb2fdb13105e1b5aae981b24b33ffe05559c492cbacc1"
PLANAR_NATIVE_HASH = "ecd54cd147bd24b9fb6ad14835ea981e7282ea4f914a0c785a2d490d33d6970b"
PLANAR_NAME = "RectangularBare.SLDPRT"
PLANAR_HASH = "302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357"
PLANAR_SOURCE_PATH = "C:\\KitImportedProbe03\\Candidates\\RectangularBare.SLDPRT"
FEATURE = "Imported geometry"
PARTS = {
    "TranslatedZ": {
        "bytes": 8995,
        "sha256": "ffb0d3f587387500ebd774c18272cfb5abff377b278ba42c54b63df9b4e4bda1",
    },
    "ReverseY": {
        "bytes": 8992,
        "sha256": "ff0054be16d0b08d888ea6299f209f59cdc286b894cdb48c0a83203b38b6272d",
    },
}
BEFORE = ("ApplicationBefore", "PlanarBefore", "StockZBefore")
AFTER = ("StockReverseYAfter", "PlanarAfter", "ApplicationAfter")
PHASES = (
    *BEFORE,
    "TranslatedZ",
    "TranslatedZReopen",
    "ReverseY",
    "ReverseYReopen",
    *AFTER,
)
CONTROL_FILES = {
    "Control.SLDPRT": CONTROL,
    PLANAR_NAME: PLANAR_HASH,
    "CylinderZ.SLDPRT": STOCK["CylinderZ"][0],
    "CylinderReverseY.SLDPRT": STOCK["CylinderReverseY"][0],
    "NativeSources.json": NATIVE_RECEIPT,
    "NativeExchange.json": EXCHANGE_HASH,
    "PlanarBuild.json": PLANAR_BUILD_HASH,
    "PlanarNative.json": PLANAR_NATIVE_HASH,
    "Build.json": BUILD_HASH,
}


def parse(content):
    return json.loads(content, object_pairs_hook=unique_object)


def planar_case(build_bytes, native_bytes):
    build, measured = parse(build_bytes), parse(native_bytes)
    case = build["cases"]["RectangularBare"]
    phases = measured["phases"]
    require(
        build["modeled_completed_update"] is True
        and build["authored_ambient"] is True
        and case["sha256"] == PLANAR_HASH
        and case["native_path"] == PLANAR_SOURCE_PATH
        and case["feature"] == FEATURE
        and measured["oracle_sha256"] == ORACLE
        and measured["oracle_file_version"] == VERSION
        and measured["build_sha256"] == PLANAR_BUILD_HASH
        and measured["controls_healthy"] is True
        and measured["distinct_native_processes"] == 11
        and "RectangularBare" in measured["clean_lifecycles"]
        and phases["RectangularBare"]["passed"] is True
        and phases["RectangularBareReopen"]["passed"] is True
        and phases["RectangularBare"]["cold"]["feature_id"]
        == phases["RectangularBareReopen"]["cold"]["feature_id"]
        == 18,
        "previous accepted planar control provenance differs",
    )
    return case["expected_si"]


def exchange_evidence(content):
    document = parse(content)
    require(
        document["oracle_version"] == VERSION
        and document["oracle_sha256"] == ORACLE
        and document["passed"] is True
        and document["controls_healthy"] is True
        and document["packet_unchanged"] is True
        and document["distinct_processes"] == 10
        and document["native_writer_outputs"] == document["heldout_cases"] == 0
        and document["tolerances"] == TOLERANCES,
        "prior binary exchange evidence differs",
    )
    candidates = {
        phase["name"]: phase
        for phase in document["phases"]
        if phase["role"] == "generated_disclosed"
    }
    require(
        set(candidates) == GENERATED.keys()
        and all(
            phase["passed"] is True
            and phase["numeric_checks"] == 76
            and phase["load_error"] == 0
            and phase["payload"] == {"bytes": 1414, "sha256": GENERATED[name]}
            for name, phase in candidates.items()
        ),
        "binary exchange did not validate the exact part kernel inputs",
    )


def verify_build(content):
    document = parse(content)
    require(
        document["schema"] == "kit.sw2026.bare-cylinder-part-host.v1"
        and document["construction_runtime_reads"]
        == document["embedded_native_processes"]
        == document["heldout_cases"]
        == 0
        and document["embedded_native_acceptance"] is False
        and document["public_writer_qualified"] is False
        and set(document["cases"]) == PARTS.keys(),
        "host cylinder part receipt scope differs",
    )
    for name, case in document["cases"].items():
        require(
            case["part"] == PARTS[name]
            and case["feature"] == FEATURE
            and case["configuration"] == "Default"
            and case["native_path"]
            == str(PureWindowsPath(GUEST_ROOT) / "Candidates" / (name + ".SLDPRT"))
            and case["kernel"] == {"bytes": 1414, "sha256": GENERATED[name]}
            and case["readback"]["owners"]["feature_id"] == 18
            and case["readback"]["public_read_boundary"]["ordinary_geometry_decoders"]
            == 0
            and bool(
                case["readback"]["public_read_boundary"]["strict_geometry_refusal"]
            ),
            f"guarded model, locator or SDK readback boundary differs: {name}",
        )
    return document


def candidate_bytes(root, name):
    identity = PARTS[name]
    return checked(
        root / "Candidates" / (name + ".SLDPRT"), identity["sha256"], identity["bytes"]
    )


def verify_job(path, checksum):
    require(path.name == "Job.json", "use the exact embedded cylinder Job.json locator")
    document = parse(checked(path, checksum))
    root = path.parent
    tools, candidates = root / "Tools", root / "Candidates"
    require(
        all(item.is_dir() and not item.is_symlink() for item in (tools, candidates))
        and Path(__file__).resolve().parent == tools,
        "run the exact frozen cylinder lifecycle tools",
    )
    require(
        set(document)
        == {
            "schema",
            "oracle_version",
            "oracle_sha256",
            "guest_root",
            "tool_checkout_head",
            "control_files",
            "cases",
            "phases",
            "tolerances",
            "tools_sha256",
        }
        and document["schema"] == SCHEMA
        and document["oracle_version"] == VERSION
        and document["oracle_sha256"] == ORACLE
        and document["guest_root"] == GUEST_ROOT
        and document["cases"] == PARTS
        and document["control_files"] == CONTROL_FILES
        and document["phases"] == list(PHASES)
        and document["tolerances"] == TOLERANCES
        and type(document["tool_checkout_head"]) is str
        and re.fullmatch(r"[a-f0-9]{40}", document["tool_checkout_head"]),
        "embedded cylinder job profile differs",
    )
    require(
        set(document["tools_sha256"]) == TOOLS,
        "embedded cylinder tool inventory differs",
    )
    for name, identity in document["tools_sha256"].items():
        checked(tools / name, identity)
    inputs = {
        name: checked(root / name, digest) for name, digest in CONTROL_FILES.items()
    }
    source_receipt(inputs["NativeSources.json"])
    exchange_evidence(inputs["NativeExchange.json"])
    expected_planar = planar_case(
        inputs["PlanarBuild.json"], inputs["PlanarNative.json"]
    )
    build = verify_build(inputs["Build.json"])
    require(
        {item.name for item in candidates.iterdir()}
        == {name + ".SLDPRT" for name in PARTS},
        "candidate directory must contain exactly the two frozen SLDPRT files",
    )
    for name in PARTS:
        candidate_bytes(root, name)
    return document, build["cases"], expected_planar


def periodic_shape(observer, body, expected, *, temporary):
    require(
        temporary is False and not bool(observer.get(body, "IsTemporaryBody")),
        "periodic part must have its actual attached solid",
    )
    return measure_cylinder(observer, expected)


def snapshot_identity(observation):
    configuration = observation["configuration"]
    require(
        configuration == "Default"
        and tuple(observation["configurations"]) == ("Default",)
        and observation["feature"] == FEATURE
        and observation["feature_id"] == 18
        and observation["feature_faces"] == 3
        and observation["shape"]["solids"] == 1
        and observation["shape"]["faces"] == 3
        and observation["shape"]["edges"] == 2
        and observation["shape"]["vertices"] == 0
        and observation["application_state"]["needs_rebuild"] == 0,
        "candidate local feature, topology or completed part state differs",
    )
    return observation["persistent_reference"], tuple(
        tuple(row) for row in observation["tree_signature"]
    )


def check_lifecycle(result, *, reference=None, identity=None, saving=False):
    if not result["passed"]:
        return result
    try:
        require(
            result["open"] == {"returned_document": True, "error": 0, "warning": 0}
            and result["read_only"] is (not saving)
            and not result["cold"]["application_state"]["save_flag"],
            "candidate first-open or actual access state differs",
        )
        cold, rebuilt = (snapshot_identity(result[key]) for key in ("cold", "rebuilt"))
        require(
            cold == rebuilt
            and (identity is None or cold == identity)
            and (reference is None or cold[0] == reference),
            "cold, rebuilt or fresh reopen persistent owner and ordered tree differ",
        )
        if saving:
            require(
                tuple(result["save"]) == (True, 0, 0)
                and re.fullmatch(r"[a-f0-9]{64}", result["saved_sha256"]),
                "candidate did not produce one clean native save copy",
            )
    except Exception as error:
        return result | {"passed": False, "lifecycle_failure": repr(error)}
    return result


def run(path, checksum, job, cases, expected_planar):
    require(
        os.name == "nt",
        "native lifecycle execution belongs to the root-owned Windows guest",
    )
    packet, root = path.parent, Path(GUEST_ROOT)
    public = packet / "Result.json"
    require(
        not public.exists() and not public.is_symlink(),
        "embedded cylinder receipt already exists",
    )
    root.mkdir()
    controls, candidates, saved = (
        root / name for name in ("Controls", "Candidates", "SavedCopies")
    )
    for directory in (controls, candidates, saved):
        directory.mkdir()
    seed = stage_local(packet, controls, "Control.SLDPRT", CONTROL)
    planar = stage_local(packet, controls, PLANAR_NAME, PLANAR_HASH)
    stock = {
        name: stage_local(packet, controls, name + ".SLDPRT", identity[0])
        for name, identity in STOCK.items()
    }
    for name, identity in PARTS.items():
        original = stage_local(
            packet / "Candidates", candidates, name + ".SLDPRT", identity["sha256"]
        )
        require(
            PureWindowsPath(original) == PureWindowsPath(cases[name]["native_path"]),
            "candidate stage changed its modeled logical locator",
        )
    result = {
        "schema": SCHEMA,
        "job_sha256": checksum,
        "oracle_sha256": ORACLE,
        "oracle_version": VERSION,
        "tools_sha256": job["tools_sha256"],
        "phases": [],
        "controls_healthy": False,
        "passed": False,
        "embedded_lifecycles_measured": [],
        "heldout_cases": 0,
        "public_writer_qualified": False,
        "installed_sdk_periodic_brep_qualified": False,
        "tolerances": TOLERANCES,
    }
    seen = set()

    def record(name, role, operation, *args, **kwargs):
        result["stage"] = name
        write_json(public, result)
        try:
            details = operation(*args, **kwargs)
            if details.get("oracle_identity"):
                identity = oracle_identity(details["oracle_identity"])
                process = identity["process_id"], identity["process_creation_filetime"]
                require(
                    process not in seen, "native phase reused an earlier oracle process"
                )
                seen.add(process)
            else:
                require(
                    not details["passed"],
                    "successful native observation lacks its exact process identity",
                )
        except Exception as error:
            details = {"passed": False, "failure": repr(error)}
        result["phases"].append({"name": name, "role": role, **details})
        write_json(public, result)
        return details

    def application(name):
        return record(name, "application_control", control, root, name, seed)

    def planar_control(name):
        return record(
            name,
            "previously_accepted_planar_control",
            part_phase,
            root,
            name,
            planar,
            PLANAR_HASH,
            expected_planar,
            FEATURE,
        )

    def stock_control(name, case_name):
        case = known_cases()[case_name]
        return record(
            name,
            "native_stock_cylinder_control",
            stock_phase,
            root,
            name,
            stock[case["source"]],
            case,
        )

    def measure(name, source, fingerprint, expected, *, identity=None, **kwargs):
        observed = part_phase(
            root,
            name,
            source,
            fingerprint,
            expected,
            FEATURE,
            measure_shape=periodic_shape,
            **kwargs,
        )
        return check_lifecycle(
            observed,
            reference=kwargs.get("reference"),
            identity=identity,
            saving="save" in kwargs,
        )

    with (
        (root / "Oracle.log").open("x", encoding="utf-8") as log,
        redirect_stdout(log),
        redirect_stderr(log),
    ):
        try:
            begin = (
                application("ApplicationBefore")["passed"]
                and planar_control("PlanarBefore")["passed"]
                and stock_control("StockZBefore", "StockZ")["passed"]
            )
            result["candidates_enabled"] = bool(begin)
            if begin:
                for name, identity in PARTS.items():
                    filename = name + ".SLDPRT"
                    original, output = candidates / filename, saved / filename
                    expected = known_cases()[name] | {"faces": 3}
                    first = record(
                        name,
                        "candidate_cold_rebuild_save",
                        measure,
                        name,
                        original,
                        identity["sha256"],
                        expected,
                        save=output,
                    )
                    if first["passed"]:
                        signed = snapshot_identity(first["rebuilt"])
                        record(
                            name + "Reopen",
                            "candidate_fresh_read_only_reopen",
                            measure,
                            name + "Reopen",
                            output,
                            first["saved_sha256"],
                            expected,
                            reference=signed[0],
                            identity=signed,
                        )
        finally:
            stock_control("StockReverseYAfter", "StockReverseY")
            planar_control("PlanarAfter")
            application("ApplicationAfter")
    by_name = {row["name"]: row for row in result["phases"]}
    result["distinct_native_processes"] = len(seen)
    result["controls_healthy"] = all(
        by_name.get(label, {}).get("passed") for label in (*BEFORE, *AFTER)
    )
    try:
        verify_job(path, checksum)
        checked(seed, CONTROL)
        checked(planar, PLANAR_HASH)
        for name, source in stock.items():
            checked(source, STOCK[name][0])
        for name, identity in PARTS.items():
            filename = name + ".SLDPRT"
            checked(candidates / filename, identity["sha256"], identity["bytes"])
            if digest := by_name.get(name, {}).get("saved_sha256"):
                checked(saved / filename, digest)
        result["inputs_and_saved_copies_unchanged"] = True
    except Exception as error:
        result.update(
            inputs_and_saved_copies_unchanged=False, custody_failure=repr(error)
        )
    if result["controls_healthy"] and result["inputs_and_saved_copies_unchanged"]:
        result["embedded_lifecycles_measured"] = [
            name
            for name in PARTS
            if by_name.get(name, {}).get("passed")
            and by_name.get(name + "Reopen", {}).get("passed")
        ]
    result["passed"] = (
        tuple(by_name) == PHASES
        and len(seen) == len(PHASES)
        and result["embedded_lifecycles_measured"] == list(PARTS)
    )
    result["stage"] = "passed" if result["passed"] else "failed"
    result["finished_at"] = time()
    write_json(public, result)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "stage",
                    "passed",
                    "controls_healthy",
                    "distinct_native_processes",
                    "embedded_lifecycles_measured",
                )
            }
        )
    )
    return 0 if result["passed"] else 3


def main(args):
    try:
        require(
            not args.job.is_symlink(), "use the regular embedded cylinder packet job"
        )
        path = args.job.resolve()
        job, cases, expected_planar = verify_job(path, args.job_sha256)
        if args.verify_only:
            print(
                json.dumps(
                    {
                        "verified": True,
                        "job_sha256": args.job_sha256,
                        "native_processes": 0,
                    }
                )
            )
            return 0
        return run(path, args.job_sha256, job, cases, expected_planar)
    except Exception as error:
        print(json.dumps({"stage": "refused", "failure": repr(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main(arguments))
