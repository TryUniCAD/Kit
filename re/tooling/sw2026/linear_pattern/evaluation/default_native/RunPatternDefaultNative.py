from argparse import ArgumentParser, SUPPRESS
from pathlib import Path
from subprocess import DEVNULL, STDOUT, run
from traceback import format_exc
from types import SimpleNamespace
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from NativePatternPacket import PARITY_MANIFEST, PARITY_RESULT, PRIVATE, ROLES, SLOT, SOURCE_LOCK, divergent, verified
from PatternLocatorLease import install, private_lock, restore
from PatternParityPacket import (
    BUILD, PRIVATE_ROOT as PARITY_PRIVATE, PRIOR_FREEZE, PRIOR_RESULT, SDK_REVISION, SOURCE_TRIAL,
    TRIAL as PARITY_TRIAL, STATES, checked, digest, encode, exclusive, pinned_result, require, verified_packet,
)


def load_custody(packet, manifest):
    parity = (packet.parent.parent / PARITY_TRIAL / "Packet").resolve(strict=True)
    frozen_parity = verified_packet(parity, PARITY_MANIFEST)
    parity_public = parity.parent / "Public" / "Result.json"
    scope = divergent(checked(parity_public, PARITY_RESULT))
    require(scope == manifest["scope"], "staged divergence differs from redacted authority")
    parity_tools = (parity / "Tools").resolve(strict=True)
    sys.path.insert(0, str(parity_tools))
    import RunPatternDefaultParity as previous

    require(Path(previous.__file__).resolve() == parity_tools / "RunPatternDefaultParity.py",
            "parity lookup escaped the pinned Python closure")
    old_packet, original, planned, guard, angle, epoch = previous.old_tools(parity)
    old_result = old_packet.parent / "Public" / "Result.json"
    prior = pinned_result(checked(old_result, PRIOR_RESULT))
    require(prior["source_lock_sha256"] == original.SOURCE_SHA == SOURCE_LOCK,
            "already qualified candidate has a different source lock")
    reference = packet.parent.parent / SOURCE_TRIAL
    lock, intent = original.source_freeze(reference)
    source, = (row for row in intent["cases"] if row["slot"] == SLOT)
    measured, = (row for row in lock["slots"] if row["slot"] == SLOT)
    native, = (row for row in prior["cases"] if row["slot"] == SLOT)
    require(native["generated_sha256"] == scope["prior_native_sha256"], "old native subject differs")
    source_root = Path(original.PRIVATE_SOURCE) / "Native"
    original_paths = original.preserve_source(source_root, source, measured, guard)
    old_home = Path(original.PRIVATE_EVAL)
    candidate = old_home / "Native" / SLOT / "Candidates" / original_paths["original"].name
    guard(candidate, old_home)
    raw = retained_candidate(scope, candidate.name, guard)
    return SimpleNamespace(
        guard=guard, previous=previous, original=original, parity=parity, frozen_parity=frozen_parity,
        parity_public=parity_public, old_result=old_result, old_packet=old_packet, reference=reference,
        lock=lock, intent=intent, source=source, measured=measured, original_paths=original_paths,
        native=native, candidate=candidate, raw=raw, plans=planned(source, candidate, epoch, angle),
    )


def retained_candidate(scope, name, guard):
    home = Path(PARITY_PRIVATE)
    pin = {"sha256": scope["generated_sha256"], "bytes": scope["generated_bytes"]}
    copies = []
    for role in ("First", "Repeat"):
        path = home / SLOT / role / name
        guard(path, home)
        copies.append(checked(path, pin))
    require(copies[0] == copies[1], "guest-retained deterministic candidates differ")
    return copies[0]


def preserved(custody, scope):
    found, _ = custody.previous.previous_files(
        custody.original, custody.guard, custody.source, custody.measured, custody.native,
    )
    require(found == custody.candidate and retained_candidate(scope, found.name, custody.guard) == custody.raw,
            "original locator or immutable parity copies changed")


