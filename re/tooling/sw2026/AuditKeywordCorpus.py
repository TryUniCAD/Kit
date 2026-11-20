from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src")]

from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseXml


OWNER = "swXmlContents/KeyWords"
PREFIX = b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n'
SCOPE = "re/solidworks/v2026/"
OPERATORS = (
    "src/convert/adapters/solidworks/Archive/Construction/Metadata/FrameKeywords.py",
    "src/convert/adapters/solidworks/Container/Archive.py",
    "src/convert/adapters/solidworks/Container/Container.py",
    "src/convert/adapters/solidworks/Core/Native.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def git(*args, data=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=data, capture_output=True, check=True).stdout


def pinned_documents(revision):
    entries = []
    for line in git("ls-tree", "-rz", revision, "--", SCOPE).rstrip(b"\0").split(b"\0"):
        descriptor, name = line.split(b"\t", 1)
        mode, kind, identifier = descriptor.split()
        path = name.decode("utf-8")
        if Path(path).suffix.casefold() not in {".sldprt", ".sldasm"}:
            continue
        require(mode == b"100644" and kind == b"blob", "CAD evidence must be a tracked regular file")
        entries.append((path, identifier))
    require(entries, "no tracked part or assembly evidence")
    content = git("cat-file", "--batch", data=b"".join(identifier + b"\n" for _, identifier in entries))
    with BytesIO(content) as stream:
        for path, identifier in entries:
            actual, kind, size = stream.readline().split()
            require((actual, kind) == (identifier, b"blob"), "unexpected Git object framing")
            raw = stream.read(int(size))
            require(len(raw) == int(size) and stream.read(1) == b"\n", "incomplete Git blob")
            yield path, raw
        require(not stream.read(), "unexpected Git object tail")


def inspect(raw):
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
            "the tracked source is outside the stated 2026 container profile")
    keywords = archive.require(OWNER)
    root = ParseXml(keywords)
    require(root.tag == "Keywords", "unexpected keyword root")
    children = []
    for node in root.iter():
        value = node.get("DissectableChildren")
        if value is None:
            continue
        pieces = value.split(",")
        children.append(len(pieces) if all(re.fullmatch(r"[0-9]+", item) for item in pieces) else "unqualified_text")
    return {
        "container_sha256": digest(raw), "container_version": archive.format_version,
        "model_version": 19000, "file_id": archive.file_id, "keyword_bytes": len(keywords),
        "keyword_sha256": digest(keywords),
        "ordinary_framing": keywords.startswith(PREFIX) and keywords.endswith(b"\r\n") and keywords.count(b"\n") == keywords.count(b"\r\n") == 2,
        "compact_typed_reassembly": FrameKeywords(root, True) == keywords,
        "spaced_typed_reassembly": FrameKeywords(root, False) == keywords,
        "tags": dict(Counter(node.tag for node in root.iter())), "dissectable_child_arities": children,
    }


def audit(revision):
    require(re.fullmatch(r"[a-f0-9]{40}", revision), "supply an exact Git revision")
    operators = {}
    for path in OPERATORS:
        expected = git("show", f"{revision}:{path}")
        require((ROOT / path).read_bytes() == expected, "source codec differs from the frozen revision")
        operators[path] = digest(expected)
    documents = {path: inspect(raw) for path, raw in pinned_documents(revision)}
    tags = Counter()
    for row in documents.values():
        tags.update(row["tags"])
    return {
        "schema": "kit.sw2026.keyword-corpus-audit.v1", "revision": revision,
        "script_sha256": digest(Path(__file__).read_bytes()), "operators": operators,
        "source_scope": SCOPE, "python": sys.version.split()[0], "source_files": len(documents),
        "parts": sum(path.casefold().endswith(".sldprt") for path in documents),
        "assemblies": sum(path.casefold().endswith(".sldasm") for path in documents),
        "ordinary_framing": sum(row["ordinary_framing"] for row in documents.values()),
        "compact_exact": sum(row["compact_typed_reassembly"] for row in documents.values()),
        "spaced_exact": sum(row["spaced_typed_reassembly"] for row in documents.values()),
        "element_counts": dict(tags),
        "child_arities": dict(Counter(str(arity) for row in documents.values() for arity in row["dissectable_child_arities"])),
        "native_processes_started": 0, "heldout_inputs_read": 0, "native_writer_outputs": 0,
        "documents": documents,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure KeyWords framing in the checked-in 2026 part and assembly corpus")
    parser.add_argument("revision")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = audit(args.revision)
    payload = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as target:
        target.write(payload)
    print(json.dumps({key: report[key] for key in ("source_files", "compact_exact", "spaced_exact", "child_arities")} | {"receipt_sha256": digest(payload)}))
