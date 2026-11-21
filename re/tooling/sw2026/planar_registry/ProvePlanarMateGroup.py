from argparse import ArgumentParser
from dataclasses import replace
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PlanarRegistryBuild import ROOT, file_sha, fingerprint, require, write


BASE = "1f2130d9fcf4f3fa4abdf8b0af0a6c4c018cdb58"
LOCK = "8f79ed2aa8559b7186f414330b495ce50c4fa3612f69d421bbd7bc83037ca417"
SEMANTIC_SEAL = "solidworks_source_semantic_sha256"
TOOL = Path(__file__).resolve()
MATES = "Contents/Config-0-MatesList"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
LAYOUT = "src/convert/adapters/solidworks/Config/RootLayout.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()


def checked(path, digest):
    value = path.read_bytes()
    require(fingerprint(value)["sha256"] == digest, "source identity differs: " + path.name)
    return value


def source_cases(base):
    lock = ROOT / "re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json"
    public = json.loads(checked(lock, LOCK))
    entries = {row["name"][:3]: row for row in public["cases"]}
    checked(base / "AssemblyMateSource02/SourceLock.json", public["private_source_lock_sha256"])
    sources = []
    for key in ("A20", "A21"):
        row = entries[key]
        packet = base / "AssemblyMateSource02" / row["name"] / "author"
        record = json.loads(checked(packet / "Record.json", row["record_sha256"][0]))
        saved = record["assembly_result"]["saved"]
        require(record["passed"] and record["job"]["phase"] == "author"
                and record["job"]["case"]["name"] == row["name"]
                and record["assembly_result"]["native_sha256"] == row["native_sha256"],
                "prior native evidence differs")
        group, = [node for node in saved["tree"] if node["type"] == "MateGroup"]
        children = [node for node in saved["tree"] if node["parent"] == group["name"]]
        require(group["parent"] is None and len(children) == 2
                and all(node["error"] == 0 and not node["warning"] and not node["suppressed"]
                        for node in (group, *children))
                and [node["name"] for node in children] == [mate["name"] for mate in saved["mates"]],
                "the earlier solver tree or native ordered members differ")
        child = row["synchronized_child"]
        sources.append({
            "case": key, "parent": str(packet / (row["name"] + ".SLDASM")),
            "parent_sha256": row["native_sha256"], "child": str(packet / child["path_basename"]),
            "child_sha256": child["native_sha256"], "native_record_sha256": row["record_sha256"][0],
            "native_group": group["name"], "native_members": [node["name"] for node in children],
        })
    return sources


def controls(base):
    planar = base / "PlanarPublicRegistry01"
    perpendicular = base / "PublicPerpendicularRegistry01"
    concentric = base / "ConcentricMateSourcePacket02/Disclosed/D01/Native/Source"
    pairs = (
        ("PlanarGenerated", planar / "FrozenGenerated", "PublicPlanarPair2", "PublicDatumPrism",
         "d31950eb971645908a82c26ecb881880525a3c8aa9478bc971b065bc5bdcf2f4",
         "b734fe2b8df59085860ae12f6dacabd363a4475f5399506efdce423d05c4ab7b"),
        ("PlanarSaved", planar / "GeneratedInput", "PublicPlanarPair2", "PublicDatumPrism",
         "ab1164708763381c3498ad8bc7b6841a09823f94bf52038685f67ad61902af56",
         "670d8a2fb9c9c03a643dceceb5ac35ce9c1c6095ba7384a08b48b0b710dc1702"),
        ("PerpendicularGenerated", perpendicular / "FrozenGenerated", "NeutralPerpPair", "NeutralPerpPrism",
         "0a740c7a632ad769174c3d145710ca68502c33d07f575ac02ccb583363293187",
         "86b6987dd8cd647e8c07067433ad41d08a7d7d0a257f2fc8956f4a747d4ed7e6"),
        ("PerpendicularSaved", perpendicular / "Saved", "NeutralPerpPair", "NeutralPerpPrism",
         "d0d873c121c150efe93e6ffb29a0b498ae8de4b2c4079d8b70af0ff54c548f51",
         "9b457e330949020af9d34a80b32d7df2fccd43b17aee0d623aa8723b6917a94c"),
        ("ConcentricSaved", concentric, "ConcentricD01AlignedFree", "ConcentricD01Child",
         "2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2",
         "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"),
    )
    return [
        {"case": case, "parent": str(folder / (parent + ".SLDASM")), "parent_sha256": parent_sha,
         "child": str(folder / (child + ".SLDPRT")), "child_sha256": child_sha,
         "read_refusal": (
             "typed planar mate graph rejected: perpendicular mate is outside the solved repeated part profile"
             if case == "PerpendicularGenerated" else None
         )}
        for case, folder, parent, child, parent_sha, child_sha in pairs
    ]


