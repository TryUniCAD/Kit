from argparse import ArgumentParser
from dataclasses import replace
import json
from pathlib import Path
import re
from struct import unpack_from
import sys
from xml.etree.ElementTree import tostring

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parent), str(HERE.parents[4] / "src")]

from AuditSavedSweepMain import LOCK, ORACLE, checked, demand, digest
from convert import open_document
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import MakeBiography
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistGraph import ReadHistGraph
from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot

BIOGRAPHY = "_MO_VERSION_19000/Biography"
CORE = "docProps/core.xml"
INFO = "docProps/ISolidWorksInformation.xml"
OMITTED = ("Contents/Definition", "Contents/DisplayLists")
HEADERS = ("Header2", "Contents/Config-0-ModelHeader")
FIXTURE_NAME = "Kit fixture"
SOURCES = (
    ("original", "SweepArcWide.SLDPRT", "author"),
    ("section", "SweepArcWideSectionEdit.SLDPRT", "section-reopen"),
)


def cleared_header(raw, editor):
    root = ReadHeaderGraph(raw, 19000)
    demand(WriteHeadGraph(root, 19000) == raw, "disclosed header did not replay exactly")
    holder = root.FieldsValue["f10"]
    user, = holder.FieldsValue["values"]
    demand(user.TextValue == editor and holder.FieldsValue["items"] == (editor,), "header author owner differs")
    holder.FieldsValue["values"] = (replace(user, TextValue=FIXTURE_NAME),)
    holder.FieldsValue["items"] = (FIXTURE_NAME,)
    return WriteHeadGraph(root, 19000)


def clean_xml(streams):
    core = ReadPropRoot(streams[CORE])
    editor, = (child for child in core if child.tag.endswith("}lastModifiedBy"))
    name = editor.text
    demand(name, "expected an attributable native save operator")
    info = ReadPropRoot(streams[INFO])
    editor_info, = (child for child in info.iter() if child.text == name)
    demand(editor_info.tag.endswith("}lpstr"), "alternate native operator owner differs")
    editor.text = FIXTURE_NAME
    editor_info.text = FIXTURE_NAME
    return name, {label: tostring(root, encoding="utf-8", xml_declaration=True)
                  for label, root in ((CORE, core), (INFO, info))}


def has_executable(data):
    for match in re.finditer(b"MZ", data):
        start = match.start()
        if len(data) - start < 64:
            continue
        header = unpack_from("<I", data, start + 60)[0]
        if 64 <= header <= len(data) - start - 24 and data[start + header:start + header + 4] == b"PE\0\0":
            return True
    return any(value in data for value in (
        b"\x7fELF", b"MSCF", b"PK\x03\x04", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    ))


def privacy_scan(archive, editor):
    identity = re.compile(r"(?<![\w])" + re.escape(editor) + r"(?![\w])", re.IGNORECASE | re.ASCII)
    path = re.compile(r"(?:[a-z]:\\users\\|/Users/|\\\\Mac\\Home)", re.IGNORECASE)
    expected_empty = ("Contents/OleItems", "OleItemInformation/OLE_Item_Data", "Contents/eModelLic")
    demand(all(archive.require(name) == bytes(4) for name in expected_empty), "unexpected OLE or license payload")
    for name, data in archive.streams.items():
        views = (data.decode("latin-1"), *(data[start:].decode("utf-16-le", errors="replace") for start in (0, 1)))
        demand(not any(identity.search(text) or path.search(text) for text in views)
               and not has_executable(data), f"unexpected account or embedded executable signature in {name}")


