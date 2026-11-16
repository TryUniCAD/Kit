from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from types import ModuleType
from xml.parsers import expat

DISCOVERY = (
    "D01CircleRadius", "D02CircleRadius", "D03CircleRadius", "D04CircleRadius",
    "D05CircleRadius", "D06CircleRadius", "D07CircleRadius", "D08CircleRadius",
    "D09Arc17Ccw", "D10Arc17Cw", "D11Arc90Ccw", "D12Arc90Cw",
    "D13Arc180Ccw", "D14Arc180Cw", "D15Arc270Ccw", "D16Arc270Cw",
    "D17TopCircle", "D18RightCircle", "D19Annulus", "D20TwoCircles",
    "D21EightCircles", "D22ConstructionArc", "D23TangentCapsule", "D24NearFullArc",
)
CONTROLS = ("ControlCircle", "ControlRectangle")
VERSION = "34.5.2.0604"
WORD_VERSION = [34, 5, 2, 604]
MAX_FILE = 64 * 1024 * 1024
MAX_STREAM = 64 * 1024 * 1024
MAX_DECODED = 256 * 1024 * 1024
MODULES = (
    "interchange.Enums.EnumBase",
    "interchange.Enums.EnumDocument",
    "convert.adapters.base.FieldAliases",
    "convert.adapters.base.ContractCompat",
    "convert.adapters.base.AdapterInfoView",
    "convert.adapters.base.AdapterInfo",
    "convert.adapters.solidworks.Container.RotateBytes",
    "convert.adapters.solidworks.Container.DecodeName",
    "convert.adapters.solidworks.Container.SldprtFormat",
    "convert.adapters.solidworks.Container.StreamLimits",
    "convert.adapters.solidworks.Container.InflateStream",
    "convert.adapters.solidworks.Container.DecodePayload",
    "convert.adapters.solidworks.Container.StreamRecord",
    "convert.adapters.solidworks.Container.DecodeScanned",
    "convert.adapters.solidworks.Container.Format",
    "convert.adapters.solidworks.Container.Container",
)
PACKAGES = (
    "interchange", "interchange.enums", "convert", "convert.adapters",
    "convert.adapters.base", "convert.adapters.solidworks",
    "convert.adapters.solidworks.container",
)
STDLIB_IMPORTS = {
    "__future__", "dataclasses", "enum", "inspect", "pathlib", "re", "struct",
    "types", "typing", "zlib",
}
BINARY_METADATA = {
    "Header2", "Contents/Definition", "Contents/DisplayLists",
    "_MO_VERSION_19000/Biography",
}
XML_METADATA = {"creator", "lastmodifiedby", "author", "username", "lastsavedby"}
SOURCE_NOTICE = (
    "SOLIDWORKS-authored discovery/control source fixtures prepared only for research parsing; "
    "not Kit-generated writer output, held-out validation or inherited native acceptance"
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_digest(value, label):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"invalid SHA-256 for {label}")
    return value


def checked_path(root, relative, directory=False):
    path = root / relative
    if path.is_symlink():
        raise ValueError(f"symlink is not permitted: {relative}")
    current = root
    for part in Path(relative).parts:
        if part in {"..", "."}:
            raise ValueError("relative source path must be canonical")
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink is not permitted: {relative}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("source path leaves the selected source root")
    if directory and not resolved.is_dir():
        raise ValueError(f"expected source directory: {relative}")
    if not directory and not resolved.is_file():
        raise ValueError(f"expected source file: {relative}")
    return resolved