def stage_controls(old_packet, work):
    from RunPatternDatumHoldout import CONTROLS

    folder = work / "Controls"
    folder.mkdir(exist_ok=False)
    for name, (_, pin) in CONTROLS.items():
        path = folder / name
        exclusive(path, checked(old_packet / "Controls" / name, pin))
        checked(path, pin)


def native_sources(custody, work, api, receipt, stamps):
    from ObservePatternEvaluation import observe

    base = custody.plans["original"]
    snapshots = {}
    for role in STATES:
        path = custody.original_paths[role]
        pin = custody.measured["native_artifacts"][role]
        label = "source-" + role
        result = custody.original.observed_phase(receipt, stamps, SLOT, label, lambda: observe(
            work, label, path, {"sha256": pin}, base, custody.plans[role], api,
        ))
        snapshots[role] = result["rebuilt"]
    require(all(row["tree"] == snapshots["original"]["tree"]
                and row["dependencies"] == snapshots["original"]["dependencies"] for row in snapshots.values()),
            "immutable native source saves lost their complete tree or direct dependency order")
    return snapshots


def native_candidate(custody, work, api, receipt, stamps, sources, scope):
    from ObservePatternEvaluation import observe
    from PlanPatternEvaluation import DRIVERS, compare_native

    baseline = custody.plans["original"]
    derivatives = work / "Derivatives"
    derivatives.mkdir(exist_ok=False)
    for role in DRIVERS:
        label = role + "-edit"
        derivative = derivatives / custody.original_paths[role].name
        custody.guard(derivative, Path(PRIVATE))
        edited = custody.original.observed_phase(receipt, stamps, SLOT, label, lambda: observe(
            work, label, custody.candidate, {"sha256": scope["generated_sha256"]},
            baseline, custody.plans[role], api, edit_role=role, destination=derivative,
        ))
        compare_native(edited["rebuilt"], sources["original"])
        compare_native(edited["edited"], sources[role])
        receipt["compared_snapshots"] += 2
        label = role + "-reopen"
        reopened = custody.original.observed_phase(receipt, stamps, SLOT, label, lambda: observe(
            work, label, derivative, edited["saved"], baseline, custody.plans[role], api,
        ))
        compare_native(reopened["rebuilt"], sources[role])
        compare_native(reopened["rebuilt"], edited["edited"])
        receipt["compared_snapshots"] += 1
        receipt["derivatives"][role] = edited["saved"]
        checked(custody.candidate, scope["generated_sha256"])
    require(set(receipt["derivatives"]) == set(DRIVERS), "both separately edited saves are required")


def finalize_integrity(packet, pin, manifest, custody, work, receipt):
    require(verified(packet, pin) == manifest and custody.original.verified(custody.old_packet, PRIOR_FREEZE)
            and verified_packet(custody.parity, PARITY_MANIFEST) == custody.frozen_parity
            and divergent(checked(custody.parity_public, PARITY_RESULT)) == manifest["scope"]
            and pinned_result(checked(custody.old_result, PRIOR_RESULT))["source_lock_sha256"] == SOURCE_LOCK,
            "one of the bound public freezes changed")
    lock, intent = custody.original.source_freeze(custody.reference)
    require(lock == custody.lock and intent == custody.intent, "immutable protected source intent changed")
    preserved(custody, manifest["scope"])
    for role, identity in receipt["derivatives"].items():
        checked(work / "Derivatives" / custody.original_paths[role].name, {
            "sha256": identity["sha256"], "bytes": identity["bytes"],
        })


