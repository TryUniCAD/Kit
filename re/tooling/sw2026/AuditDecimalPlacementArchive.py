from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json
import re

from AuditArchiveCorpus import PLANS, RELEASE, codec_identity, measure_archive, registry
from AuditKeywordCorpus import digest, git, inspect as inspect_keywords, require
from MeasurePrismPartitions import measure_prism_partitions
from convert.adapters.solidworks.Container.Container import SldprtArchive


CAMPAIGN = "re/NativePlacement2026"
SOURCE_REVISION = "881d05f3e3fc432f939081acd321ae3eed50eb01"
SOURCE_MANIFEST = "0d71fa6c532819d54993cd4462a55195e13371b402ab423c1f7da012bee355ff"
KEYWORDS = "swXmlContents/KeyWords"
ROLES = ("control-after", "control-before", "variation")
PARTITION_SCOPES = (
    "re/tooling/sw2026/para",
    "re/tooling/sw2026/builders/EmptyPartition.py",
)


def collect(manifest):
    sources = {}
    for entry in manifest["cases"]:
        case = entry["case"]
        if case["application"] != "solidworks" or entry["native_status"] != "completed":
            continue
        case_id = case["id"]
        require(re.fullmatch(r"solidworks-[0-9]{3}", case_id), "invalid disclosed case identifier")
        require(case["plane"] in {"front", "top", "right"} and type(case["reverse"]) is bool,
                "invalid disclosed feature frame")
        rows = {row["native_path"]: row for row in entry["files"]}
        require(len(rows) == len(entry["files"]) == len(ROLES), "unexpected bracket roster")
        for role in ROLES:
            path = f"Cases/{case_id}/{role}.SLDPRT"
            record = rows[path]
            require(path not in sources and record["native_batch_qualified"], "unqualified bracket input")
            require(re.fullmatch(r"[0-9a-f]{64}", record["source_sha256"]), "invalid source digest")
            sources[path] = (record["source_sha256"], case["plane"], case["reverse"])
    require(len(sources) == 69 and len({row[0] for row in sources.values()}) == 69,
            "disclosed source roster must contain 69 distinct files")
    return sources


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def partition_identity(revision):
    require(not git("diff", "--name-only", revision, "--", *PARTITION_SCOPES),
            "partition research codec differs from the selected revision")
    require(not git("ls-files", "--others", "--exclude-standard", "--", *PARTITION_SCOPES),
            "partition research codec includes untracked files")
    return {path: git("rev-parse", f"{revision}:{path}").decode().strip() for path in PARTITION_SCOPES}


def audit(codec_revision):
    identity = codec_identity(codec_revision) | partition_identity(codec_revision)
    manifest = git("show", f"{SOURCE_REVISION}:{CAMPAIGN}/Manifest.json")
    require(digest(manifest) == SOURCE_MANIFEST, "published manifest changed")
    sources = collect(json.loads(manifest))
    schemas = registry()
    plans = {**PLANS, **schemas.plans}
    stream_counts = {}
    frames = Counter()
    cases = {}
    for path, (sha256, plane, reverse) in sorted(sources.items()):
        raw = git("show", f"{SOURCE_REVISION}:{CAMPAIGN}/{path}")
        require(digest(raw) == sha256, "published native file changed: " + path)
        result = measure_archive(raw, schemas, plans, assembly=False)
        rows = result["streams"]
        for name, row in rows.items():
            require(row["bytes"] is not None and row["proven_typed_exact"],
                    f"{path}: {name}: {row}")
            stream_counts[name] = stream_counts.get(name, 0) + 1
        keywords = inspect_keywords(raw)
        require(keywords["ordinary_framing"] and
                (keywords["compact_typed_reassembly"] or keywords["spaced_typed_reassembly"]),
                "KeyWords do not replay exactly: " + path)
        stream_counts[KEYWORDS] = stream_counts.get(KEYWORDS, 0) + 1
        partitions = measure_prism_partitions(SldprtArchive.from_bytes(raw))
        for name in partitions:
            stream_counts[name] = stream_counts.get(name, 0) + 1
        frames[plane + ("_reverse" if reverse else "_forward")] += 1
        cases[path] = {
            "source_sha256": sha256, "binary_stream_report_sha256": digest(encode(rows)),
            "keyword_sha256": keywords["keyword_sha256"], "linked_partitions": partitions,
        }
    require((codec_identity(codec_revision) | partition_identity(codec_revision)) == identity,
            "codec changed during archive measurement")
    require(len(stream_counts) == 18 and set(stream_counts.values()) == {len(cases)},
            "selected stream proof is incomplete")
    return {
        "schema": "kit.sw2026.decimal-placement-archive-replay.v1",
        "codec_revision": codec_revision, "codec_git_objects": identity,
        "script_sha256": digest(Path(__file__).read_bytes()),
        "partition_measure_sha256": digest(Path(__file__).with_name("MeasurePrismPartitions.py").read_bytes()),
        "source_revision": SOURCE_REVISION, "source_manifest_sha256": SOURCE_MANIFEST,
        "qualified_source_files": len(cases), "archive_model_version": RELEASE,
        "exact_binary_replays": sum(count for name, count in stream_counts.items() if name != KEYWORDS),
        "exact_keyword_replays": stream_counts[KEYWORDS], "frames": frames, "selected_streams": stream_counts,
        "exact_vendor_build_attested": False, "native_launches": 0, "native_writer_outputs": 0,
        "heldout_credit": 0, "fcstd_credit": 0, "cases": cases,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("codec_revision")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit(args.codec_revision)
    raw = encode(report)
    with args.output.open("xb") as result:
        result.write(raw)
    print(json.dumps({key: report[key] for key in ("qualified_source_files", "exact_binary_replays",
                                                   "exact_keyword_replays")}
                     | {"receipt_sha256": digest(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