def guarding(root, inputs):
    roots = (root / "src", Path(sys.base_prefix).resolve())
    layout = root / LAYOUT
    reads = set()
    rules = set()
    denied = []

    def guard(event, args):
        if event == "open" and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve()
            if args[2] & (os.O_ACCMODE | os.O_CREAT | os.O_TRUNC) != os.O_RDONLY:
                denied.append("file mutation " + str(path))
                raise ValueError(denied[-1])
            if path in inputs:
                reads.add(path.name)
            elif path == layout:
                rules.add(LAYOUT)
            elif not (path.suffix in {".py", ".pyc", ".so"} and any(path.is_relative_to(folder) for folder in roots)):
                denied.append("extra input " + str(path))
                raise ValueError(denied[-1])
        if event.startswith(("socket.", "subprocess.", "ctypes.")) or event in {
            "os.system", "os.fork", "os.exec", "os.posix_spawn",
        }:
            denied.append("external operation " + event)
            raise ValueError(denied[-1])

    sys.addaudithook(guard)
    return reads, rules, denied


def inject(case, sdk):
    from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry

    target = import_module("convert.adapters.solidworks.Core.TypedMates.ReadPublicMates")
    if case in {"foreign-rule", "crossed-spans", "reordered-rules"}:
        original = target.ReadMateRows

        def read_rows(*args):
            entities, (first, second) = original(*args)
            return entities, {
                "foreign-rule": (first, replace(second, owner_definition_id="foreign")),
                "crossed-spans": (replace(first, provenance=second.provenance), second),
                "reordered-rules": (second, first),
            }[case]

        target.ReadMateRows = read_rows
        return
    if case == "detached-group":
        original_link = target.ReadNativeLink

        def read_link(*args):
            link = original_link(*args)
            resolved = link.ResolvedValue
            return replace(link, ResolvedValue=replace(
                resolved, RootsValue=tuple(node for node in resolved.RootsValue
                                           if node.ClassValue.NameValue != "moMateGroup_c")))

        target.ReadNativeLink = read_link
        return
    original_mates = target.ReadMatesMut

    def read_mates(*args):
        graph = original_mates(*args)
        (entry,) = [item for item in graph.MapValue.EntriesValue if isinstance(item.EntryValue, sdk["ArchiveNode"])
                    and item.EntryValue.ClassValue.NameValue == "moMateGroup_c"]
        node = entry.EntryValue
        if case == "ambiguous-group":
            snapshot = graph.MapValue
            index = snapshot.CounterValue
            alias = replace(node, IndexValue=index)
            return replace(graph, MapValue=sdk["MapSnapshot"](
                index + 1, (*snapshot.EntriesValue, MapEntry(index, alias))))
        if case == "crossed-slot":
            node.IndexValue += 1
        if case == "nested-group":
            folder, = [item.EntryValue for item in graph.MapValue.EntriesValue
                       if isinstance(item.EntryValue, sdk["ArchiveNode"])
                       and item.EntryValue.ClassValue.NameValue == "moEnvFolder_c"]
            former = folder.FieldsValue["f60"]["list"]
            former["items"].append({"o": node})
            former["n"] += 1
        if case == "inline-member":
            node.FieldsValue["f60"] = {"list": {"n": 1, "items": [{"o": graph.RootsValue[0]}]}, "tail": 0}
        if case == "group-ids":
            node.FieldsValue.update({"f4e8#count": 1, "f4e8": [{"v": graph.RootsValue[0].FieldsValue["f08"]}]})
        if case == "crossed-update":
            node.FieldsValue["f0c"] = 1
        return graph

    target.ReadMatesMut = read_mates