def fixture(raw):
    source = SldprtArchive.from_bytes(raw)
    streams = source.streams
    demand(source.format_version == 4 and len(streams) == 41, "unqualified native sweep envelope")
    editor, replacements = clean_xml(streams)
    old_bio = ReadHistGraph(streams[BIOGRAPHY], 19000).RootValue
    records = old_bio.FieldsValue["records"]
    localized = [entry["r"]["fe8"]["s3"] for entry in records[:1]]
    demand(localized and localized[0].casefold().startswith(("c:\\users\\" + editor + "\\").casefold()),
           "biography does not identify the same operator")
    replacements[BIOGRAPHY] = WriteHistGraph(MakeBiography(), 19000)[0]
    replacements.update((name, cleared_header(streams[name], editor)) for name in HEADERS)
    retained = {name: replacements.get(name, data) for name, data in streams.items() if name not in OMITTED}
    payload = BuildSldprt(retained, FormatVersion=4)
    portable = SldprtArchive.from_bytes(payload)
    demand(tuple(portable.streams) == tuple(retained) and portable.streams == retained
           and all(retained[name] != streams[name] for name in replacements),
           "fixture changed an undeclared stream")
    demand(not has_executable(payload), "unexpected executable signature in framed fixture")
    privacy_scan(portable, editor)
    for include in (True, False):
        before = open_document(raw, source_format="solidworks.sldprt", strict=True, include_brep=include)
        after = open_document(payload, source_format="solidworks.sldprt", strict=True, include_brep=include)
        demand(before == replace(after, source=replace(after.source, sha256=before.source.sha256))
               and before.source.sha256 == digest(raw) and after.source.sha256 == digest(payload),
               "privacy scrub changed strict editable sweep projection")
    return payload, {
        "scrubbed_streams": sorted(replacements),
        "omitted_streams": list(OMITTED),
        "unchanged_streams": len(retained) - len(replacements),
        "semantic_projection_equal": True,
        "archive_bytes": len(payload),
        "archive_sha256": digest(payload),
        "original_archive_bytes": len(raw),
        "original_archive_sha256": digest(raw),
    }


def stage(disclosed, output):
    lock = json.loads(checked(disclosed / "SourceLock.json", LOCK))
    demand(lock["cohort"] == "disclosed" and lock["passed"] and lock["inputs_unchanged"]
           and lock["oracle_build"] == "34.5.2.0604" and lock["oracle_sha256"] == ORACLE
           and lock["fresh_processes"] == lock["distinct_processes"] == 12
           and set(lock["controls"]) == {"before", "after"} and all(row["passed"] for row in lock["controls"].values()),
           "disclosed source lifecycle or controls differ")
    source = lock["sources"][1]
    demand(source["slot"] == 1 and source["passed"], "wrong disclosed sweep source")
    files, cases = {}, {}
    for role, name, phase in SOURCES:
        pin = source["artifact_sha256"][role]
        (observation,) = (row for row in source["phases"] if row["phase"] == phase)
        demand(observation["passed"] and observation["artifact_sha256"] == pin,
               "native source authority does not bind this archive")
        raw = checked(disclosed / name, pin)
        demand(len(raw) == observation["artifact_bytes"], "native source extent differs")
        payload, proof = fixture(raw)
        files[name] = payload
        cases[role] = {
            **proof, "file": name, "native_phase": phase,
            "native_phase_receipt_sha256": observation["receipt_sha256"],
        }
    ledger = {
        "schema": "kit.sw2026.saved-sweep-scrubbed-regression.v1",
        "source_lock_sha256": LOCK, "source_slot": 2, "oracle_sha256": ORACLE,
        "oracle_build": lock["oracle_build"],
        "author_revision": lock["source_revision"], "author_tree": lock["source_tree"],
        "authored_spec_sha256": lock["spec_sha256"],
        "healthy_controls": {name: row["receipt_sha256"] for name, row in lock["controls"].items()},
        "fixture_native_observations": 0, "writer_acceptance_credits": 0, "heldout_credits": 0,
        "cases": cases,
    }
    output.mkdir(exist_ok=False)
    files["Fixtures.json"] = (json.dumps(ledger, sort_keys=True, indent=2) + "\n").encode()
    for name, payload in files.items():
        with (output / name).open("xb") as target:
            target.write(payload)
    return ledger


if __name__ == "__main__":
    parser = ArgumentParser(description="Prepare the two privacy-scrubbed saved sweep reader fixtures")
    parser.add_argument("--disclosed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.disclosed, args.output), sort_keys=True, indent=2))
