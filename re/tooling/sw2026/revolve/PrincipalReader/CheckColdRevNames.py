from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from importlib import import_module
from pathlib import Path
import codecs
import json
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = (str(ROOT / "src"), str(ROOT), str(HERE.parent),
                str(HERE.parents[1] / "PrincipalWriter"))

from AuditPrincipalReader import digest, make_guard
from BuildPrincipalRevolves import authored_neutral
from MakePrincipalCold import make_cold

from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import PrepareCircle
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
from interchange.Core.Common import FreezeMapping
from interchange.document.Behavior.DocumentIo import ToJson
from tests.Convert.Solidworks.Research.AdapterBridge.Circles.MakeWriteCircle import MakeWriteCircle

MEASURED = "re/solidworks/measurements/2026/SdkPrincipalRevolvePreparation01.json"
DISCLOSED = "re/solidworks/v2026/PrincipalRevolveDiscoveryManifest01.json"
SEAL = "solidworks_source_semantic_sha256"
ORDINARY_NAME = "OrdinaryBossRevolve"
MODES = {
    "default": {},
    "no_tessellation": {"include_tessellation": False},
    "history": {"include_brep": False, "include_tessellation": False},
}


def pinned_bytes(path, expected):
    raw = (ROOT / path).read_bytes()
    assert digest(raw) == expected, path
    return raw


def requests():
    measured = json.loads(pinned_bytes(
        MEASURED, "09a553ca599b0fba65cf07c7c57e0d7994ecbbae96fd0ce22f5d53d21a03ac7e"
    ))
    disclosed = json.loads(pinned_bytes(
        DISCLOSED, "dfbcd01d5def3dd1dbe32ee504c223c6fcd0a823d52fb413cf4e2f6fbe1afb53"
    ))
    controls = {row["request"]["spec"]["name"]: row for row in measured["cases"]
                if "alteration" not in row["request"]}
    assert len(controls) == len(disclosed["assets"]) == 4
    for name, row in controls.items():
        yield {"case": name, "request": row["request"], "pinned_output": row["proof"]["sha256"],
               "type": "cold", "name": ORDINARY_NAME, "binds": True}
    for template, plane, name, label, ri, ro in (
        ("TopForward", "top", "ColdSweepLabel", "Pump Collar 7", 13, 31),
        ("RightReverse", "right", "ColdRightLabel", "Spindle Sleeve", 12.5, 33.2),
        ("TopReverse", "top", "ColdUnicodeLabel", "Sleeve Ω", 11, 29),
    ):
        spec = controls[f"KitPrincipalRevolve{template}"]["request"]["spec"] | {
            "name": name, "self_path": rf"C:\KitColdRevolveNames\{name}.SLDPRT",
            "radial_mm": [ri, ro], "created_at": 1795000600,
        }
        yield {"case": name, "request": {"plane": plane, "spec": spec},
               "type": "cold", "name": label, "binds": label.isascii()}
    for row in disclosed["assets"]:
        path = row["path"]
        yield {"case": Path(path).stem, "path": path, "sha256": row["sha256"], "type": "saved"}
    yield {"case": "ExistingColdCylinder", "type": "cylinder"}
    yield {"case": "ExistingLocalImport", "type": "other",
           "path": "re/solidworks/v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT",
           "sha256": "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33"}
    yield {"case": "RotatedTopSupport", "type": "rotated"}


def prepare(case, input_bytes):
    if input_bytes is not None:
        return input_bytes
    if case["type"] == "rotated":
        return make_cold("y", False, rotated=True)[0]
    if case["type"] == "cylinder":
        cylinder = MakeWriteCircle("ExistingColdCylinder", False)
        return PrepareCircle(cylinder, r"C:\KitColdRevolveNames\ExistingColdCylinder.SLDPRT",
                             1795000600).BytesValue
    spec = case["request"]["spec"]
    document = authored_neutral(spec, case["request"]["plane"], None)
    document = replace(document, feature_timeline=(
        replace(document.feature_timeline[0], name=case["name"]),),
        bodies=(replace(document.bodies[0], name=case["name"]),))
    return PrepareRevolve(document, spec["self_path"], spec["created_at"]).BytesValue


def linked_creator(raw, case):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (owner,) = ReadRevOwners(link)
    node = owner.NodeValue
    assert ReadNativeName(node) == case["name"]
    manager = link.ConfigValue.RootValue.FieldsValue["fd88"]
    atom_nodes = tuple(entry.EntryValue for entry in link.ResolvedValue.MapValue.EntriesValue
                       if hasattr(entry.EntryValue, "ClassValue")
                       and entry.EntryValue.ClassValue.NameValue == "moAtom_c")
    assert IsCacheAbsent(archive) and manager["n6c"] == 0 and not manager["atoms"] and not atom_nodes
    assert node.FieldsValue["has_f528"] == 0 and node.FieldsValue.get("f528") is None
    assert node.FieldsValue["n494"] == 0 and not node.FieldsValue["f498"]
    return {"feature": f"sldprt:feature:{NativeNodeId(node)}", "name": ReadNativeName(node),
            "manager_atoms": manager["n6c"], "output_atoms": 0, "resolved_atoms": len(atom_nodes)}