def group_evidence(data, sdk, doc):
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

    archive = sdk["SldprtArchive"].from_bytes(data)
    link = sdk["ReadNativeLink"](archive, 0)
    resolved = link.ResolvedValue
    graph = sdk["ReadMatesMut"](archive.require(MATES), resolved)
    group, = [node for node in resolved.RootsValue if node.ClassValue.NameValue == "moMateGroup_c"]
    output, _ = sdk["WriteMatesMut"](graph.RootsValue, resolved)
    resolved_bytes, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, resolved.VersionValue,
                                      link.ConfigValue.MapValue, resolved.ContextValue)
    require(output == archive.require(MATES) and resolved_bytes == archive.require(RESOLVED),
            "linked group or ordered mate list differs on typed re-emission")
    members = [{
        "native_id": node.FieldsValue["f08"], "name": ReadNativeName(node),
        "class": node.ClassValue.NameValue, "map_slot": node.IndexValue,
        "span": [node.StartOffset, node.EndOffset], "f0c": node.FieldsValue["f0c"],
    } for node in graph.RootsValue]
    (portable,) = doc.assembly.mate_groups
    root = doc.assembly.root_definition_id
    persistent = group.FieldsValue["f08"]
    span, = portable.provenance.spans
    require(portable.name == ReadNativeName(group) and portable.owner_definition_id == root
            and portable.id == f"{root}:mate-group:{persistent}"
            and not portable.parent_group_id and portable.order == 0
            and portable.provenance.native_id == str(persistent)
            and (span.stream, span.offset, span.length, span.record_kind)
            == (RESOLVED, group.StartOffset, group.EndOffset - group.StartOffset, "mate-group"),
            "the projected group is not the actual resolved owner")
    require(portable.mate_ids == tuple(rule.id for rule in doc.assembly.mates)
            and [rule.name for rule in doc.assembly.mates] == [row["name"] for row in members]
            and [int(rule.provenance.native_id) for rule in doc.assembly.mates] == [row["native_id"] for row in members],
            "the projected members differ from the separate ordered graph")
    return {
        "name": portable.name, "native_id": persistent, "map_slot": group.IndexValue,
        "span": [group.StartOffset, group.EndOffset], "resolved_ordinal": resolved.RootsValue.index(group),
        "f0c": group.FieldsValue["f0c"], "neutral_group": portable.id, "neutral_root": root,
        "neutral_mate_ids": list(portable.mate_ids), "ordered_members": members,
        "mate_map_base": graph.MapBase, "mate_map_terminal": graph.MapValue.CounterValue,
        "exact_typed_streams": {MATES: fingerprint(output), RESOLVED: fingerprint(resolved_bytes)},
    }


