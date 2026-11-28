from argparse import ArgumentParser
from pathlib import Path
from traceback import format_exc
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PatternParityPacket import (
    PRIOR_FREEZE, PRIOR_RESULT, SLOTS, SOURCE_TRIAL, TRIAL as BASE_TRIAL, PRIVATE_ROOT as BASE_PRIVATE,
    checked, digest, encode, exclusive, pinned_result, require, verified_packet,
)
from PublicPatternPacket import (
    BASE_MANIFEST, BASE_RESULT, PRIVATE, SDK_REVISION, SDK_TREE, SOURCE_LOCK, frozen_slots, install_overlay, verified,
)


def previous_packet(packet):
    prior = (packet.parent.parent / BASE_TRIAL / "Packet").resolve(strict=True)
    manifest = verified_packet(prior, BASE_MANIFEST)
    tools = prior / "Tools"
    sys.path.insert(0, str(tools))
    import RunPatternDefaultParity as original

    require(Path(original.__file__).resolve() == tools / "RunPatternDefaultParity.py",
            "protected bridge supervision is outside its pinned tool closure")
    return prior, manifest, original


def original_locator(original, guard, source, measured):
    native_sources = original.preserve_source(Path(original.PRIVATE_SOURCE) / "Native", source, measured, guard)
    old = Path(original.PRIVATE_EVAL)
    locator = old / "Native" / source["slot"] / "Candidates" / native_sources["original"].name
    guard(locator, old)
    return locator


def retained_pair(slot, locator, guard, pin):
    base = Path(BASE_PRIVATE)
    copies = []
    for kind in ("First", "Repeat"):
        path = base / slot / kind / locator.name
        guard(path, base)
        copies.append(checked(path, pin))
    require(copies[0] == copies[1], "protected parity outputs no longer contain the same pinned bytes")
    return copies[0]


def public_row(row):
    return {
        "slot": row["slot"], "expected_sha256": row["prior_native_sha256"], "generated_sha256": row["generated_sha256"],
        "repeat_sha256": row["repeat_sha256"], "bytes": row["generated_bytes"], "byte_equal": row["byte_equal"],
        "guarded_writer_processes": row["writer_processes"], "bridge_processes": row["bridge_processes"],
        "public_write_calls": 2 * row["writer_processes"], "strict_stream_reads": row["writer_processes"],
        "runtime_file_reads": row["runtime_file_reads"], "typed_replays_per_generation": row["typed_replays_per_generation"],
    }


def run_public(packet, pin):
    manifest = verified(packet, pin)
    require(packet.parent == Path(manifest["guest_root"]).resolve(strict=True), "unexpected public parity locator")
    base, base_manifest, supervisor = previous_packet(packet)
    references = base.parent / "Public" / "Result.json"
    expected = frozen_slots(checked(references, BASE_RESULT))
    require(expected == manifest["slots"], "public packet does not own both exact prior generated outputs")
    old, original, planned, guard, angle, epoch = supervisor.old_tools(base)
    old_public = old.parent / "Public" / "Result.json"
    measured_previous = pinned_result(checked(old_public, PRIOR_RESULT))
    require(measured_previous["source_lock_sha256"] == original.SOURCE_SHA == SOURCE_LOCK,
            "previous qualified evaluation belongs to a different locked source")
    home = Path(PRIVATE)
    guard(home, home)
    public = packet.parent / "Public"
    require(not home.exists() and not public.exists() and not public.is_symlink() and not public.is_junction(),
            "public parity needs unused local C drive and public receipt directories")
    home.mkdir(exist_ok=False)
    guard(home, home)
    public.mkdir(exist_ok=False)
    require(public.resolve(strict=True).parent == packet.parent, "receipt escapes its dedicated share root")
    source_share = packet.parent.parent / SOURCE_TRIAL
    cases, immutable, intent = [], False, None
    try:
        overlay = checked(packet / "Overlay.zip", manifest["files"]["Overlay.zip"])
        worker = install_overlay(base, base_manifest, overlay, manifest["overlay_members"], home)
        lock, intent = original.source_freeze(source_share)
        require(tuple(row["slot"] for row in intent["cases"]) == SLOTS, "private authored input slots changed")
        for source, measured in zip(intent["cases"], lock["slots"], strict=True):
            slot = source["slot"]
            case = home / slot
            case.mkdir(exist_ok=False)
            guard(case, home)
            try:
                locator = original_locator(original, guard, source, measured)
                authority = retained_pair(slot, locator, guard, expected[slot])
                model = planned(source, locator, epoch, angle)["original"]["modeled_input"]
                row = supervisor.compare_slot(worker, case, model, locator, authority, expected[slot]["sha256"], guard, home)
                cases.append(public_row(row))
            except Exception:
                exclusive(case / "Failure.log", format_exc().encode("utf-8"))
                cases.append({"slot": slot, "expected_sha256": expected[slot]["sha256"], "byte_equal": False,
                              "disposition": "generation-or-custody-refused"})
    except Exception:
        exclusive(home / "Failure.log", format_exc().encode("utf-8"))
    finally:
        try:
            require(intent is not None and verified(packet, pin) == manifest
                    and verified_packet(base, BASE_MANIFEST) == base_manifest
                    and frozen_slots(checked(references, BASE_RESULT)) == expected
                    and original.verified(old, PRIOR_FREEZE)["epoch"] == epoch
                    and pinned_result(checked(old_public, PRIOR_RESULT)) == measured_previous,
                    "prepared or previous custody packet changed")
            fresh_lock, fresh_intent = original.source_freeze(source_share)
            require(fresh_lock == lock and fresh_intent == intent, "protected source custody changed")
            for source, measured in zip(fresh_intent["cases"], fresh_lock["slots"], strict=True):
                locator = original_locator(original, guard, source, measured)
                retained_pair(source["slot"], locator, guard, expected[source["slot"]])
            supervisor.assert_python_only()
            immutable = True
        except Exception:
            exclusive(home / "IntegrityFailure.log", format_exc().encode("utf-8"))
    passed = immutable and tuple(row["slot"] for row in cases) == SLOTS and all(row["byte_equal"] for row in cases)
    report = {
        "schema": "kit.sw2026.public-oblique-pattern-parity-result.v1", "packet_sha256": pin,
        "sdk_revision": SDK_REVISION, "sdk_source_tree": SDK_TREE, "parity_result_sha256": BASE_RESULT,
        "source_lock_sha256": SOURCE_LOCK, "passed": passed, "cases": cases, "source_and_parity_immutable": immutable,
        "matching_cases": sum(row["byte_equal"] for row in cases) if immutable else 0,
        "native_processes_started": 0, "private_data_guest_only": True,
    }
    raw = encode(report)
    exclusive(public / "Result.json", raw)
    print(json.dumps({"passed": passed, "matching_cases": report["matching_cases"], "result_sha256": digest(raw)}), flush=True)
    return int(not passed)


def main():
    parser = ArgumentParser(description="Guarded guest-only public SDK parity for both frozen pattern outputs")
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "protected parity requires Windows Python 3.12")
    return run_public(Path(__file__).resolve().parents[1], args.pin)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"passed":false,"disposition":"transport-refused"}', flush=True)
        raise SystemExit(1) from None
