from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import re
import sys

from AuditKeywordCorpus import ROOT, SCOPE, digest, git, pinned_documents, require

sys.path.insert(0, str(Path(__file__).resolve().parent / "serial"))

from RoundTrip import PLANS, REQUIRED, expand, registry, stream_roundtrip, usage_summary
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Container.Container import SldprtArchive


CODE_SCOPES = (
    "src",
    "re/tooling/sw2026/serial",
    "re/tooling/sw2026/AuditKeywordCorpus.py",
)
RELEASE = 19000


def codec_identity(revision):
    require(re.fullmatch(r"[a-f0-9]{40}", revision), "supply an exact codec revision")
    require(not git("diff", "--name-only", revision, "--", *CODE_SCOPES), "codec sources differ from the selected revision")
    require(not git("ls-files", "--others", "--exclude-standard", "--", *CODE_SCOPES), "untracked files in the codec scopes")
    return {path: git("rev-parse", f"{revision}:{path}").decode().strip() for path in CODE_SCOPES}


def compact_stream(record):
    summary = usage_summary([record])
    provisional = sorted({name for row in summary.values() for name in row["provisional_schemas"]})
    missing = sorted({name for row in summary.values() for name in row["missing_schemas"]})
    raw = sum(row["raw_operation_count"] for row in summary.values())
    exact = record["byte_identity_passed"]
    typed = exact and raw == 0
    output = {
        "bytes": record.get("bytes"),
        "sha256": record.get("sha256"),
        "exact_without_tail": exact,
        "exact_without_raw": typed,
        "proven_typed_exact": typed and record["proven_schemas"],
        "raw_operations": raw,
        "provisional_schemas": provisional,
        "missing_schemas": missing,
    }
    for name in ("map_base", "map_count", "seeded_map_count", "tail", "first_diff"):
        if name in record:
            output[name] = record[name]
    if "error" in record:
        output["error_class"] = record["error"].partition("(")[0]
        output["failure_kind"] = "missing_schema" if missing else "serializer_error"
        detail = record.get("details")
        if isinstance(detail, dict):
            output["error_boundary"] = {key: detail[key] for key in ("class", "field", "offset", "phase")
                                        if key in detail and type(detail[key]) in {int, str}}
    return output


def sdk_stream(data, emit):
    result = {"bytes": len(data), "sha256": digest(data), "raw_operations": 0}
    try:
        rebuilt, seed, reports = emit()
        exact = rebuilt == data and all(report["completed"] for report in reports)
        raw_fields = sum(len(report["native_byte_fields"]) for report in reports)
        provisional = sorted({name for report in reports for name in report["provisional_schemas"]})
        missing = sorted({name for report in reports for name in report["missing_schemas"]})
        result.update(exact_without_tail=exact, exact_without_raw=exact and raw_fields == 0,
                      proven_typed_exact=exact and raw_fields == 0 and not provisional and not missing,
                      raw_operations=raw_fields, provisional_schemas=provisional, missing_schemas=missing, **seed)
    except (ValueError, KeyError, TypeError) as failure:
        result.update(exact_without_tail=False, exact_without_raw=False, proven_typed_exact=False,
                      missing_schemas=[], provisional_schemas=[],
                      error_class=type(failure).__name__, failure_kind="sdk_serializer_error",
                      error_boundary=str(failure))
    return result


def sdk_definition(data):
    decoded = ReadModelDef(data, RELEASE)
    encoded = WriteModelDef(decoded.GraphValue)
    require(decoded.MapValue.CounterValue == encoded.MapValue.CounterValue, "Definition map changed")
    return encoded.OutputValue, {"map_count": encoded.MapValue.CounterValue}, (
        GetBodyReport(decoded.UsageValue), GetBodyReport(encoded.UsageValue),
    )


def sdk_mates(archive, name, configuration):
    link = ReadNativeLink(archive, configuration)
    data_config, config = WriteConfigMut(link.ConfigValue.RootValue, RELEASE, link.ConfigValue.HeaderValue)
    data_resolved, resolved = WriteResolMut(
        link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
        RELEASE, config.MapValue, link.ResolvedValue.ContextValue,
    )
    stem = f"Contents/Config-{configuration}"
    require(data_config == archive.require(stem) and data_resolved == archive.require(stem + "-ResolvedFeatures"),
            "mate handoff prerequisites did not reproduce their original bytes")
    decoded = ReadMatesMut(archive.require(name), link.ResolvedValue)
    output, encoded = WriteMatesMut(decoded.RootsValue, resolved)
    return output, {"seeded_map_count": resolved.MapValue.CounterValue,
                    "map_count": encoded.MapValue.CounterValue}, (decoded.ReportValue, encoded.ReportValue)


