from collections import Counter
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from os import walk
from pathlib import Path, PurePosixPath
from re import sub
from subprocess import check_output
from sys import argv
from tarfile import TarError, open as open_tar
from xml.etree.ElementTree import fromstring
from zipfile import BadZipFile, ZipFile
from lzma import LZMAError, open as open_xz

SNAPSHOTS = {
    "audit_base": "c9d64090b37b2fa56971662f926441aa9bb2be1f",
    "accepted_main": "0ec0b3e9e3d503e1dde0c18d8ff0a3cfdd0d0750",
    "inventory_revision": "c739ea4da218983a66f05e54342f7f0f124538f7",
    "original_pr_121_head": "960ffde7a866ba94a83043fc8a7d21d0b9edb882",
    "recorded_audit": "2ac05f439476115605ee911cf6eef6fc4221129e",
    "historical_discovery": "48ff095c940efb439c5aea674484bff1522412b6",
    "saved_control_introduction": "22075ee5e77c3db9b56bd8c2bc8c415d6baf237d",
    "additive_box_pr_snapshot": "4662af4b49b9b820f02ad3472b7fce6723ef6f63",
    "additive_box_original_snapshot": "a7de8bb522c654a98de68b01f4e7d4254d84d6dd",
}
MEASUREMENTS = "re/solidworks/measurements/2026/"
HISTORICAL_ASSEMBLIES = (
    ".rescratch/out.FCStd",
    ".rescratch/freecad/FreeCAD_1.1.3-Windows-x86_64-py311/data/examples/AssemblyExample.FCStd",
    "re/solidworks/examples/Random/V8_engine.FCStd",
    "re/solidworks/examples/Random/V8_engine/Conrod_2.FCStd",
    "re/solidworks/examples/Random/V8_engine/Piston_2.FCStd",
)
DOC_SUFFIXES = {".fcstd", ".fcstd1"}
ZIP_HEADERS = {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}
EXCLUDED = ("heldout", "holdout", "sealed")
ASSEMBLY_TYPES = {"Assembly::AssemblyObject", "Assembly::AssemblyLink", "App::Link", "App::LinkGroup"}


def git(repo, *args):
    return check_output(("git", "-C", str(repo), *args))


def digest(data):
    return sha256(data).hexdigest()


def skip(name):
    return any(token in sub(r"[\W_]+", "", name.casefold()) for token in EXCLUDED)


def tracked_document(data):
    with ZipFile(BytesIO(data)) as archive:
        members = [item for item in archive.infolist() if item.filename == "Document.xml"]
        if len(members) != 1 or members[0].file_size > 2_000_000:
            raise ValueError("ambiguous or oversized FreeCAD document member")
        raw = archive.read(members[0])
    xml = raw.decode("utf-8-sig")
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
        raise ValueError("unexpected XML declaration")
    root = fromstring(xml)
    objects = root.find("Objects")
    if root.tag != "Document" or objects is None:
        raise ValueError("FreeCAD document object table missing")
    classes = Counter(obj.attrib["type"] for obj in objects.findall("Object"))
    if int(objects.attrib["Count"]) != sum(classes.values()):
        raise ValueError("object table count mismatch")
    dates = {}
    for name in ("CreationDate", "LastModifiedDate"):
        value = root.find(f"./Properties/Property[@name='{name}']/String")
        if value is not None:
            dates[name] = value.get("value")
    return {
        "source_sha256": digest(data),
        "bytes": len(data),
        "document_xml_sha256": digest(raw),
        "program_version": root.get("ProgramVersion"),
        "document_dates": dates,
        "assembly_or_link_classes": {key: classes[key] for key in sorted(ASSEMBLY_TYPES) if classes[key]},
    }


def tracked_sources(repo, known):
    snapshots, controls = {}, {}
    for label, revision in SNAPSHOTS.items():
        paths = 0
        for line in git(repo, "ls-tree", "-rz", revision, "--", "re").split(b"\0"):
            if not line:
                continue
            header, name = line.split(b"\t", 1)
            path = name.decode()
            if PurePosixPath(path).suffix.casefold() not in DOC_SUFFIXES:
                continue
            mode, kind, oid = header.decode().split()
            if skip(path) or mode != "100644" or kind != "blob":
                raise ValueError("excluded custody path or unsupported Git entry")
            if oid not in controls:
                row = tracked_document(git(repo, "cat-file", "blob", oid))
                controls[oid] = row | {"disclosed_aliases": known.get(row["source_sha256"], []), "path_snapshots": {}}
            controls[oid]["path_snapshots"].setdefault(path, []).append(label)
            paths += 1
        snapshots[label] = {"revision": revision, "tracked_document_paths": paths}
    return snapshots, controls


def block_walk_failure(_error):
    raise RuntimeError("repository research tree could not be fully walked")


def path_state(root, relative):
    for name in PurePosixPath(relative).parts:
        root = root / name
        if root.is_symlink():
            return "symlink_not_followed"
    return "present" if root.exists() else "absent"


