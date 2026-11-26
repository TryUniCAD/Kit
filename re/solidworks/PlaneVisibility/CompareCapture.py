from argparse import ArgumentParser
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from EncoderRoundTrip.Artifacts import read_record
from EncoderRoundTrip.Pipeline import SDK_INPUT_SUFFIXES
from OutputManifest import output_manifest
from TypedInventory import canonical, compare, digest, inspect
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def read(path):
    with path.open("rb") as source:
        raw = source.read(128 * 1024 * 1024 + 1)
    if len(raw) > 128 * 1024 * 1024:
        raise ValueError("comparison input exceeds 128 MiB")
    return raw


def asset(path, expected):
    raw = read(path)
    if digest(raw) != expected:
        raise ValueError("source archive differs from its expected SHA-256")
    archive = SldprtArchive.from_bytes(raw, "<plane-display-discovery>")
    version = ContainerMo(archive.streams)
    if archive.format_version != 4 or version != 19000:
        raise ValueError("comparison requires format 4 generation 19000")
    outcomes, full = inspect(archive, version)
    streams = {
        name: {"bytes": len(data), "sha256": digest(data)}
        for name, data in sorted(archive.streams.items())
    }
    return {
        "sha256": digest(raw),
        "bytes": len(raw),
        "typed": outcomes,
        "streams": streams,
    }, full


def write(output, name, value):
    raw = canonical(value) + b"\n"
    with (output / name).open("xb") as target:
        target.write(raw)
    return {"path": name, "sha256": digest(raw), "size_bytes": len(raw)}


def bound_sources(record):
    if record.get("schema") == "kit.sw2026.vendor-boss-plane-visibility.v1":
        author = record["phases"]["Author"]
        return {row["sha256"] for row in author.get("snapshots", {}).values()} | {
            author.get("source_sha256")
        }
    if "samples" in record:
        return {row["sha256"] for row in record["samples"].values()}
    raise ValueError("unsupported capture receipt binding")


def phase_custody(path, record, previous_path=None, previous=None):
    result = {}
    for role, row in record["phases"].items():
        if role not in {"ControlBefore", "Author", "NoOp", "Toggled", "ControlAfter"}:
            raise ValueError("unexpected plane capture phase")
        reused = row.get("reused_preflight_role")
        if reused is not None:
            if (
                previous is None
                or reused not in previous["phases"]
                or not all(
                    row.get(key) == value
                    for key, value in previous["phases"][reused].items()
                )
            ):
                raise ValueError("reused phase differs from its retained original")
            folder = previous_path.parent / reused
        else:
            folder = path.parent / role
        packet_raw, request_raw = read(folder / "Record.json"), read(
            folder / "Request.json"
        )
        if (
            digest(packet_raw) != row["record_sha256"]
            or digest(request_raw) != row["request_sha256"]
        ):
            raise ValueError("private phase record or request digest differs")
        packet, request = read_record(packet_raw), read_record(request_raw)
        if not all(row.get(key) == value for key, value in packet.items()):
            raise ValueError("terminal phase differs from its private original record")
        if (
            digest(read(Path(request["path"]))) != request["sha256"]
            or request["sha256"] != row["source_sha256"]
        ):
            raise ValueError("private phase source digest differs")
        for snapshot in packet.get("snapshots", {}).values():
            target = (folder / snapshot["archive"]).resolve()
            if not target.is_relative_to(folder.resolve()):
                raise ValueError("snapshot leaves its phase directory")
            payload = read(target)
            if (
                digest(payload) != snapshot["sha256"]
                or len(payload) != snapshot["bytes"]
            ):
                raise ValueError("private snapshot custody differs")
        identity, outcome = packet["oracle_identity"], packet["exit"]
        if outcome["exit_code"] != 0 or any(
            identity[key] != outcome[key] for key in ("pid", "started")
        ):
            raise ValueError("native lifetime has no matching normal exit")
        result[role] = {
            "record_sha256": digest(packet_raw),
            "request_sha256": digest(request_raw),
            "source_sha256": request["sha256"],
            "snapshots_checked": len(packet.get("snapshots", {})),
            "reused_preflight_role": reused,
            "exit_code": outcome["exit_code"],
        }
    return result