def measure(path, raw, reg, plans):
    require(path.startswith(SCOPE + "corpus/"), "audit permits only disclosed corpus files")
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == RELEASE, "native archive build profile differs")
    optional = (name for name in plans if name not in REQUIRED and name in archive.streams)
    selected = expand(archive, (*REQUIRED, *optional))
    rows = {}
    for name in selected:
        research = stream_roundtrip(archive, name, reg, plans, linked=True)
        rows[name] = compact_stream(research)
        if name == "Contents/Definition":
            data = archive.require(name)
            rows[name] = sdk_stream(data, lambda: sdk_definition(data))
            slots = Counter()
            for direction in ("load", "store"):
                for raw_field in research["schema_usage"][direction]["raw_operations"]:
                    slots[(raw_field["field"], raw_field["observed_length"])] += 1
            rows[name]["research_reference"] = {
                "exact": research["byte_identity_passed"],
                "raw_fields": [{"field": field, "bytes": size, "operations": count}
                               for (field, size), count in sorted(slots.items())],
            }
    if path.casefold().endswith(".sldasm"):
        for name in archive.streams:
            match = re.fullmatch(r"Contents/Config-([0-9]+)-MatesList", name)
            if match is not None:
                configuration = int(match[1])
                rows[name] = sdk_stream(archive.require(name), lambda: sdk_mates(archive, name, configuration))
    return {"sha256": digest(raw), "format_version": 4, "archive_version": RELEASE, "streams": rows}


def audit(source_revision, codec_revision):
    require(re.fullmatch(r"[a-f0-9]{40}", source_revision), "supply an exact disclosed source revision")
    identity = codec_identity(codec_revision)
    reg = registry()
    plans = {**PLANS, **reg.plans}
    cases = {path: measure(path, raw, reg, plans) for path, raw in pinned_documents(source_revision)}
    require(codec_identity(codec_revision) == identity, "codec sources changed during the audit")
    flags = ("exact_without_tail", "exact_without_raw", "proven_typed_exact")
    counts_by_stream = {}
    missing_schemas = Counter()
    provisional_schemas = Counter()
    for case in cases.values():
        for name, row in case["streams"].items():
            group = re.sub(r"Config-[0-9]+", "Config-#", name)
            counts = counts_by_stream.setdefault(group, Counter())
            counts.update({"attempts": 1, **{flag: int(row[flag]) for flag in flags}})
            counts.update({"unavailable": int(row["bytes"] is None), "raw_operations": row["raw_operations"]})
            missing_schemas.update(row["missing_schemas"])
            provisional_schemas.update(row["provisional_schemas"])
    totals = {key: sum(counts[key] for counts in counts_by_stream.values()) for key in ("attempts", *flags)}
    complete_files = {flag: sum(all(row[flag] for row in case["streams"].values()) for case in cases.values())
                      for flag in flags}
    return {
        "schema": "kit.sw2026.binary-archive-corpus-audit.v1",
        "script_sha256": digest(Path(__file__).read_bytes()),
        "source_revision": source_revision,
        "codec_revision": codec_revision,
        "codec_git_objects": identity,
        "python": sys.version.split()[0],
        "source_files": len(cases),
        "parts": sum(path.casefold().endswith(".sldprt") for path in cases),
        "assemblies": sum(path.casefold().endswith(".sldasm") for path in cases),
        "stream_counts": totals,
        "complete_files": complete_files,
        "counts_by_stream": counts_by_stream,
        "missing_schema_incidence": dict(missing_schemas),
        "provisional_schema_incidence": dict(provisional_schemas),
        "heldout_inputs_read": 0,
        "native_processes_started": 0,
        "native_writer_outputs": 0,
        "cases": cases,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Census of 2026 typed binary archive re-emission on disclosed tracked files")
    parser.add_argument("source_revision")
    parser.add_argument("codec_revision")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.source_revision, args.codec_revision)
    payload = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as target:
        target.write(payload)
    selected = ("source_files", "stream_counts", "complete_files")
    print(json.dumps({key: result[key] for key in selected} | {"receipt_sha256": digest(payload)}))