def worker(root, request):
    sys.path.insert(0, str(ROOT / "re/tooling/sw2026"))
    from SdkMatesProcess import load_sdk

    sdk = load_sdk(root)
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtFormatError
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import CheckAsmShape
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmGroup import ReadAsmGroup

    parent, child = (Path(request[role]).resolve(strict=True) for role in ("parent", "child"))
    data = checked(parent, request["parent_sha256"])
    checked(child, request["child_sha256"])
    if request.get("fault"):
        inject(request["fault"], sdk)
    reads, rules, denied = guarding(root, {parent, child})
    row = {}
    use_geometry = request["view"] == "default"
    try:
        doc = open_document(parent, include_brep=use_geometry, include_tessellation=use_geometry, strict=True)
    except SldprtFormatError as error:
        require(request.get("fault") or str(error) == request.get("read_refusal"),
                "unexpected strict read refusal: " + str(error))
        row["diagnostic"] = str(error)
    else:
        require(not request.get("read_refusal"), "an unsupported control passed the strict read")
        doc.assert_valid()
        require(len(doc.assembly.documents) == 1
                and doc.assembly.documents[0].document.source.sha256 == request["child_sha256"],
                "strict read did not resolve the actual child")
        status = doc.metadata["solidworks.typed_mates_semantics"]
        row["diagnostic"] = status.get("diagnostic")
        groups = doc.assembly.mate_groups
        row["group_count"] = len(groups)
        count = 0 if request.get("fault") or (request["before"] and request["case"] != "ConcentricSaved") else 1
        require(len(groups) == count and status["status"] == ("unsupported" if request.get("fault") else "admitted")
                and status["full_selected_mate_graph"] is (not request.get("fault"))
                and status["public_writer_qualified"] is False, "public read or scope differs")
        if groups:
            row["group"] = group_evidence(data, sdk, doc)
            if "native_members" in request:
                require(row["group"]["name"] == request["native_group"]
                        and [item["name"] for item in row["group"]["ordered_members"]] == request["native_members"],
                        "typed owners differ from prior native tree")
        if request["case"] in {"A20", "A21"} and not request.get("fault"):
            for key, action, wanted in (
                ("root_refusal", lambda: CheckAsmShape(doc), "assembly root contains unprojected model content"),
                ("group_refusal", lambda: ReadAsmGroup(doc.assembly, doc.assembly.root_definition_id),
                 "mate group has unprojected extensions" if groups else "one complete ordered mate group is required"),
            ):
                try:
                    action()
                except ValueError as error:
                    require(str(error) == wanted, "unexpected assembly writer refusal")
                    row[key] = str(error)
                else:
                    raise ValueError("unqualified source owner passed writer preparation")
        document = json.loads(doc.to_json(indent=None))
        row["document_sha256"] = fingerprint(canonical(document))["sha256"]
        document["assembly"].pop("mate_groups")
        row["derived_source_seal"] = document["metadata"].pop(SEMANTIC_SEAL)
        row["without_group_and_derived_seal_sha256"] = fingerprint(canonical(document))["sha256"]
    require(not any(name in {"Swapp", "pythoncom", "pywintypes"} or name.startswith("win32com") for name in sys.modules),
            "the guarded worker imported a CAD runtime")
    require(reads == {parent.name, child.name}, "guarded CAD input set differs")
    require(not denied, "guarded worker attempted unexpected operations: " + str(denied))
    return {**row, "pid": os.getpid(), "only_cad_inputs": sorted(reads), "reader_rule_files": sorted(rules)}


def run_worker(root, request):
    result = subprocess.run((sys.executable, "-I", "-B", str(TOOL), "--worker", "--root", str(root)),
                            input=canonical(request), capture_output=True, check=False, timeout=90)
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    return json.loads(result.stdout)