def collect(packet, pin, manifest, custody, home):
    import Swapp
    from RunPatternDatumHeight import registered
    from RunPatternDatumHoldout import CONTROLS, observe_controls, preserve_controls

    scope = manifest["scope"]
    work = home / "Native"
    hold = home / "Handoff"
    work.mkdir(exist_ok=False)
    hold.mkdir(exist_ok=False)
    custody.guard(work, home)
    custody.guard(hold, home)
    receipt = {"controls": [], "phases": [], "derivatives": {}, "compared_snapshots": 0, "state": "preflight"}
    stamps, before = [], None
    complete, installed, restored, verified_inputs, controls_equal = False, False, False, False, False
    try:
        require(not Swapp.application_pids(), "shared native oracle must be idle")
        preserved(custody, scope)
        stage_controls(custody.old_packet, work)
        api = registered(custody.old_packet)
        exclusive(work / "RegisteredApi.json", encode(api))
        receipt["state"] = "control-before"
        rows, identities, before = observe_controls(work, work, "before")
        receipt["controls"].extend(rows)
        stamps.extend(identities)
        require(len(rows) == 2 and all(row["passed"] for row in rows), "before controls were not healthy")
        receipt["state"] = "source"
        references = native_sources(custody, work, api, receipt, stamps)
        receipt["state"] = "candidate"
        require(not Swapp.application_pids(), "native source process remains active")
        install(hold, custody.candidate, scope["prior_native_sha256"], custody.raw, pin)
        installed = True
        native_candidate(custody, work, api, receipt, stamps, references, scope)
        complete = True
    except Exception:
        exclusive(work / "Failure.log", format_exc().encode("utf-8"))
    finally:
        try:
            require(not Swapp.application_pids(), "stop the active native process before recovery")
            restore(hold, custody.candidate, scope["prior_native_sha256"], custody.raw, pin)
            restored = True
        except Exception:
            exclusive(work / "RestoreFailure.log", format_exc().encode("utf-8"))
        try:
            if before is not None:
                rows, identities, after = observe_controls(work, work, "after")
                receipt["controls"].extend(rows)
                stamps.extend(identities)
                require(len(rows) == 2 and all(row["passed"] for row in rows), "after controls were not healthy")
                preserve_controls(before, after)
                controls_equal = True
        except Exception:
            exclusive(work / "ControlFailure.log", format_exc().encode("utf-8"))
        try:
            require(restored and not Swapp.application_pids(), "prior locator or native process state is unresolved")
            finalize_integrity(packet, pin, manifest, custody, work, receipt)
            for name, (_, control_pin) in CONTROLS.items():
                if (work / "Controls" / name).is_file():
                    checked(work / "Controls" / name, control_pin)
            verified_inputs = True
        except Exception:
            exclusive(work / "IntegrityFailure.log", format_exc().encode("utf-8"))
    passed = bool(complete and restored and verified_inputs and controls_equal and receipt["compared_snapshots"] == 6
                  and tuple(row["role"] for row in receipt["phases"]) == ROLES
                  and len(receipt["controls"]) == 4 and all(row["passed"] for row in (*receipt["controls"], *receipt["phases"]))
                  and len(stamps) == 11 and stamps == sorted(set(stamps)))
    receipt.update(process_creation_filetimes=stamps, prior_locator_restored=restored,
                   original_artifacts_immutable=verified_inputs, controls_equal=controls_equal, passed=passed)
    raw = encode(receipt)
    exclusive(work / "PrivateResult.json", raw)
    return {
        "schema": "kit.sw2026.oblique-pattern-default-native-result.v1", "packet_sha256": pin,
        "parity_result_sha256": PARITY_RESULT, "prior_result_sha256": PRIOR_RESULT, "source_lock_sha256": SOURCE_LOCK,
        "sdk_revision": SDK_REVISION, "native_build": BUILD, "slot": SLOT, "generated_sha256": scope["generated_sha256"],
        "passed": passed, "private_data_guest_only": True, "private_receipt_sha256": digest(raw),
        "same_original_locator": installed, "prior_locator_restored": restored,
        "original_artifacts_immutable": verified_inputs, "controls_equal": controls_equal,
        "distinct_processes": len(set(stamps)), "compared_snapshots": receipt["compared_snapshots"],
        "numeric_checks": sum(row["checks"] for row in receipt["phases"]),
        "controls": [{key: row[key] for key in ("control_slot", "role", "passed")} for row in receipt["controls"]],
        "phases": [{key: row[key] for key in ("role", "passed", "checks")} for row in receipt["phases"]],
        "disposition": "native-qualified" if passed else "native-refused" if restored else "restore-required",
    }


