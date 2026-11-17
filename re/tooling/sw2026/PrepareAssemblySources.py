from __future__ import annotations

import argparse
import re
from pathlib import Path

from PrepareCurveCorpus import MAX_DECODED, MAX_FILE, MAX_STREAM, Privacy, binary_redaction, checked_path, container_api, digest, json_bytes, read_bytes, read_json, xml_redaction
from PrepareSavedCircles import private_summary, require

DISCOVERY = ("A07EmptyAssembly", "A08SingleAssembly", "A09RepeatedAssembly")
XML_MIRRORS = ("swXmlContents/Features", "swXmlContents/Components", "swXmlContents/COMPINSTANCETREE")
NOTICE = "Prepared native assembly discovery fixtures from an ineligible source batch. Reader inputs only, zero generated writer outputs and zero held-out acceptance."


class AssemblyPrivacy(Privacy):
    def __init__(self, names, research_folder):
        super().__init__(names, ())
        marker = re.escape(research_folder)
        self.home = re.compile(self.home.pattern + r"|[A-Za-z]:[\\/]Documents[\\/]UniCAD[\\/]" + marker + r"[\\/]", re.IGNORECASE)


def prepare_archive(api, raw, name, privacy):
    source = api.SldprtArchive.FromBytes(raw, name, SizeLimit=MAX_DECODED)
    require({key.split("/", 1)[0] for key in source.streams if key.startswith("_MO_VERSION_")} == {"_MO_VERSION_19000"}, "unexpected assembly format")
    chosen, streams, operations, previews = [], [], [], []
    total = 0
    for item in source.records:
        require(not privacy.private(item.name), "private assembly stream name")
        total += len(item.data)
        require(len(item.data) <= MAX_STREAM and total <= MAX_DECODED, "assembly fixture exceeds its stream bound")
        if item.name.endswith(".xml") or item.name in XML_MIRRORS:
            prepared, changes, framed = xml_redaction(
                item.name, item.data, privacy,
                additional_metadata_properties=(("docProps/ISolidWorksInformation.xml", "SW-Folder Name"),),
                additional_metadata_attributes=tuple((stream, "http://www.solidworks.com/sw2003/schema}swFile", "swPath") for stream in XML_MIRRORS),
            )
        else:
            prepared, changes = binary_redaction(item.name, item.data, privacy, additional_metadata_streams=("Contents/CMgr", "Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "SwDocContentMgr/SwDocContentMgrInfo"))
            framed = []
        require(len(prepared) == len(item.data), "assembly metadata transformation changed field width")
        if privacy.scan(prepared, framed):
            raise ValueError(f"unclassified private context: {name}/{item.name}; {private_summary(prepared, privacy)}")
        covered = {offset for row in changes for offset in range(row["offset"], row["offset"] + row["bytes"])}
        require(all(before == after or offset in covered for offset, (before, after) in enumerate(zip(item.data, prepared, strict=True))), "unrecorded assembly mutation")
        chosen.append((item.name, prepared))
        streams.append({"name": item.name, "bytes": len(prepared), "source_sha256": digest(item.data), "sha256": digest(prepared), "privacy_operations": len(changes)})
        operations.extend({"stream": item.name, **row} for row in changes)
        if item.name == "PreviewPNG":
            require(prepared.startswith(b"\x89PNG\r\n\x1a\n"), "unexpected assembly preview encoding")
            previews.append((name + ".png", prepared))
    result = api.BuildSldprt(chosen, Template=raw)
    require(len(result) <= MAX_FILE, "prepared assembly exceeds the fixture size limit")
    return result, streams, operations, previews


def main():
    parser = argparse.ArgumentParser(description="Prepare only three hash-bound native assembly discovery sources without executing archive schemas")
    parser.add_argument("source", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--redact-name", action="append", required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    destination = args.destination.absolute()
    require(source == args.source.absolute() and source.is_dir(), "assembly source directory is not canonical")
    require(destination.parent.resolve(strict=True) == destination.parent and not destination.exists() and not destination.is_symlink(), "assembly destination must be unused beneath a canonical parent")
    receipt, receipt_sha = read_json(args.receipt)
    require(receipt["schema"] == "kit.sw2026.ordinary-assembly-source-attempt.v1" and receipt["eligible_for_heldout"] is False and receipt["controls_healthy"], "unexpected assembly source receipt")
    rows = {row["name"]: row for row in receipt["cases"] if row["split"] == "discovery"}
    require(tuple(rows) == DISCOVERY and all(not row["passed"] and row["native_sha256"] for row in rows.values()), "assembly discovery membership differs")
    warnings = {row["name"]: row["open_warnings"] for row in receipt["discovery_diagnostics"]}
    require(warnings == dict(zip(DISCOVERY, (0, 32, 32), strict=True)), "assembly discovery diagnostics differ")
    privacy = AssemblyPrivacy(args.redact_name, source.parent.name)
    api, modules = container_api(Path(__file__).resolve().parents[3])
    records, logs, files, previews = [], [], [], []
    for name, row in rows.items():
        filename = name + ".SLDASM"
        path = checked_path(source, f"{name}/author/{filename}")
        raw = read_bytes(path)
        require(len(raw) == row["native_bytes"] and digest(raw) == row["native_sha256"], "native assembly discovery fingerprint differs")
        prepared, streams, operations, pictures = prepare_archive(api, raw, filename, privacy)
        require(read_bytes(path) == raw, "native discovery source changed during preparation")
        sha = digest(prepared)
        records.append({"name": name, "file": filename, "split": "discovery", "source_sha256": digest(raw), "sha256": sha, "bytes": len(prepared), "source_reopen_warnings": warnings[name], "streams": streams})
        logs.append({"file": filename, "prepared_sha256": sha, "operations": operations})
        files.append((filename, prepared))
        previews.extend(pictures)
    ledger_raw = json_bytes({"schema": "kit.sw2026.assembly-discovery-privacy.v1", "redacted_account_fingerprints": privacy.name_fingerprints, "records": logs})
    info = {"schema": "kit.sw2026.assembly-discovery-fixtures.v1", "notice": NOTICE, "source_receipt_sha256": receipt_sha, "privacy_ledger_sha256": digest(ledger_raw), "reader_fixture_count": len(records), "is_writer_output": False, "native_acceptance": False, "heldout_payloads_read": False, "records": records}
    manifest_raw = json_bytes(info)
    proof = {"schema": "kit.sw2026.assembly-discovery-preparation.v1", "source_receipt_sha256": receipt_sha, "manifest_sha256": digest(manifest_raw), "privacy_ledger_sha256": digest(ledger_raw), "preparer_sha256": digest(Path(__file__).read_bytes()), "modules": modules, "archive_schemas_executed": False, "container_outputs_reparsed": False, "heldout_payloads_read": False, "files": len(files), "streams": sum(len(row["streams"]) for row in records), "redactions": sum(len(row["operations"]) for row in logs), "previews": len(previews)}
    for value in (info, proof, {"records": logs}):
        require(not privacy.private_json(value), "assembly preparation retained a private context")
    destination.mkdir()
    for filename, data in [*files, ("Manifest.json", manifest_raw), ("PrivacyLedger.json", ledger_raw), ("SourceEvidence.json", json_bytes(proof))]:
        with (destination / filename).open("xb") as out:
            out.write(data)
    if previews:
        folder = destination / "Previews"
        folder.mkdir()
        for filename, data in previews:
            require((folder / filename).parent == folder, "assembly preview path escaped its directory")
            with (folder / filename).open("xb") as out:
                out.write(data)
    print(json_bytes({key: proof[key] for key in ("files", "streams", "redactions", "previews", "manifest_sha256")}).decode("ascii"), end="")


if __name__ == "__main__":
    main()
