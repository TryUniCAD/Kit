from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
from traceback import format_exc
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PatternParityPacket import (
    APPLICATIONS, BUILD, PRIVATE_ROOT, PRIOR_FREEZE, PRIOR_RESULT, PRIOR_TRIAL, SDK_REVISION,
    SLOTS, SOURCE_TRIAL, STATES, checked, check_product, check_request, digest, encode, exclusive,
    invoke, pinned_result, require, unpack_sources, verified_packet,
)


def assert_python_only():
    require(not APPLICATIONS.intersection(name.split(".")[0] for name in sys.modules),
            "parity supervisor imported an application")


def old_tools(packet):
    previous = (packet.parent.parent / PRIOR_TRIAL / "Packet").resolve(strict=True)
    manifest = json.loads(checked(previous / "Freeze.json", PRIOR_FREEZE))
    require({member.relative_to(previous).as_posix() for member in previous.rglob("*") if member.is_file()}
            == set(manifest["packet_files"]) | {"Freeze.json"}, "previous packet file closure changed")
    tools = previous / "Tools"
    require(tools.resolve(strict=True).is_relative_to(previous) and not tools.is_symlink()
            and not tools.is_junction(), "previous tool directory escapes its pinned packet")
    for name, pin in manifest["packet_files"].items():
        if name.startswith("Tools/") and name.endswith(".py"):
            candidate = previous / name
            require(candidate.parent == tools, "unexpected prior helper directory")
            checked(candidate, pin)
    sys.path.insert(0, str(tools))
    import RunPatternEvaluation as original
    import PlanPatternEvaluation as planner
    from PatternDatumHoldoutIntent import require_private_dir
    from PatternEnvelopeSpec import specification

    require(Path(original.__file__).resolve() == tools / "RunPatternEvaluation.py"
            and Path(planner.__file__).resolve() == tools / "PlanPatternEvaluation.py",
            "previous source or evaluation helper import escaped the verified tools")
    require(original.verified(previous, PRIOR_FREEZE) == manifest
            and Path(manifest["guest_root"]).resolve(strict=True) == previous.parent,
            "previous evaluation package changed")
    angle = specification()["direction_datum"]["arguments"][1]
    assert_python_only()
    return previous, original, planner.planned, require_private_dir, angle, manifest["epoch"]


def previous_files(original, private_guard, source, measured, native_result):
    source_root = Path(original.PRIVATE_SOURCE) / "Native"
    immutable_sources = original.preserve_source(source_root, source, measured, private_guard)
    slot = source["slot"]
    require(slot == measured["slot"] == native_result["slot"]
            and measured["native_artifacts"]["original"] == native_result["source_initial_sha256"],
            "old generated candidate does not belong to its native source slot")
    home = Path(original.PRIVATE_EVAL)
    candidates = home / "Native" / slot / "Candidates"
    private_guard(candidates, home)
    paths = {role: candidates / immutable_sources[role].name for role in STATES}
    hashes = {"original": native_result["generated_sha256"],
              **{role: native_result["saved_derivatives"][role]["sha256"] for role in STATES[1:]}}
    before = {}
    for role in STATES:
        private_guard(paths[role], home)
        before[role] = checked(paths[role], hashes[role])
    return paths["original"], before["original"]


def private_process(entry, mode, raw, case, label):
    task = invoke(sys.executable, entry, mode, raw, case)
    if task.returncode or task.stderr:
        exclusive(case / (label + ".stdout"), task.stdout)
        exclusive(case / (label + ".stderr"), task.stderr)
        raise ValueError("isolated neutral bridge or writer refused")
    return json.loads(task.stdout)


def compare_slot(entry, case, modeled, locator, old_raw, old_pin, private_guard, home):
    request = check_request(private_process(entry, "--bridge", encode(modeled), case, "Bridge"))
    require(request["target"] == {"PathName": str(locator), "SavedAt": modeled["seed"]["epoch"]},
            "neutral bridge changed the candidate locator or creation epoch")
    neutral = encode(request)
    products = []
    for stage in ("First", "Repeat"):
        product, payload = check_product(private_process(entry, "--emit", neutral, case, stage))
        output = case / stage / locator.name
        private_guard(output, home)
        output.parent.mkdir(exist_ok=False)
        exclusive(output, payload)
        checked(output, {"bytes": product["bytes"], "sha256": product["sha256"]})
        products.append((product, payload))
    first, second = products
    deterministic = first == second
    equal = deterministic and first[1] == old_raw
    return {
        "slot": case.name, "prior_native_sha256": old_pin, "generated_sha256": first[0]["sha256"],
        "repeat_sha256": second[0]["sha256"], "generated_bytes": first[0]["bytes"],
        "prior_native_bytes": len(old_raw), "stream_count": len(first[0]["streams"]),
        "typed_replays_per_generation": first[0]["typed_replays"], "writer_processes": 2,
        "bridge_processes": 1, "runtime_file_reads": 0,
        "deterministic": deterministic, "byte_equal": equal,
        "disposition": "byte-equal" if equal else "byte-difference" if deterministic else "repeat-difference",
    }


