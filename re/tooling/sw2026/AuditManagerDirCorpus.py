from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import re

from AuditKeywordCorpus import digest, git, pinned_documents, require
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def code_identity(revision):
    require(re.fullmatch(r"[0-9a-f]{40}", revision), "use an exact codec revision")
    require(not git("diff", "--name-only", revision, "--", "src"), "codec differs from its pin")
    require(not git("ls-files", "--others", "--exclude-standard", "--", "src"), "untracked codec file")
    return git("rev-parse", f"{revision}:src").decode().strip()


def measure(path, raw):
    row = {"source_sha256": digest(raw), "source_format": path.rsplit(".", 1)[-1].lower()}
    try:
        archive = SldprtArchive.from_bytes(raw)
        payload = archive.require("Contents/CMgrHdr2")
        require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
                "the pinned current-format profile is required")
        graph = ReadMgrHeader(payload, 19000)
        rebuilt, written = WriteMgrHeader(graph.RootValue, 19000)
        rows = tuple(value["o"] for value in graph.RootValue.FieldsValue["f08"]["items"])
        require(rebuilt == payload and graph.MapValue == written.MapValue,
                "the manager directory bytes or map changed")
    except (KeyError, TypeError, ValueError) as error:
        return row | {"passed": False, "refusal": str(error)}
    return row | {
        "passed": True,
        "directory_sha256": digest(payload),
        "directory_bytes": len(payload),
        "root_slot": graph.RootValue.IndexValue,
        "map_next": graph.MapValue.CounterValue,
        "row_slots": [node.IndexValue for node in rows],
        "rows": len(rows),
        "distinct_child_objects": len(set(rows)),
    }


def audit(source_revision, codec_revision):
    source_tree = code_identity(codec_revision)
    cases = {path: measure(path, raw) for path, raw in pinned_documents(source_revision)}
    require(source_tree == code_identity(codec_revision), "codec changed during the inventory")
    accepted = [row for row in cases.values() if row["passed"]]
    return {
        "schema": "kit.sw2026.typed-manager-directory-corpus.v1",
        "tool_sha256": digest(Path(__file__).read_bytes()),
        "source_revision": source_revision,
        "codec_revision": codec_revision,
        "source_tree": source_tree,
        "source_files": len(cases),
        "exact_typed_directories": len(accepted),
        "accepted_source_formats": dict(Counter(row["source_format"] for row in accepted)),
        "row_counts": dict(Counter(row["rows"] for row in accepted)),
        "native_processes": 0,
        "generated_documents": 0,
        "heldout_inputs_read": 0,
        "cases": cases,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("source_revision")
    parser.add_argument("codec_revision")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    evidence = audit(args.source_revision, args.codec_revision)
    payload = (json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as handle:
        handle.write(payload)
    keys = ("source_files", "exact_typed_directories", "accepted_source_formats", "row_counts")
    print(json.dumps({key: evidence[key] for key in keys} | {"sha256": digest(payload)}))


if __name__ == "__main__":
    main()