def describe(doc, case, mode, creator):
    doc.assert_valid()
    (body,) = doc.bodies
    row = {"name": body.name, "body_id": body.id,
           "document_sha256": digest(ToJson(doc).encode())}
    if case["type"] == "cold" and mode != "history":
        assert doc.brep is not None and not doc.brep_payloads
        assert "solidworks.native_body_names" not in doc.metadata
        assert "solidworks.cacheless_body_names" not in doc.metadata
        assert any(diagnostic.code == "sldprt.brep_reconstructed" for diagnostic in doc.diagnostics)
        assert len(doc.brep.bodies) == 1 and doc.brep.bodies[0].design_body_id == body.id
        assert not doc.brep.validate(frozenset((body.id,)))
        assert body.final_feature_id == creator["feature"]
        (feature,) = (step for step in doc.feature_timeline if step.id == body.final_feature_id)
        assert feature.name == creator["name"] and feature.provenance is not None
        stable = replace(doc, bodies=(replace(body, name=body.id, provenance=None),),
                         metadata=FreezeMapping({key: value for key, value in doc.metadata.items()
                                                 if key != SEAL}))
        row.update(preserves_creator_provenance=body.provenance == feature.provenance,
                   other_fields_sha256=digest(ToJson(stable).encode()),
                   native_payload_count=len(doc.brep_payloads))
    if case["type"] == "saved" and mode != "history":
        assert body.name == ORDINARY_NAME
        assert doc.metadata["solidworks.native_body_names"]["status"] == "complete"
        assert doc.brep is not None and doc.brep.bodies[0].design_body_id == body.id
        row["native_payloads"] = [value.sha256 for value in doc.brep_payloads]
        assert len(row["native_payloads"]) == 2
    return row


def worker(case):
    input_bytes = pinned_bytes(case["path"], case["sha256"]) if "path" in case else None
    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for module in (
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.AngleRevValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate",
        "interchange.document.Validation.DistExtValidate",
    ):
        import_module(module)
    state, audit = make_guard(ROOT / "src")
    state["enabled"] = True
    raw = prepare(case, input_bytes)
    assert audit["grammar_reads"] == 0, "writer attempted a package layout read"
    archive_hash = digest(raw)
    assert archive_hash == case.get("pinned_output", archive_hash), (case["case"], archive_hash)
    creator = linked_creator(raw, case) if case["type"] == "cold" else None
    modes = {}
    if case["type"] == "rotated":
        try:
            open_document(raw, source_format="solidworks.sldprt", strict=True)
        except ValueError as error:
            modes["default"] = {"refused": str(error)}
        else:
            raise ValueError("quarter-turn Top frame unexpectedly admitted")
    else:
        for mode, options in MODES.items():
            previous_reads = audit["grammar_reads"]
            document = open_document(raw, source_format="solidworks.sldprt", strict=True, **options)
            modes[mode] = describe(document, case, mode, creator)
            grammar_reads = audit["grammar_reads"] - previous_reads
            if case["type"] == "cold" and mode != "history":
                assert grammar_reads == 0, (case["case"], mode)
            modes[mode]["package_layout_reads"] = grammar_reads
    assert not audit["unexpected_attempts"], audit
    return {"archive_sha256": archive_hash, "creator": creator, "modes": modes, "guard": audit}


def isolated(case):
    result = subprocess.run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                            input=json.dumps(case).encode(), capture_output=True, timeout=120)
    assert result.returncode == 0, (case["case"], result.stderr.decode())
    return json.loads(result.stdout)


def compare(cases, original, current):
    changed = unchanged = 0
    for case in cases:
        before, after = original[case["case"]], current[case["case"]]
        assert {k: v for k, v in before.items() if k != "modes"} == {
            k: v for k, v in after.items() if k != "modes"}
        assert before["modes"].keys() == after["modes"].keys()
        for mode, row in before["modes"].items():
            result = after["modes"][mode]
            if case.get("binds") and mode != "history":
                assert row["name"] == "Body 1" and result["name"] == case["name"]
                assert result["preserves_creator_provenance"]
                assert result["other_fields_sha256"] == row["other_fields_sha256"]
                assert result["document_sha256"] != row["document_sha256"]
                changed += 1
            else:
                assert row == result
                unchanged += 1
    return {"only_derived_name_provenance_and_seal_changed": changed,
            "unchanged_reads_and_refusals": unchanged}


def main():
    parser = ArgumentParser(description="Verify derived names on guarded ordinary cold revolves")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--before", type=Path)
    args = parser.parse_args()
    if args.worker:
        answer = worker(json.load(sys.stdin))
    else:
        cases = tuple(requests())
        with ThreadPoolExecutor(max_workers=4) as pool:
            records = dict(zip((case["case"] for case in cases), pool.map(isolated, cases), strict=True))
        answer = {"workers": len(cases), "records": records}
        if args.before:
            baseline = json.loads(args.before.read_bytes())
            assert baseline["workers"] == len(cases)
            answer["compared"] = compare(cases, baseline["records"], records)
    print(json.dumps(answer, sort_keys=True, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