def worker(packet, manifest, home, pin, restoring):
    custody = load_custody(packet, manifest)
    custody.guard(home, home)
    custody.guard(home / "Transport.lock", home)
    if restoring:
        import Swapp

        require(home.is_dir(), "no native working directory to restore")
        custody.guard(home / "Handoff", home)
        with private_lock(home):
            require(not Swapp.application_pids(), "stop the active native process before recovery")
            restore(home / "Handoff", custody.candidate, manifest["scope"]["prior_native_sha256"], custody.raw, pin)
            finalize_integrity(packet, pin, manifest, custody, home / "Native", {"derivatives": {}})
        return 0
    public = packet.parent / "Public"
    require(home.is_dir() and not public.exists() and not public.is_symlink() and not public.is_junction(),
            "qualified native comparison needs unused local and public result roots")
    public.mkdir(exist_ok=False)
    require(public.resolve(strict=True).parent == packet.parent, "public receipt escaped the dedicated packet root")
    with private_lock(home):
        result = collect(packet, pin, manifest, custody, home)
    exclusive(public / "Result.json", encode(result))
    return int(not result["passed"])


def transport(packet, home, pin, restoring):
    public = packet.parent / "Public"
    require(home.drive == "C:" and home.resolve() == home and not home.is_symlink() and not home.is_junction(),
            "private transport escaped the fixed local C drive")
    if restoring:
        require(home.is_dir(), "no private comparison to restore")
    else:
        require(not public.exists(), "new public receipt directory required")
        home.mkdir(exist_ok=False)
    log = home / ("RestoreTransport.log" if restoring else "Transport.log")
    require(not log.is_symlink() and not log.is_junction(), "private transport log cannot be a link")
    argv = [sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--pin", pin, "--worker"]
    if restoring:
        argv.append("--restore-only")
    with log.open("ab" if restoring else "xb") as output:
        outcome = run(argv, cwd=home, stdin=DEVNULL, stdout=output, stderr=STDOUT, check=False)
    if restoring:
        summary = {"prior_locator_restored": outcome.returncode == 0}
    elif (public / "Result.json").is_file():
        raw = (public / "Result.json").read_bytes()
        redacted = json.loads(raw)
        summary = {key: redacted[key] for key in ("passed", "distinct_processes", "prior_locator_restored")}
        summary["result_sha256"] = digest(raw)
    else:
        summary = {"passed": False, "disposition": "no-terminal-receipt"}
    print(json.dumps(summary), flush=True)
    return outcome.returncode


def main():
    parser = ArgumentParser(description="Guest-only native test of the previously frozen oblique pattern divergence")
    parser.add_argument("--pin", required=True)
    parser.add_argument("--restore-only", action="store_true")
    parser.add_argument("--worker", action="store_true", help=SUPPRESS)
    args = parser.parse_args()
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "reserved Windows Python 3.12 oracle required")
    packet = Path(__file__).resolve().parents[1]
    manifest = verified(packet, args.pin)
    require(packet.parent == Path(manifest["guest_root"]).resolve(strict=True), "unexpected packet locator")
    home = Path(PRIVATE)
    if args.worker:
        require(Path.cwd() == home, "native worker needs its private transport directory")
        return worker(packet, manifest, home, args.pin, args.restore_only)
    return transport(packet, home, args.pin, args.restore_only)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"passed":false,"disposition":"transport-refused"}', flush=True)
        raise SystemExit(1) from None
