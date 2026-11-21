from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import isclose
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import codecs
import json
import os
import sys

HERE = Path(__file__).resolve()
PACKET = "TwoStockWriterEvaluation02"
SCHEMA = "kit.sw2026.two-stock-writer-holdout-evaluation.v2"
SOURCE_LOCK = "1c07e988d425da1de7fd53ccdb30f7b18dc6b431236674404bcc1d8f3b21ae2c"
PRIOR_FREEZE = "10660269a55fa4f363ebc5f5d96e3e148a76a7cfdd628f844223a4a631fea8cb"
PRIOR_STAGE = "94a0e10010f7f5f30041eb88787cc149557a2ab959e6371dc62f06299a59e258"
WRITER_REVISION = "6fc230fb31c3195ff16da5327d4a872f51e49290"
WRITER_SRC_TREE = "93f0ef018a2e403a5cf98ba2d832a2db16b362fa"
SOURCE_AUTHOR = "re/tooling/sw2026/ThroughAllSourcePlan.py"
SOURCE_AUTHOR_PIN = "3fbbf5c54296619e88432e446f2e4675883ba5af3ea6e05a40b974fecb3f7ac5"
SLOTS = ("a", "b")
BASE = PureWindowsPath("C:/KitSdkCandidates")
PYTHON = r"C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe"
WRITTEN_AT = 1765500071
PREPARER = (
    "src/convert/adapters/solidworks/Core/Preparation/TwoStock/PrepareStockPart.py"
)
MODULES = {
    "FreezeTwoStockSources01.py": "FreezeTwoStockSources01",
    "ProbeThroughMultiStock01.py": "ProbeThroughMultiStock01",
    "ProbeThroughAutoScope01.py": "ProbeThroughAutoScope01",
    "MeasureTwoStockConstruction01.py": "MeasureTwoStockConstruction01",
}
NATIVE_PHASES = (
    "before",
    "a-open",
    "a-reopen",
    "b-open",
    "b-reopen",
    "after",
    "summary",
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, pin):
    require(
        path.is_file() and not path.is_symlink(),
        "input is missing or redirected: " + path.name,
    )
    raw = path.read_bytes()
    require(digest(raw) == pin, "input checksum differs: " + path.name)
    return raw


def wire(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def publish(path, raw):
    with path.open("xb") as output:
        output.write(raw)
    return digest(raw)


def publish_candidate(path, raw):
    expected = digest(raw)
    if path.exists() or path.is_symlink():
        checked(path, expected)
        return expected
    return publish(path, raw)


def part_name(slot):
    return "TwoStockHoldout" + slot.upper()


def imports():
    sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent)]
    return tuple(import_module(name) for name in MODULES.values())


def revision(root):
    exact = check_output(("git", "rev-parse", "HEAD"), cwd=root, text=True).strip()
    require(
        run(
            ("git", "diff", "--quiet", exact, "--", "src", "re/tooling"), cwd=root
        ).returncode
        == 0,
        "the evaluated implementation differs from its committed revision",
    )
    require(
        check_output(("git", "rev-parse", f"{exact}:src"), cwd=root, text=True).strip()
        == WRITER_SRC_TREE,
        "the production source tree differs from the original writer freeze",
    )
    return exact