def read_bytes(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError(f"source exceeds preparation size bound: {path.name}")
    return path.read_bytes()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def invalid_number(value):
    raise ValueError(f"non-finite JSON number: {value}")


def read_json(path):
    raw = read_bytes(path)
    value = json.loads(
        raw, object_pairs_hook=unique_object, parse_constant=invalid_number,
    )
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value, digest(raw)


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def container_api(repository):
    if any(name in sys.modules for name in PACKAGES):
        raise ValueError("container preparation requires a fresh interpreter without the SDK imported")
    source = checked_path(repository, "src", directory=True)
    sources = {}
    for name in MODULES:
        relative = Path(*name.split(".")).with_suffix(".py")
        path = checked_path(source, relative)
        raw = read_bytes(path)
        tree = ast.parse(raw, filename=str(relative))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    raise ValueError(f"unexpected relative import in bounded container dependency: {name}")
                imported = [node.module]
            else:
                continue
            if any(item not in MODULES and item not in PACKAGES and item not in STDLIB_IMPORTS for item in imported):
                raise ValueError(f"unreviewed import in bounded container dependency: {name}")
        sources[name] = (path, raw)
    for name in PACKAGES:
        package = ModuleType(name)
        package.__path__ = [str(source.joinpath(*name.split(".")))]
        package.__package__ = name
        package.__spec__ = importlib.util.spec_from_loader(name, loader=None, is_package=True)
        sys.modules[name] = package
    loaded = []
    for name in MODULES:
        path, raw = sources[name]
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ValueError("cannot load bounded container dependency")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
        loaded.append({"module": name, "file": str(path.relative_to(repository)), "sha256": digest(raw)})
        if name == "interchange.Enums.EnumDocument":
            sys.modules["interchange"].Capability = module.Capability
        if name == "convert.adapters.base.AdapterInfo":
            sys.modules["convert.adapters.base"].AdapterInfo = module.AdapterInfo
    return sys.modules[MODULES[-1]], {
        "strategy": "explicit real-module dependency order with namespace packages",
        "package_initializers_executed": False,
        "mocked_behavior": False,
        "archive_schemas_loaded": False,
        "modules": loaded,
        "python": sys.version,
    }


class Privacy:
    def __init__(self, names, dimension_names):
        if not names or any(not name or name.isspace() for name in names):
            raise ValueError("at least one nonempty --redact-name is required")
        self.names = [re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", re.IGNORECASE) for name in names]
        self.home = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]|[\\/]{2}Mac[\\/]Home[\\/]|/Users/|/home/)", re.IGNORECASE)
        self.email = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.dimension_names = set(dimension_names)
        if any(self.non_email_private(value) for value in self.dimension_names):
            raise ValueError("qualified dimension identity contains an account/home marker")
        self.name_fingerprints = [{"sha256": digest(name.encode()), "utf8_bytes": len(name.encode())} for name in names]

    def non_email_private(self, text):
        return self.home.search(text) is not None or any(pattern.search(text) is not None for pattern in self.names)

    def private(self, text, framed=False):
        if self.non_email_private(text):
            return True
        if framed and text in self.dimension_names:
            return False
        return self.email.search(text) is not None

    def replace(self, text, encoding):
        if self.home.search(text) is not None:
            count = len(text.encode(encoding)) // (2 if encoding.startswith("utf-16") else 1)
            return "_" * count
        result = text
        for pattern in [self.email, *self.names]:
            result = pattern.sub(lambda match: "_" * (len(match.group().encode(encoding)) // (2 if encoding.startswith("utf-16") else 1)), result)
        if len(result.encode(encoding)) != len(text.encode(encoding)):
            raise ValueError("privacy replacement changed encoded width")
        return result

    def dimension_frames(self, data):
        spans = []
        for value in self.dimension_names:
            payload = value.encode("utf-16-le")
            count = len(payload) // 2
            if not 0 < count < 255:
                continue
            frame = b"\xff\xfe\xff" + bytes([count]) + payload
            cursor = 0
            while True:
                start = data.find(frame, cursor)
                if start < 0:
                    break
                spans.append((start + 4, start + len(frame)))
                cursor = start + len(frame)
        return spans

    def scan(self, data, xml_dimension_spans=()):
        email_view = bytearray(data)
        for start, end in [*self.dimension_frames(data), *xml_dimension_spans]:
            email_view[start:end] = b"\x00" * (end - start)
        for encoding, offsets in (("utf-8", (0,)), ("latin-1", (0,)), ("utf-16-le", (0, 1)), ("utf-16-be", (0, 1))):
            for offset in offsets:
                if self.non_email_private(data[offset:].decode(encoding, errors="replace")):
                    return True
                if self.email.search(email_view[offset:].decode(encoding, errors="replace")) is not None:
                    return True
        return False

    def private_json(self, value):
        if isinstance(value, str):
            return self.private(value, framed=True)
        if isinstance(value, list):
            return any(self.private_json(item) for item in value)
        if isinstance(value, dict):
            return any(self.private(key) or self.private_json(item) for key, item in value.items())
        return False


def dimension_identities(selected):
    names = set()
    for manifest, manifest_hash, raw, source_manifest in selected:
        candidates = []
        for role in ("author", "verify"):
            for call in manifest[role]["api_calls"]:
                if call.get("method") == "FullName":
                    candidates.append(call.get("result"))
        for rows in (manifest["author"]["dimensions"], manifest["verify"]["job"]["dimensions"]):
            candidates.extend(row.get("full_name") for row in rows)
        for value in candidates:
            if not isinstance(value, str):
                raise ValueError("source FullName/dimension observation is not a string")
            components = value.split("@")
            if len(components) < 3 or any(not component for component in components) or re.fullmatch(r"D[1-9][0-9]*", components[0]) is None or not components[-1].endswith(".Part") or not components[-1][:-5] or any(char in value for char in "\r\n\x00<>/\\"):
                raise ValueError("source FullName/dimension observation is not a qualified CAD dimension identifier")
            names.add(value)
    return names


def replacement_record(kind, start, before, after, context):
    if len(before) != len(after):
        raise ValueError("privacy operation changed encoded byte width")
    return {
        "kind": kind, "offset": start, "bytes": len(before), "context": context,
        "source_value_sha256": digest(before), "replacement_sha256": digest(after),
    }


def binary_redaction(name, data, privacy, *, additional_metadata_streams=()):
    output = bytearray(data)
    replacements = []
    allowed = name in BINARY_METADATA or name in additional_metadata_streams or re.fullmatch(r"Contents/Config-\d+-ModelHeader", name) is not None
    cursor = 0
    while True:
        start = data.find(b"\xff\xfe\xff", cursor)
        if start < 0:
            break
        cursor = start + 3
        if start + 4 > len(data):
            continue
        count = data[start + 3]
        if not 0 < count < 255:
            continue
        begin, end = start + 4, start + 4 + 2 * count
        if end > len(data):
            continue
        before = data[begin:end]
        try:
            text = before.decode("utf-16-le")
        except UnicodeDecodeError:
            continue
        if not privacy.private(text, framed=True):
            continue
        if not allowed:
            raise ValueError(f"private CString appears outside recognized metadata stream: {name}")
        if "\x00" in text or any(ord(char) < 32 for char in text):
            raise ValueError(f"private CString metadata contains unsupported control characters: {name}")
        if replacements and begin < replacements[-1]["offset"] + replacements[-1]["bytes"]:
            raise ValueError("overlapping CString privacy operations")
        after = privacy.replace(text, "utf-16-le").encode("utf-16-le")
        output[begin:end] = after
        replacements.append(replacement_record("short-unicode-cstring", begin, before, after, name))
        cursor = end
    return bytes(output), replacements


def xml_redaction(name, data, privacy):
    output = bytearray(data)
    replacements = []
    dimension_spans = []
    stack = []
    parser = expat.ParserCreate(namespace_separator="}")

    def forbidden(*arguments):
        raise ValueError(f"DTD/entity declarations are unsupported in fixture XML: {name}")

    def begin(tag, attributes):
        if stack:
            stack[-1]["children"] = True
        stack.append({"tag": tag, "attributes": attributes, "text": [], "start": None, "children": False})

    def text(value):
        if not stack:
            return
        node = stack[-1]
        if node["start"] is None:
            node["start"] = parser.CurrentByteIndex
        node["text"].append(value)

    def end(tag):
        node = stack.pop()
        value = "".join(node["text"])
        if value in privacy.dimension_names:
            if node["children"] or node["start"] is None or data[node["start"]:parser.CurrentByteIndex] != value.encode("utf-8"):
                raise ValueError(f"qualified XML dimension uses unsupported text framing: {name}")
            dimension_spans.append((node["start"], parser.CurrentByteIndex))
        if not privacy.private(value, framed=True):
            return
        local = tag.rsplit("}", 1)[-1].casefold()
        property_name = stack[-1]["attributes"].get("name", "") if stack else ""
        property_key = re.sub(r"[^a-z]", "", property_name.casefold())
        metadata_property = any(key in property_key for key in ("author", "lastsavedby", "lastmodifiedby", "username", "creator"))
        allowed = name.startswith("docProps/") and name.endswith(".xml") and (local in XML_METADATA or local == "lpstr" and metadata_property)
        if not allowed or node["children"] or node["start"] is None:
            raise ValueError(f"private XML text appears outside recognized metadata context: {name}")
        start, finish = node["start"], parser.CurrentByteIndex
        before = data[start:finish]
        if before != value.encode("utf-8"):
            raise ValueError(f"private XML text uses unsupported escaping/encoding: {name}")
        after = privacy.replace(value, "utf-8").encode("utf-8")
        output[start:finish] = after
        replacements.append(replacement_record("xml-text", start, before, after, tag + (":" + property_name if property_name else "")))

    parser.StartElementHandler = begin
    parser.EndElementHandler = end
    parser.CharacterDataHandler = text
    parser.StartDoctypeDeclHandler = forbidden
    parser.EntityDeclHandler = forbidden
    parser.ExternalEntityRefHandler = forbidden
    parser.Parse(data, True)
    return bytes(output), replacements, dimension_spans


def sanitize(value, privacy, changes, location):
    if isinstance(value, str):
        if not privacy.private(value, framed=True):
            return value
        if any(identifier in value for identifier in privacy.dimension_names):
            raise ValueError("qualified dimension appears outside a whole structured string")
        after = privacy.replace(value, "utf-8")
        changes.append({
            "field": location, "kind": "structured-json-string",
            "source_value_sha256": digest(value.encode()), "replacement_sha256": digest(after.encode()),
            "source_utf8_bytes": len(value.encode()), "replacement_utf8_bytes": len(after.encode()),
        })
        return after
    if isinstance(value, dict):
        if any(not isinstance(key, str) or privacy.private(key) for key in value):
            raise ValueError("unsupported private/non-string JSON key")
        return {key: sanitize(item, privacy, changes, location + "." + key) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item, privacy, changes, location + f"[{index}]") for index, item in enumerate(value)]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite source number")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ValueError("unsupported source metadata type")


def validate_identity(identity):
    if not isinstance(identity, dict) or identity.get("file_version") != VERSION or identity.get("file_version_words") != WORD_VERSION or identity.get("expected_version") != WORD_VERSION or identity.get("version_matches") is not True or identity.get("executable") != "SLDWORKS.exe" or identity.get("pe_machine") != "0x8664":
        raise ValueError("source oracle identity is not the pinned 2026 build")
    for key in ("process_id", "process_creation_filetime", "bytes"):
        if type(identity.get(key)) is not int or identity[key] <= 0:
            raise ValueError("source oracle identity has an invalid exact integer")
    return checked_digest(identity.get("sha256"), "source executable"), identity["bytes"]


def validate_case(source, group, name, proof, identity, locked):
    relative = f"{group}/{name}"
    checked_path(source, relative, directory=True)
    manifest_path = checked_path(source, relative + "/Manifest.json")
    native_path = checked_path(source, relative + "/" + name + ".SLDPRT")
    manifest, manifest_hash = read_json(manifest_path)
    if manifest_hash != locked.get("manifest_sha256"):
        raise ValueError(f"source manifest differs from frozen lock: {name}")
    case = manifest.get("case")
    split = "discovery" if group == "Discovery" else "control"
    if not isinstance(case, dict) or case.get("name") != name or case.get("split") != split or manifest.get("passed") is not True:
        raise ValueError(f"source case manifest mismatch: {name}")
    for role in ("author", "verify"):
        phase = manifest.get(role)
        if not isinstance(phase, dict) or phase.get("passed") is not True or phase.get("work_completed") is not True or phase.get("worker_exit_code") != 0 or phase.get("worker_timed_out") is not False or phase.get("first_failure") is not None or phase.get("cleanup_errors"):
            raise ValueError(f"source phase did not finish cleanly: {name}/{role}")
        checks = phase.get("checks")
        if not isinstance(checks, list) or not checks or any(not isinstance(check, dict) or check.get("passed") is not True for check in checks):
            raise ValueError(f"source phase has incomplete checks: {name}/{role}")
        if validate_identity(phase.get("identity")) != identity:
            raise ValueError(f"source executable identity differs: {name}/{role}")
        job = phase.get("job")
        if not isinstance(job, dict) or job.get("tool_hashes") != proof["source_tools"] or job.get("case") != case:
            raise ValueError(f"source tool/spec identity differs: {name}/{role}")
    source_hash = checked_digest(manifest.get("sha256"), name)
    if source_hash != locked.get("sha256") or locked.get("split") != split:
        raise ValueError(f"source native/split differs from frozen lock: {name}")
    if manifest["verify"].get("source_sha256_after") != source_hash:
        raise ValueError(f"source changed during native verification: {name}")
    raw = read_bytes(native_path)
    if digest(raw) != source_hash:
        raise ValueError(f"original native hash differs: {name}")
    return manifest, manifest_hash, raw, relative + "/Manifest.json"


def prepare_case(api, manifest, manifest_hash, raw, source_manifest, privacy):
    case = manifest["case"]
    name = case["name"]
    archive = api.SldprtArchive.FromBytes(raw, name, SizeLimit=MAX_DECODED)
    versions = {key.split("/", 1)[0] for key in archive.streams if key.startswith("_MO_VERSION_")}
    configurations = sorted(key for key in archive.streams if re.fullmatch(r"Contents/Config-\d+", key))
    if versions != {"_MO_VERSION_19000"} or configurations != ["Contents/Config-0"]:
        raise ValueError(f"unsupported version/configuration set: {name}")
    items = []
    streams = []
    operations = []
    total = 0
    for stream in archive.records:
        if privacy.private(stream.name):
            raise ValueError(f"private stream name cannot be rewritten: {name}")
        data = stream.data
        total += len(data)
        if len(data) > MAX_STREAM or total > MAX_DECODED:
            raise ValueError(f"decoded fixture exceeds preparation bound: {name}")
        xml = stream.name.endswith(".xml")
        if xml:
            prepared, changes, dimension_spans = xml_redaction(stream.name, data, privacy)
        else:
            prepared, changes = binary_redaction(stream.name, data, privacy)
            dimension_spans = []
        if privacy.scan(prepared, dimension_spans):
            raise ValueError(f"unrecognized private byte context remains in {name}/{stream.name}")
        if len(prepared) != len(data):
            raise ValueError("prepared stream changed encoded length")
        changed = set()
        for change in changes:
            start = change["offset"]
            changed.update(range(start, start + change["bytes"]))
            operations.append({"stream": stream.name, **change})
        if any(before != after and index not in changed for index, (before, after) in enumerate(zip(data, prepared))):
            raise ValueError("stream change has no framed privacy operation")
        items.append((stream.name, prepared))
        streams.append({
            "name": stream.name, "bytes": len(prepared), "source_sha256": digest(data),
            "sha256": digest(prepared), "privacy_operations": len(changes),
        })
    result = api.BuildSldprt(items, Template=raw)
    metadata_changes = []
    snapshots = {
        "author": manifest["author"]["authored"], "reopened": manifest["verify"]["reopened"],
        "edited": manifest["verify"]["edited"], "edit": manifest["verify"]["edit"],
        "author_identity": manifest["author"]["identity"], "verify_identity": manifest["verify"]["identity"],
        "author_dimensions": manifest["author"]["dimensions"], "verify_dimensions": manifest["verify"]["job"]["dimensions"],
        "author_checks": manifest["author"]["checks"], "verify_checks": manifest["verify"]["checks"],
        "save_calls": [call for call in manifest["author"]["api_calls"] if call.get("method") == "SaveAs3"],
    }
    if not snapshots["save_calls"]:
        raise ValueError(f"source has no SaveAs3 observation: {name}")
    record = {
        "name": name, "file": name + ".SLDPRT", "split": case["split"],
        "source_sha256": manifest["sha256"], "sha256": digest(result),
        "source_manifest": source_manifest, "source_manifest_sha256": manifest_hash,
        "spec": sanitize(case, privacy, metadata_changes, "spec"),
        "source_observations": sanitize(snapshots, privacy, metadata_changes, "source_observations"),
        "configurations": ["Config-0"], "streams": streams,
    }
    ledger = {
        "name": name, "source_sha256": manifest["sha256"], "sha256": digest(result),
        "stream_operations": operations, "metadata_operations": metadata_changes,
        "unchanged_encoded_stream_lengths": True,
        "container_rebuilt": True, "container_output_reparsed": False,
    }
    return result, record, ledger


def main():
    parser = argparse.ArgumentParser(description="Prepare only locked curve discovery/control research fixtures without archive-schema execution")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-lock-sha256", required=True)
    parser.add_argument("--expected-proof-sha256", required=True)
    parser.add_argument("--redact-name", action="append", required=True)
    arguments = parser.parse_args()
    if sys.version_info < (3, 11):
        raise ValueError("preparation requires Python 3.11 or later")
    source_argument = arguments.source.expanduser().absolute()
    source = source_argument.resolve(strict=True)
    if source != source_argument or source_argument.is_symlink() or not source.is_dir():
        raise ValueError("source root must be a canonical directory without symlinks")
    destination = arguments.destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination must not already exist")
    parent = destination.parent.resolve(strict=True)
    if parent != destination.parent or not parent.is_dir():
        raise ValueError("destination parent must be an existing canonical directory without symlinks")
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("preparation output must be separate from original source evidence")
    expected_lock = checked_digest(arguments.expected_lock_sha256, "expected lock")
    expected_proof = checked_digest(arguments.expected_proof_sha256, "expected proof")
    lock, lock_hash = read_json(checked_path(source, "Lock.json"))
    proof, proof_hash = read_json(checked_path(source, "RootLockVerification.json"))
    if lock_hash != expected_lock or proof_hash != expected_proof or proof.get("lock_sha256") != lock_hash:
        raise ValueError("source lock/root verification fingerprint differs")
    if proof.get("all_checks_passed") is not True or proof.get("native_source_files_hash_verified") != 32 or proof.get("source_cases") != 30 or proof.get("controls_before") != ["ControlRectangle", "ControlCircle"] or proof.get("controls_after") != ["ControlRectangle", "ControlCircle"] or proof.get("writer_implementation_started") is not False:
        raise ValueError("source-family lock proof is incomplete")
    tools = proof.get("source_tools")
    if not isinstance(tools, dict) or set(tools) != {"AuthorCurves.py", "Swapp.py", "OracleIdentity.py"}:
        raise ValueError("source proof has an unsupported authoring tool set")
    for name, fingerprint in tools.items():
        checked_digest(fingerprint, name)
    revision = proof.get("source_revision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("source proof has no exact revision")
    if lock.get("schema") != "kit-sw2026-curve-source-lock/1" or lock.get("generator_revision") != revision or lock.get("tool_hashes") != tools or lock.get("script_sha256") != tools["AuthorCurves.py"] or lock.get("writer_implementation_started") is not False or lock.get("batch_sha256") != proof.get("batch_sha256"):
        raise ValueError("frozen source lock and root verification disagree")
    cases = lock.get("cases")
    if not isinstance(cases, list) or len(cases) != 32:
        raise ValueError("frozen source lock has an unexpected hash-record count")
    selected_names = set(DISCOVERY + CONTROLS)
    locked = {}
    for item in cases:
        if not isinstance(item, dict):
            raise ValueError("frozen source lock has an invalid hash record")
        name = item.get("name")
        if name in selected_names:
            if name in locked:
                raise ValueError("frozen source lock has duplicate selected records")
            checked_digest(item.get("sha256"), "locked native input")
            checked_digest(item.get("manifest_sha256"), "locked source manifest")
            locked[name] = item
    if set(locked) != selected_names:
        raise ValueError("frozen source lock lacks a selected discovery/control record")
    for group, names in (("Discovery", DISCOVERY), ("Controls", CONTROLS)):
        directory = checked_path(source, group, directory=True)
        if {entry.name for entry in directory.iterdir()} != set(names):
            raise ValueError(f"source selection is not the exact bounded family: {group}")
    first, _ = read_json(checked_path(source, "Controls/ControlRectangle/Manifest.json"))
    identity = validate_identity(first.get("author", {}).get("identity"))
    selected = []
    for group, names in (("Discovery", DISCOVERY), ("Controls", CONTROLS)):
        for name in names:
            selected.append(validate_case(source, group, name, proof, identity, locked[name]))
    privacy = Privacy(arguments.redact_name, dimension_identities(selected))
    repository = Path(__file__).resolve().parents[3]
    sys.dont_write_bytecode = True
    api, dependencies = container_api(repository)
    files = []
    records = []
    ledgers = []
    for item in selected:
        prepared, record, ledger = prepare_case(api, *item, privacy)
        files.append((record["file"], prepared))
        records.append(record)
        ledgers.append(ledger)
    ledger_data = {
        "schema": "kit.sw2026.curve-discovery-privacy.v1", "research_only": True,
        "scope": "recognized short Unicode CString metadata and plain UTF-8 XML metadata text; not a full parametric field parse",
        "private_name_fingerprints": privacy.name_fingerprints, "records": ledgers,
        "qualified_dimension_identifiers": sorted(privacy.dimension_names),
        "technical_identifier_policy": "email-only exceptions require exact frozen FullName/dimension observations and whole JSON/CString/XML text framing; account/home markers take precedence",
        "unsupported_private_context_policy": "fail before creating destination",
    }
    ledger_bytes = json_bytes(ledger_data)
    source_lock = {
        "sha256": lock_hash, "source_revision": revision,
        "owner_verification_sha256": proof_hash, "heldout_native_payloads_included": 0,
    }
    manifest_data = {
        "schema": "kit.sw2026.curve-discovery-fixtures.v1", "version": 19000,
        "native_build": VERSION, "research_only": True, "origin": "oracle-authored",
        "is_writer_output": False, "native_acceptance_inherited": False,
        "provenance": SOURCE_NOTICE, "source_lock": source_lock,
        "privacy_ledger_sha256": digest(ledger_bytes), "records": records,
    }
    manifest_bytes = json_bytes(manifest_data)
    proof_changes = []
    evidence_data = {
        "schema": "kit.sw2026.curve-discovery-source-evidence.v1",
        "manifest_sha256": digest(manifest_bytes), "privacy_ledger_sha256": digest(ledger_bytes),
        "source_lock": source_lock, "owner_verification": sanitize(proof, privacy, proof_changes, "owner_verification"),
        "owner_verification_privacy_operations": proof_changes,
        "selected_discovery": 24, "selected_controls": 2, "heldout_payloads_read": 0,
        "source_hashes_recomputed": 26, "archive_model_verification_executed": False,
        "fixture_native_acceptance": "unmeasured", "provenance": SOURCE_NOTICE,
        "preparer_sha256": digest(Path(__file__).read_bytes()), "dependencies": dependencies,
        "privacy_scan": "known operator account names, home paths and email patterns across UTF-8, Latin-1 and both UTF-16 alignments; no exhaustive privacy attestation",
    }
    evidence_bytes = json_bytes(evidence_data)
    for label, payload, value in (("Manifest.json", manifest_bytes, manifest_data), ("PrivacyLedger.json", ledger_bytes, ledger_data), ("SourceEvidence.json", evidence_bytes, evidence_data)):
        if privacy.private_json(value):
            raise ValueError(f"private publication metadata remains: {label}")
        files.append((label, payload))
    destination.mkdir(exist_ok=False)
    for name, payload in files:
        with (destination / name).open("xb") as output:
            output.write(payload)
    print(json.dumps({
        "prepared": len(records), "manifest_sha256": digest(manifest_bytes),
        "source_lock_sha256": lock_hash, "is_writer_output": False,
        "native_acceptance_inherited": False,
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"preparation failed: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)