def run_parity(packet, pin):
    manifest = verified_packet(packet, pin)
    require(packet.parent == Path(str(PureWindowsPath(manifest["guest_root"]))).resolve(strict=True),
            "parity packet is outside its fixed share root")
    previous, original, planned, private_guard, angle, epoch = old_tools(packet)
    prior_public = previous.parent / "Public" / "Result.json"
    prior = pinned_result(checked(prior_public, PRIOR_RESULT))
    home = Path(PRIVATE_ROOT)
    public = packet.parent / "Public"
    private_guard(home, home)
    require(not home.exists() and not public.exists() and not public.is_symlink() and not public.is_junction(),
            "parity requires an unused output and receipt directory")
    home.mkdir(exist_ok=False)
    private_guard(home, home)
    public.mkdir(exist_ok=False)
    require(public.resolve(strict=True).parent == packet.parent, "public receipt escapes its packet root")
    cases, preserved, frozen = [], False, None
    source_share = packet.parent.parent / SOURCE_TRIAL
    try:
        entry = unpack_sources(
            checked(packet / "Source.zip", manifest["packet_files"]["Source.zip"]), manifest["source_members"], home / "Code"
        )
        lock, frozen = original.source_freeze(source_share)
        require(prior["source_lock_sha256"] == original.SOURCE_SHA,
                "prior qualification uses a different source lock")
        require(tuple(row["slot"] for row in frozen["cases"]) == SLOTS,
                "immutable source slots do not match the previous measurement")
        for source, measured, native in zip(frozen["cases"], lock["slots"], prior["cases"], strict=True):
            slot = source["slot"]
            case = home / slot
            case.mkdir(exist_ok=False)
            private_guard(case, home)
            try:
                locator, old_raw = previous_files(original, private_guard, source, measured, native)
                model = planned(source, locator, epoch, angle)["original"]["modeled_input"]
                cases.append(compare_slot(entry, case, model, locator, old_raw, native["generated_sha256"], private_guard, home))
            except Exception:
                exclusive(case / "Failure.log", format_exc().encode("utf-8"))
                cases.append({"slot": slot, "prior_native_sha256": native["generated_sha256"],
                              "byte_equal": False, "disposition": "generation-or-custody-refused"})
    except Exception:
        exclusive(home / "Failure.log", format_exc().encode("utf-8"))
    finally:
        try:
            require(frozen is not None and verified_packet(packet, pin) == manifest
                    and original.verified(previous, PRIOR_FREEZE)["epoch"] == epoch
                    and pinned_result(checked(prior_public, PRIOR_RESULT)) == prior,
                    "measured source or code snapshot did not retain its original identity")
            lock_after, intent_after = original.source_freeze(source_share)
            require(lock_after == lock and intent_after == frozen, "immutable independent source design changed")
            for source, measured, native in zip(frozen["cases"], lock_after["slots"], prior["cases"], strict=True):
                previous_files(original, private_guard, source, measured, native)
            assert_python_only()
            preserved = True
        except Exception:
            exclusive(home / "FinalIntegrity.log", format_exc().encode("utf-8"))
    complete = preserved and len(cases) == 2 and all(case.get("deterministic") is True for case in cases)
    matched = sum(case["byte_equal"] for case in cases) if preserved else 0
    result = {
        "schema": "kit.sw2026.oblique-pattern-default-parity-result.v1", "packet_sha256": pin,
        "prior_freeze_sha256": PRIOR_FREEZE, "prior_result_sha256": PRIOR_RESULT,
        "source_lock_sha256": prior["source_lock_sha256"], "sdk_revision": SDK_REVISION, "native_build": BUILD,
        "prior_artifacts_immutable": preserved, "cases": cases, "completed": complete, "matching_cases": matched,
        "different_cases": sum(case["disposition"] == "byte-difference" for case in cases) if preserved else 0,
        "native_processes_started": 0, "private_data_guest_only": True,
        "disposition": "exact-byte-parity" if complete and matched == 2 else "complete-byte-difference"
                       if complete else "parity-refused",
    }
    raw = encode(result)
    exclusive(public / "Result.json", raw)
    print(json.dumps({"result_sha256": digest(raw), "completed": complete, "matching_cases": matched,
                      "native_processes_started": 0}), flush=True)
    return 0 if complete and matched == 2 else 2 if complete else 1


def main():
    parser = ArgumentParser(description="Guest-only comparison of the current neutral writer with previously qualified bytes")
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    require(os.name == "nt" and sys.version_info[:2] == (3, 12),
            "protected parity is confined to its Windows Python 3.12 custodian")
    return run_parity(Path(__file__).resolve().parents[1], args.pin)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"completed":false,"disposition":"transport-refused"}', flush=True)
        raise SystemExit(1) from None