def freeze(root, control, stock):
    lock_path = root / "re/solidworks/v2026/heldout/TwoStockWriterSourceLock01.json"
    lock_raw = checked(lock_path, SOURCE_LOCK)
    lock = json.loads(lock_raw)
    head = revision(root)
    preparer = check_output(("git", "show", f"{head}:{PREPARER}"), cwd=root)
    require(
        run(
            (
                "git",
                "merge-base",
                "--is-ancestor",
                lock["before_writer_revision"],
                head,
            ),
            cwd=root,
        ).returncode
        == 0,
        "the writer revision does not descend from the pre-implementation source lock",
    )
    control_trial = control.disclosed(stock.SHARED / stock.DISCLOSED)
    author_source = check_output(
        ("git", "show", f"{lock['before_writer_revision']}:{SOURCE_AUTHOR}"), cwd=root
    )
    require(
        digest(author_source) == SOURCE_AUTHOR_PIN
        and control_trial["tools_sha256"]["ThroughAllSourcePlan.py"]
        == SOURCE_AUTHOR_PIN,
        "the original source authoring labels do not match the committed evidence",
    )
    checked(root / SOURCE_AUTHOR, SOURCE_AUTHOR_PIN)
    packet = stock.SHARED / PACKET
    packet.mkdir(mode=0o700, exist_ok=False)
    sources = (
        HERE,
        HERE.with_name("MeasureTwoStockConstruction01.py"),
        *(
            HERE.parent.parent / name
            for name in MODULES
            if name != "MeasureTwoStockConstruction01.py"
        ),
    )
    tools = {
        source.name: publish(packet / source.name, source.read_bytes())
        for source in sources
    }
    publish(packet / "SourceLock.json", lock_raw)
    record = {
        "schema": SCHEMA,
        "writer_revision": WRITER_REVISION,
        "writer_src_tree": WRITER_SRC_TREE,
        "evaluator_revision": head,
        "prior_freeze_sha256": PRIOR_FREEZE,
        "prior_stage_sha256": PRIOR_STAGE,
        "authoring_datum_labels_sha256": SOURCE_AUTHOR_PIN,
        "source_lock_sha256": SOURCE_LOCK,
        "oracle_build": stock.BUILD,
        "oracle_exe_sha256": stock.ORACLE,
        "control_trial_sha256": stock.TRIAL,
        "tool_sha256": tools,
        "sdk_preparer": {"path": PREPARER, "sha256": digest(preparer)},
        "written_at": WRITTEN_AT,
        "native_phase_order": NATIVE_PHASES,
    }
    return {**record, "freeze_sha256": publish(packet / "Freeze.json", wire(record))}


def frozen(packet, pin, stock):
    result = json.loads(checked(packet / "Freeze.json", pin))
    require(
        packet.name == PACKET
        and not packet.is_symlink()
        and result["schema"] == SCHEMA
        and result["oracle_build"] == stock.BUILD
        and result["oracle_exe_sha256"] == stock.ORACLE
        and result["control_trial_sha256"] == stock.TRIAL
        and result["source_lock_sha256"] == SOURCE_LOCK
        and result["native_phase_order"] == list(NATIVE_PHASES)
        and result["written_at"] == WRITTEN_AT,
        "the evaluation freeze identifies another experiment",
    )
    require(
        result["writer_revision"] == WRITER_REVISION
        and result["writer_src_tree"] == WRITER_SRC_TREE
        and result["prior_freeze_sha256"] == PRIOR_FREEZE
        and result["prior_stage_sha256"] == PRIOR_STAGE
        and result["authoring_datum_labels_sha256"] == SOURCE_AUTHOR_PIN,
        "the corrected evaluator changed the frozen writer or authoring identity",
    )
    require(
        set(result["tool_sha256"]) == {HERE.name, *MODULES},
        "the frozen tool manifest differs",
    )
    for name, expected in result["tool_sha256"].items():
        checked(packet / name, expected)
    return result


def neutral_document(slot, design, stock, datum_names):
    from ProofModels import FRONT, RIGHT, authored_document

    a, b = design["stationary_m"], design["moving_initial_m"]
    front = (a[0][0], a[0][1], a[1][0], a[1][1])
    right = (-b[1][2], b[0][1], -b[0][2], b[1][1])
    inputs = {
        "stocks": (
            (FRONT, tuple(n * 1000 for n in front), a[1][2] * 1000, False),
            (RIGHT, tuple(n * 1000 for n in right), b[1][0] * 1000, False),
        ),
        "circle": tuple(
            n * 1000 for n in (*design["tool_center_m"], design["tool_radius_m"])
        ),
        "selected": 0,
    }
    doc = authored_document(inputs)
    features = tuple(
        replace(item, name=name)
        for item, name in zip(
            doc.feature_timeline, (stock.STEADY, stock.MOVING, stock.CUT), strict=True
        )
    )
    sketches = tuple(
        replace(item, name=name)
        for item, name in zip(doc.sketches, stock.PROFILES, strict=True)
    )
    by_id = {item.id: item.name for item in features}
    bodies = tuple(
        replace(item, name=by_id[item.final_feature_id]) for item in doc.bodies
    )
    return replace(
        doc,
        metadata={"name": part_name(slot)},
        feature_timeline=features,
        sketches=sketches,
        bodies=bodies,
        support_planes=tuple(
            replace(plane, name=name)
            for plane, name in zip(doc.support_planes, datum_names, strict=True)
        ),
    )