def run(args):
    before, first = asset(args.before, args.before_sha256)
    after, second = asset(args.after, args.after_sha256)
    changed = compare(first, second)
    streams = [
        {
            "name": name,
            "before": before["streams"].get(name),
            "after": after["streams"].get(name),
        }
        for name in sorted(set(before["streams"]) | set(after["streams"]))
        if before["streams"].get(name) != after["streams"].get(name)
    ]
    receipt = None
    if args.receipt is not None:
        raw = read(args.receipt)
        if digest(raw) != args.receipt_sha256:
            raise ValueError("capture receipt differs from its expected SHA-256")
        record = read_record(raw)
        bound = bound_sources(record)
        preflight = None
        if args.preflight_receipt is not None:
            previous_raw = read(args.preflight_receipt)
            if (
                digest(previous_raw) != args.preflight_sha256
                or record.get("original_preflight_sha256") != args.preflight_sha256
            ):
                raise ValueError(
                    "continuation does not bind the exact stopped preflight"
                )
            previous = read_record(previous_raw)
            if previous.get("schema") != record.get("schema"):
                raise ValueError("preflight and continuation schemas differ")
            if any(
                previous.get(key) != record.get(key)
                for key in ("plan_sha256", "executable_sha256")
            ):
                raise ValueError(
                    "preflight and continuation plan or executable differs"
                )
            bound.update(bound_sources(previous))
            prior_author = previous["phases"]["Author"]["oracle_identity"]
            next_author = record["phases"]["Author"]["oracle_identity"]
            preflight = {
                "sha256": digest(previous_raw),
                "bytes": len(previous_raw),
                "record_passed": previous.get("passed"),
                "controls_healthy": previous.get("controls_healthy"),
                "same_author_process": all(
                    prior_author.get(key) == next_author.get(key)
                    for key in ("pid", "started")
                ),
                "link_checked": True,
                "phase_custody": phase_custody(args.preflight_receipt, previous),
            }
        if any(value["sha256"] not in bound for value in (before, after)):
            raise ValueError("capture receipt does not bind both exact source hashes")
        if args.purpose == "controlled_toggle" and (
            record.get("passed") is not True
            or record.get("controls_healthy") is not True
        ):
            raise ValueError("controlled toggle receipt has no healthy measured result")
        receipt = {
            "sha256": digest(raw),
            "bytes": len(raw),
            "schema": record.get("schema"),
            "record_passed": record.get("passed"),
            "controls_healthy": record.get("controls_healthy"),
            "preflight": preflight,
            "phase_custody": (
                phase_custody(
                    args.receipt,
                    record,
                    args.preflight_receipt,
                    previous if preflight is not None else None,
                )
                if record.get("schema") == "kit.sw2026.vendor-boss-plane-visibility.v1"
                else None
            ),
            "scope": "hash custody only; no native acceptance inferred",
        }
    elif args.purpose == "controlled_toggle":
        raise ValueError(
            "controlled toggle comparison requires its exact capture receipt"
        )
    source_digests = {
        path.relative_to(ROOT).as_posix(): digest(path.read_bytes())
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and path.suffix in SDK_INPUT_SUFFIXES
    }
    sdk = {
        "source_files": len(source_digests),
        "sources_sha256": digest(canonical(source_digests)),
        "git_source_tree": subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD:src"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip(),
    }
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT / "src"):
        raise ValueError("use a fresh research output directory outside src")
    output.mkdir(parents=True, exist_ok=False)
    artifacts = {
        "before_inventory": write(output, "BeforeInventory.json", first),
        "after_inventory": write(output, "AfterInventory.json", second),
        "typed_comparison": write(output, "TypedComparison.json", changed),
    }
    output_manifest(artifacts)
    report = {
        "schema": "kit.sw2026.plane-display-comparison.v1",
        "purpose": args.purpose,
        "before": before,
        "after": after,
        "receipt": receipt,
        "changed_streams": streams,
        "typed_changes": {
            name: {
                "row_count": len(value.get("rows", [])),
                "map_equal": (
                    value["map_before"] == value["map_after"]
                    if "map_before" in value and "map_after" in value
                    else None
                ),
            }
            for name, value in changed.items()
        },
        "artifacts": artifacts,
        "sdk": sdk,
        "python": sys.version.split()[0],
        "method_sha256": {
            path.name: digest(path.read_bytes())
            for path in (Path(__file__), Path(__file__).with_name("TypedInventory.py"))
        },
        "confidence": "not_found",
        "field_hypothesis": None,
        "comparison_policy": "exact typed paths and map ownership; no field masking, identity remapping or semantic inference",
        "models_used": False,
        "vendor_loadable": False,
        "application_usable": False,
    }
    if (
        digest(read(args.before)) != args.before_sha256
        or digest(read(args.after)) != args.after_sha256
    ):
        raise ValueError("source changed during offline comparison")
    artifact = write(output, "Comparison.json", report)
    return {
        "report": artifact,
        "typed_changes": report["typed_changes"],
        "changed_streams": len(streams),
        "confidence": "not_found",
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Compare exact native plane-display discovery archives without running CAD"
    )
    for role in ("before", "after"):
        parser.add_argument("--" + role, type=Path, required=True)
        parser.add_argument("--" + role + "-sha256", required=True)
    parser.add_argument(
        "--purpose", choices=("diagnostic", "noise", "controlled_toggle"), required=True
    )
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--receipt-sha256")
    parser.add_argument("--preflight-receipt", type=Path)
    parser.add_argument("--preflight-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.receipt) != bool(args.receipt_sha256):
        raise ValueError("receipt requires both path and digest")
    if bool(args.preflight_receipt) != bool(args.preflight_sha256) or (
        args.preflight_receipt is not None and args.receipt is None
    ):
        raise ValueError("preflight requires its digest and a continuation receipt")
    sys.stdout.buffer.write(canonical(run(args)) + b"\n")
