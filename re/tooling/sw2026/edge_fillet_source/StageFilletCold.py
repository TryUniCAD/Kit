from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import sys

from FilletColdPacket import (
    ARMS, CASE, GUEST_ROOT, NEW_FILES, PARTITION, PRIOR_FILES, REGISTERED_API,
    SOURCE, SOURCE_HASH, SOURCE_JOB, SOURCE_LOCK, SOURCE_PHASE, TOOL_FILES,
    checked, read_job, sha, write_new,
)
from FilletModel import require
from FilletPacket import BUILD, ORACLE, inspect_packet, job_bytes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields


def expected_state(capture):
    lock = json.loads(checked(capture / "SourceLock.json", SOURCE_LOCK))
    require(lock["passed"] is True and lock["job_sha256"] == SOURCE_JOB
            and lock["oracle_build"] == BUILD and lock["oracle_sha256"] == ORACLE
            and lock["registered_api_sha256"] == REGISTERED_API
            and lock["controls"]["before"]["passed"] is True and lock["controls"]["after"]["passed"] is True,
            "disclosed native source lock is incomplete")
    case, = (row for row in lock["sources"] if row["case"] == CASE)
    require(case["passed"] is True and case["original_sha256"] == SOURCE_HASH
            and case["phases"][1]["receipt_sha256"] == SOURCE_PHASE,
            "disclosed axial life cycle does not bind the original and reopen")
    result = json.loads(checked(capture / CASE / "reopen-edit-save" / "Record.json", SOURCE_PHASE))
    require(result["passed"] is True and result["source_immutable"] is True, "the exact native reopen did not pass")
    return job_bytes({name: {"tree": result[name]["tree"],
                             "driver_owners": result[name]["driver"]["name"].split("@")[:2],
                             "definition_type": result[name]["definition"]["type"],
                             "stock_parents": result[name]["definition"]["parents"]}
                      for name in ("reopened", "edited")})


def repack_arms(raw):
    source = SldprtArchive.from_bytes(raw)
    fields = TemplateFields(raw, source)
    signatures, type_ids = fields
    expected = source.streams
    require(source.format_version == 4 and len(expected) == 40 and expected[PARTITION],
            "the exact native source stream inventory differs")

    decoded = {}
    arms = {}
    for arm in ARMS:
        streams = dict(expected)
        if arm == "OmitPartition":
            del streams[PARTITION]
        result = EmitSldprt(list(streams.items()), source.file_id, source.format_version, signatures, type_ids)
        artifact = SldprtArchive.from_bytes(result)
        require(tuple(artifact.streams.items()) == tuple(streams.items())
                and (artifact.file_id, artifact.format_version) == (source.file_id, source.format_version)
                and TemplateFields(result, artifact) == (signatures, {name: type_ids[name] for name in streams}),
                "repacked diagnostic changed an unrelated stream or container type")
        arms[f"{arm}.SLDPRT"] = result
        decoded[arm] = len(streams)
    return arms, {"format_version": source.format_version, "file_id": source.file_id,
                  "stream_counts": decoded,
                  "retained_streams_sha256": sha(job_bytes([[name, sha(data)] for name, data in expected.items()
                                                            if name != PARTITION])),
                  "omitted_stream_sha256": sha(expected[PARTITION]),
                  "omitted_stream_bytes": len(expected[PARTITION])}


def git(*arguments):
    return subprocess.check_output(("git", "-C", str(ROOT), *arguments))


def prepare(source_root, output, revision):
    source_root = source_root.resolve(strict=True)
    output = output.resolve()
    require(not source_root.is_relative_to(ROOT) and not output.is_relative_to(ROOT)
            and not output.is_relative_to(source_root) and not output.exists(),
            "diagnostic packet must use a fresh external research path")
    require(git("rev-parse", revision + "^{commit}").decode().strip() == revision,
            "freeze requires an exact full committed revision")
    for relative in (*TOOL_FILES, "StageFilletCold.py"):
        path = HERE / Path(relative).name
        require(git("show", revision + ":" + path.relative_to(ROOT).as_posix()) == path.read_bytes(),
                f"cold tooling diverges from committed revision: {path.name}")

    packet = source_root / "Packet"
    original = source_root / "Capture" / CASE / f"{CASE}.SLDPRT"
    prior = inspect_packet(packet / "SourceJob.json", SOURCE_JOB)
    require(prior["cohort"] == "disclosed", "only the original disclosed packet is eligible")
    data = {name: checked(packet / name, prior["files"][name]["sha256"]) for name in PRIOR_FILES}
    data.update({name: (HERE / Path(name).name).read_bytes() for name in TOOL_FILES})
    data["Expected.json"] = expected_state(source_root / "Capture")
    arms, comparison = repack_arms(checked(original, SOURCE_HASH))
    data.update(arms)
    require(set(data) == PRIOR_FILES | NEW_FILES, "diagnostic output packet inventory differs")

    output.mkdir(parents=True, exist_ok=False)
    (output / "Tool").mkdir()
    for name, contents in data.items():
        write_new(output / name, contents)
    job = {"schema": "kit.sw2026.edge-fillet-cold-diagnostic.v1",
           "scope": "disclosed native-source diagnostic only",
           "tool_revision": revision, "tool_tree": git("rev-parse", revision + "^{tree}").decode().strip(),
           "oracle": {"build": BUILD, "sha256": ORACLE, "registered_api_sha256": REGISTERED_API},
           "source": {"file_sha256": SOURCE_HASH, "job_sha256": SOURCE_JOB, "lock_sha256": SOURCE_LOCK,
                      "phase_sha256": SOURCE_PHASE, "guest_path": SOURCE},
           "guest_packet": str(GUEST_ROOT / "Packet"), "guest_run": str(GUEST_ROOT / "Run01"),
           "mutation": {"action": "omit_one_logical_stream", "stream": PARTITION},
           "comparison": comparison, "writer_output_count": 0,
           "files": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in data.items()}}
    pin = sha(job_bytes(job))
    write_new(output / "ColdJob.json", job_bytes(job))
    read_job(output / "ColdJob.json", pin)
    checked(original, SOURCE_HASH)
    return job | {"cold_job_sha256": pin, "native_processes_started": 0}


def main():
    parser = ArgumentParser(description="stage an external two-arm fillet partition experiment without CAD")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.receipt is not None:
        require(not args.receipt.resolve().is_relative_to(ROOT) and not args.receipt.exists(),
                "receipt must use a fresh external path")
    result = prepare(args.source_root, args.output, args.revision)
    if args.receipt is not None:
        write_new(args.receipt, job_bytes(result))
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