def generate_worker(slot, root, stock):
    sys.path[:0] = [
        str(root / "src"),
        str(HERE.parent.parent / "twostockshape"),
        str(HERE.parent.parent.parent),
    ]
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import (
        PrepareStockPart,
    )
    from ProofModels import authored_document
    from ThroughAllSourcePlan import PLANES

    checked(root / SOURCE_AUTHOR, SOURCE_AUTHOR_PIN)
    datum_names = (PLANES["front"], PLANES["right"])
    for name in (
        "DocumentValidate",
        "DocumentAssemblyValidate",
        "DocumentFeatureValidate",
        "DocumentReferenceValidate",
    ):
        import_module("interchange.document.Validation." + name)
    for name in ("DocumentProvenance", "DocumentWalk"):
        import_module("interchange.document.Models." + name)
    for encoding in (
        "ascii",
        "latin-1",
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
    ):
        codecs.lookup(encoding)
    require(callable(authored_document), "independent neutral author is unavailable")
    attempts = []

    def audit(event, _):
        if event in {
            "open",
            "os.listdir",
            "os.scandir",
            "os.system",
            "os.exec",
            "os.fork",
            "os.posix_spawn",
            "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError("guarded neutral generation attempted " + event)

    sys.addaudithook(audit)
    design = json.loads(sys.stdin.buffer.read())
    doc = neutral_document(slot, design, stock, datum_names)
    destination = str(BASE / PACKET / (part_name(slot) + ".SLDPRT"))
    candidate = PrepareStockPart(
        doc,
        BytesIO(),
        WRITTEN_AT,
        WriteOptions(values={"final_destination": destination}),
    )
    require(
        len(candidate.StreamsValue) == 10 and not attempts,
        "held-out output has unexpected streams or runtime reads",
    )
    return candidate.BytesValue


def win_call(stock, pin, phase):
    tool = str(stock.GUEST.parent / PACKET / HERE.name)
    return check_output(
        (
            "prlctl",
            "exec",
            "Windows 11",
            "--current-user",
            PYTHON,
            "-B",
            tool,
            phase,
            "--pin",
            pin,
        ),
        timeout=180,
    )


def stage(root, pin, stock):
    from ProvePublicColdStocks import run_worker

    packet = stock.SHARED / PACKET
    freeze_value = frozen(packet, pin, stock)
    require(
        revision(root) == freeze_value["evaluator_revision"],
        "the frozen evaluator revision changed before evaluation",
    )
    require(
        freeze_value["sdk_preparer"]["path"] == PREPARER,
        "the frozen SDK preparer differs",
    )
    checked(root / PREPARER, freeze_value["sdk_preparer"]["sha256"])
    require(
        not (packet / "Stage.json").exists(),
        "the frozen generation has already been staged",
    )
    prior = json.loads(
        checked(stock.SHARED / "TwoStockWriterEvaluation01/Stage.json", PRIOR_STAGE)
    )
    result = {}
    for slot in SLOTS:
        request = wire(json.loads(win_call(stock, pin, slot + "-export")))
        request_sha256 = digest(request)
        require(
            request_sha256 == prior["slots"][slot]["request_sha256"],
            "the independently authored request changed during evaluator correction",
        )
        args = (sys.executable, "-I", "-B", str(HERE), slot + "-generate")
        candidate = run(
            args, input=request, capture_output=True, timeout=90, check=True
        ).stdout
        repeated = run(
            args, input=request, capture_output=True, timeout=90, check=True
        ).stdout
        require(
            candidate == repeated, "held-out neutral generation is not deterministic"
        )
        sdk = run_worker("initial", candidate, root / "src")
        require(
            len(sdk["brep_ids"]) == 2 and sdk["cut_direction"] == [0, 0, 1],
            "ordinary strict SDK read did not reconstruct both stocks and the selected Front cut",
        )
        name = part_name(slot) + ".SLDPRT"
        result[slot] = {
            "name": name,
            "sha256": publish_candidate(packet / name, candidate),
            "bytes": len(candidate),
            "request_sha256": request_sha256,
            "cold_sdk_semantic_sha256": sdk["semantic_sha256"],
            "cold_sdk_body_count": len(sdk["brep_ids"]),
            "generation_guarded_processes": 2,
            "cold_sdk_guarded_processes": 1,
            "runtime_access_attempts": sdk["runtime_access_attempts"],
        }
    receipt = {
        "schema": SCHEMA,
        "freeze_sha256": pin,
        "writer_revision": freeze_value["writer_revision"],
        "evaluator_revision": freeze_value["evaluator_revision"],
        "slots": result,
    }
    return {**receipt, "stage_sha256": publish(packet / "Stage.json", wire(receipt))}


def private_sources(packet, lock_module, stock):
    raw = checked(packet / "SourceLock.json", SOURCE_LOCK)
    original = Path(BASE / lock_module.PACKET)
    checked(original / "SourceLock.json", SOURCE_LOCK)
    lock = json.loads(raw)
    private = lock_module.load_private(
        original, lock["public_freeze_sha256"], lock["private_plan_sha256"]
    )
    require(set(private["designs"]) == set(SLOTS), "the private design slots changed")
    return original, lock, private["designs"]


def source_reference(original, entry, stock):
    path = original / entry["slot"]
    for phase, pin in zip(
        ("AutoAuthor", "AutoReopen"), entry["phase_sha256"], strict=True
    ):
        checked(path / phase / "Record.json", pin)
    raw = checked(path / "AutoAuthor" / stock.PART, entry["sha256"])
    require(len(raw) == entry["bytes"], "source CAD file size differs")
    result = stock.prior_phase(path, "AutoReopen")
    require(
        result["passed"] and result["result"]["opened_sha256"] == entry["sha256"],
        "locked native reference differs",
    )
    return result["result"]


def compare(reference, candidate, stock):
    names = {*stock.PROFILES, stock.STEADY, stock.MOVING, stock.CUT}
    old_tree, new_tree = reference["tree"], candidate["tree"]
    result = {"full_tree_equal": old_tree == new_tree, "checks": 0}
    require(
        [row for row in old_tree if row["name"] in names]
        == [row for row in new_tree if row["name"] in names]
        and reference["profiles"] == candidate["profiles"],
        "native authored feature rows or signed sketch supports differ",
    )
    for key in ("feature_scope", "auto_select"):
        require(
            reference["cut_scope"][key] == candidate["cut_scope"][key],
            "native cut scope differs",
        )
    require(
        not reference["moving_stock_cut"] and not candidate["moving_stock_cut"],
        "the unrelated stock was cut",
    )

    def close(actual, expected, absolute):
        require(
            isclose(actual, expected, rel_tol=5e-7, abs_tol=absolute),
            "native numeric comparison differs",
        )
        result["checks"] += 1

    for name in (stock.STEADY, stock.MOVING):
        left, right = reference["drivers"][name], candidate["drivers"][name]
        require(
            left["owner"].split("@")[:2] == right["owner"].split("@")[:2],
            "driver ownership differs",
        )
        close(right["value_m"], left["value_m"], 1e-12)
        left, right = reference["bodies"][name], candidate["bodies"][name]
        require(left["cut_face"] is right["cut_face"], "cut face provenance differs")
        close(right["volume_m3"], left["volume_m3"], 1e-22)
        close(right["area_m2"], left["area_m2"], 1e-18)
        for key in ("com_m", "box_m"):
            for given, wanted in zip(right[key], left[key], strict=True):
                close(given, wanted, 1e-10)
    if not result["full_tree_equal"]:
        result["native_tree_lengths"] = [len(old_tree), len(new_tree)]
        result["native_tree_sha256"] = [
            digest(wire(tree)) for tree in (old_tree, new_tree)
        ]
    return result


def case_result(original, folder, entry, staged, stock, controls_passed):
    reference = source_reference(original, entry, stock)
    native = {}
    for phase in ("Open", "Reopen"):
        path = folder / phase / "Record.json"
        if path.is_file() and not path.is_symlink():
            row = stock.prior_phase(folder, phase)
            native[phase] = {
                "sha256": digest(path.read_bytes()),
                "passed": row["passed"],
                "open": row["result"].get("open"),
                "measurements": row["result"],
            }
    lifecycle = len(native) == 2 and all(row["passed"] for row in native.values())
    comparisons, failures = {}, {}
    if lifecycle and controls_passed:
        first, last = (native[phase]["measurements"] for phase in ("Open", "Reopen"))
        snapshots = {
            "initial": (reference["before_edit"], first["before_edit"]),
            "edited": (reference["after_edit"], first["after_edit"]),
            "reopened": (reference["after_edit"], last["before_edit"]),
        }
        for name, (expected, observed) in snapshots.items():
            try:
                comparisons[name] = compare(expected, observed, stock)
            except ValueError as error:
                failures[name] = str(error)
    return {
        "source_sha256": entry["sha256"],
        "generated_sha256": staged["sha256"],
        "native_phases": {
            phase: {key: value for key, value in row.items() if key != "measurements"}
            for phase, row in native.items()
        },
        "lifecycle_passed": lifecycle,
        "comparison": comparisons,
        "comparison_failures": failures,
        "full_native_tree_equal": len(comparisons) == 3
        and all(item["full_tree_equal"] for item in comparisons.values()),
    }


def observe(phase, pin, stage_pin, lock_module, stock, control, measure):
    packet = HERE.parent
    plan = frozen(packet, pin, stock)
    original, lock, designs = private_sources(packet, lock_module, stock)
    if phase.endswith("-export"):
        slot = phase.split("-")[0]
        entry = next(item for item in lock["sources"] if item["slot"] == slot)
        source_reference(original, entry, stock)
        return designs[slot]
    require(stage_pin, "native evaluation requires an exact staged generation receipt")
    stage = json.loads(checked(packet / "Stage.json", stage_pin))
    require(
        stage["schema"] == SCHEMA
        and stage["freeze_sha256"] == pin
        and stage["writer_revision"] == plan["writer_revision"]
        and stage["evaluator_revision"] == plan["evaluator_revision"]
        and set(stage["slots"]) == set(SLOTS),
        "staged generation identifies another evaluation revision",
    )
    for slot, value in stage["slots"].items():
        require(
            value["name"] == part_name(slot) + ".SLDPRT"
            and value["request_sha256"] == digest(wire(designs[slot]))
            and value["runtime_access_attempts"] == 0,
            "staged candidate does not bind to the locked request",
        )
        checked(packet / value["name"], value["sha256"])
    folder = Path(BASE / PACKET)
    trial = packet.with_name(stock.DISCLOSED)
    controls = control.disclosed(trial)
    sys.path.insert(0, str(trial / "Tools"))
    if phase == "before":
        folder.mkdir(exist_ok=False)
    if phase in ("before", "after"):
        return control.measure(folder, phase.capitalize(), trial, controls)
    before = stock.prior_phase(folder, "Before")
    require(before["passed"], "the leading native control failed")
    if phase != "summary":
        slot, action = phase.split("-")
        if action == "open":
            (folder / slot).mkdir(exist_ok=False)
        stock.DESIGN = designs[slot]
        measure.PART = stage["slots"][slot]["name"]
        return measure.native_candidate(
            stock,
            folder / slot,
            {"candidate_sha256": stage["slots"][slot]["sha256"]},
            action.capitalize(),
        )
    after = stock.prior_phase(folder, "After")
    controls_passed = before["passed"] and after["passed"]
    cases = {
        entry["slot"]: case_result(
            original,
            folder / entry["slot"],
            entry,
            stage["slots"][entry["slot"]],
            stock,
            controls_passed,
        )
        for entry in lock["sources"]
    }
    qualified = sum(case["full_native_tree_equal"] for case in cases.values())
    result = {
        "schema": SCHEMA,
        "source_lock_sha256": SOURCE_LOCK,
        "freeze_sha256": pin,
        "stage_sha256": stage_pin,
        "writer_revision": plan["writer_revision"],
        "writer_src_tree": plan["writer_src_tree"],
        "evaluator_revision": plan["evaluator_revision"],
        "prior_freeze_sha256": plan["prior_freeze_sha256"],
        "oracle_build": stock.BUILD,
        "oracle_exe_sha256": stock.ORACLE,
        "controls_passed": controls_passed,
        "control_sha256": {
            phase: digest((folder / phase / "Record.json").read_bytes())
            for phase in ("Before", "After")
        },
        "native_candidate_records": sum(
            len(case["native_phases"]) for case in cases.values()
        ),
        "cases": cases,
        "qualified_holdout_cases": qualified,
        "passed": controls_passed and qualified == len(SLOTS),
    }
    publish(folder / "Summary.json", wire(result))
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "phase",
        choices=(
            "freeze",
            "stage",
            *NATIVE_PHASES,
            *(f"{slot}-{mode}" for slot in SLOTS for mode in ("export", "generate")),
        ),
    )
    parser.add_argument("--pin")
    parser.add_argument("--stage-pin")
    args = parser.parse_args()
    lock_module, stock, control, measure = imports()
    if os.name == "nt":
        result = observe(
            args.phase, args.pin, args.stage_pin, lock_module, stock, control, measure
        )
    else:
        root = HERE.parents[5]
        if args.phase.endswith("-generate"):
            sys.stdout.buffer.write(
                generate_worker(args.phase.split("-")[0], root, stock)
            )
            raise SystemExit(0)
        if args.phase == "freeze":
            result = freeze(root, control, stock)
        elif args.phase == "stage":
            result = stage(root, args.pin, stock)
        else:
            raise ValueError("native phases run inside the pinned Windows guest")
    sys.stdout.buffer.write(wire(result))
    raise SystemExit(0 if result.get("passed", True) else 1)