def physical_research(root):
    counts = Counter()
    hits, exceptions = [], []
    for directory, subdirs, files in walk(root, followlinks=False, onerror=block_walk_failure):
        subdirs[:] = sorted(name for name in subdirs if not skip(name))
        counts["walked_directories"] += 1
        counts["directory_symlinks"] += sum(Path(directory, name).is_symlink() for name in subdirs)
        for name in sorted(files):
            if skip(name):
                continue
            path = Path(directory, name)
            counts["filesystem_paths"] += 1
            path_hash = digest(path.relative_to(root).as_posix().encode())
            if path.suffix.casefold() in DOC_SUFFIXES:
                hits.append([path_hash, "direct_filename", int(path.is_symlink())])
                continue
            if path.is_symlink() or not path.is_file():
                counts["file_symlinks_or_nonregular"] += 1
                continue
            with path.open("rb") as file:
                prefix = file.read(8)
            try:
                names = []
                if prefix[:4] in ZIP_HEADERS:
                    counts["zip_central_directories"] += 1
                    with ZipFile(path) as archive:
                        names = archive.namelist()
                elif name.casefold().endswith((".tar", ".tar.xz", ".tgz", ".tar.gz", ".tar.bz2")):
                    counts["tar_member_tables"] += 1
                    if path.stat().st_size > 256 * 1024 * 1024:
                        exceptions.append([path_hash, "tar_size_bound"])
                        continue
                    with open_tar(path, "r|*") as archive:
                        names = [item.name for item in archive]
                elif prefix.startswith(b"\xfd7zXZ\0"):
                    counts["standalone_xz_decoded_headers"] += 1
                    with open_xz(path, "rb") as file:
                        if file.read(4) in ZIP_HEADERS:
                            hits.append([path_hash, "wrapped_zip_header", 1])
                elif prefix.startswith((b"7z\xbc\xaf'\x1c", b"Rar!", b"\x1f\x8b")):
                    exceptions.append([path_hash, "other_compression_signature"])
                named = sum(PurePosixPath(member).suffix.casefold() in DOC_SUFFIXES for member in names)
                if named:
                    hits.append([path_hash, "named_archive_member", named])
                if "Document.xml" in names:
                    hits.append([path_hash, "root_document_xml", 1])
            except (BadZipFile, TarError, LZMAError) as error:
                exceptions.append([path_hash, type(error).__name__])
    return {
        "checkout_revision": git(root.parent, "rev-parse", "HEAD").decode().strip(),
        "checkout_re_tree": git(root.parent, "rev-parse", "HEAD:re").decode().strip(),
        "walk_counts": dict(counts),
        "candidates": sorted(hits),
        "archive_metadata_exceptions": sorted(exceptions),
        "historical_random_directory": path_state(root, "solidworks/examples/Random"),
        "historical_locator_states": {path: path_state(root.parent, path) for path in HISTORICAL_ASSEMBLIES},
    }


def evidence(repo, revision, filename, fields):
    path = MEASUREMENTS + filename
    raw = git(repo, "show", f"{revision}:{path}")
    row = loads(raw)
    return {"path": path, "revision": revision, "sha256": digest(raw), **{key: row[key] for key in fields}}


def main(args):
    if len(args) != 3:
        raise SystemExit("usage: AuditFcstdAvailability.py GIT_CHECKOUT PHYSICAL_RE NEW_RECEIPT")
    repo, physical, output = map(Path, args)
    if physical.is_symlink() or physical.name != "re" or not physical.is_dir():
        raise ValueError("PHYSICAL_RE must name the repository research directory")
    physical = physical.resolve(strict=True)
    if output.resolve().is_relative_to(physical):
        raise ValueError("receipt must be outside the inspected research tree")
    inventory_pin = SNAPSHOTS["inventory_revision"]
    inventory_path = MEASUREMENTS + "DisclosedFcstdSourceInventory01.json"
    raw = git(repo, "show", f"{inventory_pin}:{inventory_path}")
    inventory = loads(raw)
    known = {row[0]: row[-1] for row in inventory["source_identities"]}
    snapshots, tracked = tracked_sources(repo, known)
    base = SNAPSHOTS["audit_base"]
    result = {
        "schema": "kit.sw2026.fcstd-corpus-availability.v1",
        "audit_source_sha256": digest(Path(__file__).read_bytes()),
        "requested_target": inventory["requested_target"],
        "historical_audit": inventory["historical_audit"],
        "alternate_inventory_path": inventory_path,
        "alternate_inventory_sha256": digest(raw),
        "alternate_inventory": inventory["independent_scan"],
        "alternate_neutral_read": evidence(repo, base, "NeutralCorpusRead01.json", (
            "source_count", "assembly_documents", "original_benchmark_membership_verified",
        )),
        "alternate_public_write": evidence(repo, base, "PublicFcstdWriterCensus01.json", (
            "original_paths_attempted", "actual_destination_formats", "accepted_conversions", "generated_outputs",
            "historical_165_plus_5_roster_membership_verified",
        )),
        "git_snapshots": snapshots,
        "tracked_controls_by_git_blob": tracked,
        "physical_repository_re": physical_research(physical),
        "native_processes_started": 0,
        "generated_outputs": 0,
        "production_conversion_credit": {"parts": 0, "assemblies": 0},
        "sealed_inputs_opened": 0,
    }
    wire = (dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    with output.open("xb") as file:
        file.write(wire)
    print(digest(wire))


if __name__ == "__main__":
    main(argv[1:])