def batch(args):
    sys.path.insert(0, str(ROOT / "re/tooling/sw2026"))
    from ReadSdkOrderedNative import source_manifest

    root = args.root.resolve(strict=True)
    cases = source_cases(args.disclosed) + controls(args.disclosed)
    for request in cases:
        for role in ("parent", "child"):
            checked(Path(request[role]), request[role + "_sha256"])
    sources = source_manifest(root)
    layout_sha = file_sha(root / LAYOUT)
    pairs = []
    with TemporaryDirectory(prefix="KitPlanarMateGroupBaseline") as temporary:
        old = Path(temporary).resolve()
        bundle = subprocess.check_output(("git", "archive", BASE, "src"), cwd=root)
        with open_tar(fileobj=BytesIO(bundle)) as archive:
            archive.extractall(old, filter="data")
        checked(old / LAYOUT, layout_sha)
        for case in cases:
            views = ("metadata", "default") if case["case"] in {"A20", "A21"} else ("metadata",)
            for view in views:
                request = {**case, "view": view}
                before = run_worker(old, {**request, "before": True})
                after = run_worker(root, {**request, "before": False})
                if case.get("read_refusal"):
                    require(before["diagnostic"] == after["diagnostic"] == case["read_refusal"],
                            "the earlier strict refusal changed")
                else:
                    field = ("document_sha256" if case["case"] == "ConcentricSaved"
                             else "without_group_and_derived_seal_sha256")
                    require(before[field] == after[field], "the group read changed an unrelated neutral owner: "
                            + case["case"] + "/" + view)
                    require((before["derived_source_seal"] == after["derived_source_seal"])
                            is (case["case"] == "ConcentricSaved"), "the source seal does not bind the changed group")
                bounds = {key: value for key, value in case.items() if key.endswith("sha256")}
                pairs.append({"case": case["case"], "view": view, **bounds, "before": before, "after": after})
    faults = (
        ("ambiguous-group", "top-level native group"),
        ("detached-group", "top-level native group"),
        ("crossed-slot", "top-level native group"),
        ("nested-group", "top-level native group"),
        ("inline-member", "unsupported native state or contents"),
        ("group-ids", "unsupported native state or contents"),
        ("crossed-update", "unsupported native state or contents"),
        ("foreign-rule", "membership differs from the owned native list"),
        ("crossed-spans", "membership differs from the owned native list"),
        ("reordered-rules", "membership differs from the owned native list"),
    )
    negatives = []
    for case, reason in faults:
        result = run_worker(root, {**cases[0], "view": "metadata", "before": False, "fault": case})
        require(reason in result["diagnostic"], "the negative refused at a different gate")
        negatives.append({"fault": case, **result})
    pids = [item[phase]["pid"] for item in pairs for phase in ("before", "after")] + [item["pid"] for item in negatives]
    require(len(set(pids)) == len(pids), "process isolation was lost")
    for request in cases:
        for role in ("parent", "child"):
            checked(Path(request[role]), request[role + "_sha256"])
    require(source_manifest(root) == sources and file_sha(root / LAYOUT) == layout_sha,
            "SDK snapshot changed during verification")
    subject = "src/convert/adapters/solidworks/Core/TypedMates/"
    receipt = {
        "schema": "kit.sw2026.planar-mate-group-read.v1", "task": "B04-SW2026-MATES-PLANAR/saved-group-read",
        "delivery_pr": 121, "owner": "assembly_frontier", "passed": True, "base_revision": BASE,
        "tool_sha256": file_sha(TOOL), "source_manifest_sha256": fingerprint(canonical(sources))["sha256"],
        "root_layout_sha256": layout_sha,
        "source_files": {path: sources[subject + path] for path in (
            "ReadMateGroup.py", "ReadPublicMates.py", "Cylinders/ReadCylGroup.py",
        )},
        "prior_public_lock_sha256": LOCK, "comparisons": pairs, "in_memory_refusals": negatives,
        "fresh_sdk_processes": len(pids), "native_processes": 0, "additional_heldout_credit": 0,
        "unseen_heldout_reads": 0, "writer_outputs": 0, "source_inputs_unchanged": True,
    }
    print(write(args.output, receipt))


def main():
    parser = ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.root.resolve(strict=True), json.load(sys.stdin)), sort_keys=True))
    else:
        require(args.disclosed is not None and args.output is not None and not args.output.exists(),
                "use the disclosed base and an unused receipt path")
        batch(args)


if __name__ == "__main__":
    main()
