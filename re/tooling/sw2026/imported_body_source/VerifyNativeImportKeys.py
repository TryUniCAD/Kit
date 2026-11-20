from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [
    str(ROOT / "src"),
    str(ROOT),
    str(TOOLS),
    str(TOOLS.parent),
    str(TOOLS.parent / "serial"),
]

from BuildImportedLocalPart import EPOCH
from ProjectDisclosedImport import decode_import, project_import, rectangular_boundary
from ProjectImportedSemantics import (
    project_import_semantics,
    project_part_text,
    read_empty_file_owner,
)
from VerifyBareImportPackage import BareLabels, guard_build, recipe
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportKeyInput import (
    ImportKeyInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import (
    MakeBareImport,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImpKeyNodes import (
    ReadImpKeyNodes,
)
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseXml
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import (
    ReadLightInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import (
    ReadNotesInput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.FindLocalOwner import (
    FindLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalKeys import (
    ReadLocalKeys,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadLocalExpl import (
    ReadLocalExpl,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange import CadDocument
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource

BASE = "1b70d67b854814cb5066f44028439c43f2b4a632"
BUILD = "728ab68458024189e9a6d54530a801c34e07985d53d73c5e7f2bae90f1dba1e4"
SOURCES = {
    "Disclosed": "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325",
    "OtherShape": "8c77ddcd2451466781ae153b7724808f4e9bbf102ebd14aab6cd6b9274870f1d",
    "RenamedFeature": "660277a250a8c719705d6332cfc1f3713ccc5082d07de2ad5c3006279c1f20e8",
}
OWNERS = tuple(
    "src/convert/adapters/solidworks/" + path
    for path in (
        "Archive/Construction/Metadata/MakeKeywords.py",
        "Archive/Construction/Part/Imports/ImportKeyInput.py",
        "Archive/Construction/Part/Imports/MakeBareImport.py",
        "Archive/Construction/Part/Imports/MakeImportKeys.py",
        "Archive/Construction/Part/Imports/ReadImpKeyNodes.py",
        "Core/TypedResolved/Geometry/LocalBody/FindLocalOwner.py",
        "Core/TypedResolved/Geometry/LocalBody/ReadLocalKeys.py",
    )
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    require(digest(raw) == expected, f"disclosed input hash changed for {path.name}")
    return raw


def project_index(archive, linked, document):
    data = archive.require(KeywordsStream)
    root = ParseXml(data)
    (config,), feature_rows = ParseKeywords(data)
    owners, expected_rows, material = ReadImpKeyNodes(
        linked.ConfigValue.RootValue, linked.ResolvedValue.RootsValue
    )
    (import_owner,) = (
        node for node in owners if node.ClassValue.NameValue == "moBaseBody_c"
    )
    (manager,) = (
        node for node in owners if node.ClassValue.NameValue == "moPrtExplViewManager_c"
    )
    source_id = NativeNodeId(import_owner)
    require(
        ReadLocalKeys(archive) == (True, source_id),
        "source keyword index does not bind its actual import",
    )
    require(
        not document.materials
        and root.attrib["Name"] == ReadNodeName(linked.ConfigValue.RootValue)
        and config.properties["Material"] == material
        and document.configurations[0].attributes["native_properties"]["Material"]
        == material,
        "source title or unassigned material differs from its physical owners",
    )
    return (
        ImportKeyInput(root.attrib["Name"], int(root.attrib["id"]), material),
        roles(feature_rows),
        {
            "import_id": source_id,
            "import_map_index": import_owner.IndexValue,
            "manager_id": NativeNodeId(manager),
            "manager_map_index": manager.IndexValue,
            "indexed_owners": len(expected_rows),
        },
    )


def roles(rows):
    return sorted((row.xml_tag, row.properties["Type"], row.name) for row in rows)


def prepare_inputs(raw, destination):
    original = decode_import(raw)
    footprint = project_import(original)
    semantics = project_import_semantics(original)
    archive = SldprtArchive.from_bytes(raw)
    linked = ReadNativeLink(archive, 0)
    keyword, expected_rows, identities = project_index(archive, linked, original)
    root = linked.ConfigValue.RootValue
    require(
        ReadLocalExpl(linked) is not None and not semantics.body_name_is_authored,
        "source differs from the disclosed empty-manager derived-body profile",
    )
    lights = tuple(map(ReadLightInput, ReadChildren(root.FieldsValue["f1e0"])))
    (cabinet,) = (
        node
        for node in linked.ResolvedValue.RootsValue
        if node.ClassValue.NameValue == "moDetailCabinet_c"
    )
    notes = ReadNotesInput(ReadChildren(cabinet))
    read_empty_file_owner(raw)
    text = replace(
        project_part_text(original, preserve_empty=True), HasEmptyFileOwner=True
    )
    labels = BareLabels(
        destination.stem, semantics.configuration_name, semantics.feature_name
    )
    neutral = CadDocument(
        CadSource("kit.neutral", "", ""),
        (Configuration("active", semantics.configuration_name, True),),
        (),
        (),
        (),
        (),
        (),
        (),
        brep=footprint.model,
    )
    return (
        (neutral, recipe(labels, destination, EPOCH, text), labels),
        lights,
        notes,
        keyword,
        expected_rows,
        identities,
    )


def render(inputs, lights, notes, keyword, exploded):
    with guard_build() as audit:
        result = MakeBareImport(
            *inputs,
            LightValues=lights,
            NotesValue=notes,
            HasEmptyExplodedView=exploded,
            KeywordInput=keyword,
        )
    require(
        not audit.DeniedReads, "keyword construction attempted a runtime input read"
    )
    return result


def compare_case(raw, previous, destination, *, exploded=True):
    inputs, lights, notes, keyword, expected_roles, source_identities = prepare_inputs(
        raw, destination
    )
    legacy = render(inputs, lights, notes, None, exploded)
    native = render(inputs, lights, notes, keyword, exploded)
    repeat = render(inputs, lights, notes, keyword, exploded)
    require(
        native.BytesValue == repeat.BytesValue,
        "new keyword composition is not deterministic",
    )
    if previous is not None:
        require(
            legacy.BytesValue == previous,
            "legacy generation differs from its frozen same-locator candidate",
        )
    changed = sorted(
        name
        for name in legacy.StreamsValue.keys() | native.StreamsValue.keys()
        if legacy.StreamsValue.get(name) != native.StreamsValue.get(name)
    )
    require(changed == [KeywordsStream], "index policy changed another logical stream")
    older_archive = SldprtArchive.from_bytes(legacy.BytesValue)
    archive = SldprtArchive.from_bytes(native.BytesValue)
    link = ReadNativeLink(archive, 0)
    raw_rows = archive.require(KeywordsStream)
    (config,), features = ParseKeywords(raw_rows)
    root = ParseXml(raw_rows)
    expected = (
        expected_roles
        if exploded
        else [row for row in expected_roles if row[1] != "Exploded Views"]
    )
    require(
        roles(features) == expected
        and raw_rows == FrameKeywords(root, True)
        and [(row.xml_tag, str(row.object_id)) for row in features]
        == sorted((row.xml_tag, str(row.object_id)) for row in features),
        "new roles, names, physical owner projection or framing differ from the source",
    )
    require(
        root.attrib == {"Name": keyword.TitleValue, "id": str(keyword.SavedAt)}
        and config.properties["Material"] == keyword.MaterialValue,
        "index-specific metadata differs from the explicit source input",
    )
    model = NativePartModel(archive, None)
    owner = FindLocalOwner(model, archive)
    old = FindLocalOwner(NativePartModel(older_archive, None), older_archive)
    require(
        owner is not None
        and old is not None
        and owner.object_id == old.object_id
        and ReadLocalKeys(archive) == (True, owner.object_id)
        and ReadLocalKeys(older_archive) == (False, None),
        "native and legacy paths changed their selected import identity",
    )
    document = decode_import(native.BytesValue)
    (body,) = document.bodies
    require(
        body.final_feature_id == f"sldprt:feature:{owner.object_id}"
        and body.topology.solid_count == 1
        and rectangular_boundary(document.brep, body.id).limits
        == rectangular_boundary(inputs[0].brep).limits,
        "indexed import lost its ordinary strict local-body binding",
    )
    manager = ReadLocalExpl(link)
    require((manager is not None) == exploded, "keyword style changed manager presence")
    part_name = ReadNodeName(link.ConfigValue.RootValue)
    require(part_name == destination.stem, "index title changed the binary part name")
    (typed_import,) = (
        node
        for node in link.ResolvedValue.RootsValue
        if node.ClassValue.NameValue == "moBaseBody_c"
    )
    require(
        NativeNodeId(typed_import) == owner.object_id,
        "keyword index selected a foreign import",
    )
    return native.BytesValue, {
        "file_sha256": digest(native.BytesValue),
        "legacy_file_sha256": digest(legacy.BytesValue),
        "keys_sha256": digest(raw_rows),
        "keys_bytes": len(raw_rows),
        "keyword_rows": len(features),
        "binary_part_name": part_name,
        "keyword_title": keyword.TitleValue,
        "keyword_epoch": keyword.SavedAt,
        "config_material": keyword.MaterialValue,
        "config_id": config.object_id,
        "import_id": owner.object_id,
        "exploded": exploded,
        "import_map_index": typed_import.IndexValue,
        "manager_id": None if manager is None else NativeNodeId(manager),
        "manager_map_index": None if manager is None else manager.IndexValue,
        "binary_map_counts": [
            link.ConfigValue.MapValue.CounterValue,
            link.ResolvedValue.MapValue.CounterValue,
        ],
        "source_index_owners": source_identities,
        "strict_local_solid_count": body.topology.solid_count,
        "changed_streams": changed,
        "modes": {"legacy": False, "native": True},
        "legacy_reference_exact": None if previous is None else True,
        "runtime_reads": 0,
    }


def using_streams(archive, changes):
    return SldprtArchive.from_bytes(
        BuildSldprt(
            dict(archive.streams) | changes, FormatVersion=archive.format_version
        )
    )


def malformed_keys(raw):
    archive = SldprtArchive.from_bytes(raw)
    data = archive.require(KeywordsStream)
    roles_under_test = {"Imported", "Exploded Views", "Ambient", "Directional", "Notes"}
    mutations = (
        "stale_import_id",
        "stale_manager_id",
        "fabricated_manager_name",
        "omitted_light",
        "omitted_notes",
        "duplicate_light",
        "wrong_light_name",
        "wrong_origin_tag",
        "wrong_config_id",
        "misattached_config_name",
        "wrong_material",
        "missing_material",
        "empty_title",
        "noncanonical_epoch",
        "omitted_native_inventory",
        "omitted_inventory_with_class_row",
        "spaced_native_roles",
    )
    refused = []
    for change in mutations:
        root = ParseXml(data)
        config = root[0]
        rows = {
            kind: [row for row in root if row.get("Type") == kind]
            for kind in roles_under_test
        }
        if change == "stale_import_id":
            rows["Imported"][0].set("id", "26")
        elif change == "stale_manager_id":
            rows["Exploded Views"][0].set("id", "801")
        elif change == "fabricated_manager_name":
            rows["Exploded Views"][0].set("Name", "Exploded Views 25")
        elif change == "omitted_light":
            root.remove(rows["Ambient"][0])
        elif change == "omitted_notes":
            for row in rows["Notes"]:
                root.remove(row)
        elif change == "duplicate_light":
            root.insert(
                list(root).index(rows["Ambient"][0]), deepcopy(rows["Ambient"][0])
            )
        elif change == "wrong_light_name":
            rows["Directional"][0].set("Name", rows["Directional"][1].get("Name"))
        elif change == "wrong_origin_tag":
            next(row for row in root if row.get("Type") == "Origin").tag = "Feature"
        elif change == "wrong_config_id":
            config.set("id", "1")
        elif change == "misattached_config_name":
            config.set("Name", root.get("Name"))
        elif change == "wrong_material":
            config.set("Material", root.get("Name"))
        elif change == "missing_material":
            del config.attrib["Material"]
        elif change == "empty_title":
            root.set("Name", "")
        elif change == "noncanonical_epoch":
            root.set("id", "0" + root.get("id"))
        elif change == "omitted_native_inventory":
            root[:] = [config, rows["Imported"][0]]
        elif change == "omitted_inventory_with_class_row":
            comments = next(row for row in root if row.get("Type") == "Comments")
            comments.set("Type", "moCommentsFolder_c")
            root[:] = [config, comments, rows["Imported"][0]]
        encoded = FrameKeywords(root, change != "spaced_native_roles")
        malformed = using_streams(archive, {KeywordsStream: encoded})
        model = NativePartModel(malformed, None)
        if change == "stale_import_id":
            require(
                next(row.object_id for row in model.features if row.kind == "Imported")
                == 18,
                "stale import case no longer exercises the legacy name repair",
            )
        require(
            ReadLocalKeys(malformed) == (True, None)
            and FindLocalOwner(model, malformed) is None,
            f"malformed canonical index admitted {change}",
        )
        refused.append(change)
    return refused


def malformed_physical_owner(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    config = link.ConfigValue
    resolved = link.ResolvedValue
    config.RootValue.FieldsValue["f13f8"] = None
    config_bytes, stored = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved_bytes, _ = WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        19000,
        stored.MapValue,
        resolved.ContextValue,
    )
    malformed = using_streams(
        archive, {link.ConfigName: config_bytes, link.StreamName: resolved_bytes}
    )
    cleaned = ReadNativeLink(malformed, 0)
    require(
        ReadLocalExpl(cleaned) is None
        and ReadLocalKeys(malformed) == (True, None)
        and FindLocalOwner(NativePartModel(malformed, None), malformed) is None,
        "keyword manager survived removal of its typed direct owner",
    )
    return "physical_manager_removed"


def prior_keyword_defaults():
    source = subprocess.check_output(["git", "show", f"{BASE}:{OWNERS[0]}"], cwd=ROOT)
    scope = {}
    exec(compile(source, OWNERS[0], "exec"), scope)
    cfg = (KeywordConfig(0, "Working", ""),)
    circle = (
        KeywordFeature(
            42,
            "Round",
            "Sketch",
            "Sketch",
            (KeywordDim("D1", 9, None),),
            (),
            None,
            None,
        ),
        KeywordFeature(
            43,
            "Boss",
            "Boss-Extrude",
            "Extrusion",
            (KeywordDim("D1", 4, None),),
            (),
            None,
            None,
        ),
    )
    revolve = (
        KeywordFeature(33, "Profile", None, "Sketch", (), (), True, None),
        KeywordFeature(
            34,
            "Wheel",
            "Revolve",
            "Feature",
            (KeywordDim("D1", 130, "degree"),),
            (33,),
            None,
            None,
        ),
    )
    results = {}
    for label, rows in (
        ("blind_circle_keywords", circle),
        ("degree_revolve_keywords", revolve),
    ):
        earlier = scope["MakeKeywords"]("Derived Title", EPOCH, cfg, rows)
        current = MakeKeywords("Derived Title", EPOCH, cfg, rows)
        require(earlier == current, f"default recipe changed {label}")
        results[label] = digest(current)
    return results


def main():
    parser = ArgumentParser(
        description="Verify the disclosed import keyword index and model-only stream deltas"
    )
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(codec)
    baseline = json.loads(checked(args.packet / "Build.json", BUILD))
    reports = {}
    for name, checksum in SOURCES.items():
        source = checked(args.packet / "Sources" / f"{name}.SLDPRT", checksum)
        prev = checked(
            args.packet / "Candidates" / f"{name}.SLDPRT",
            baseline[name]["file"]["sha256"],
        )
        destination = PureWindowsPath(baseline[name]["native_path"])
        native, report = compare_case(source, prev, destination)
        reports[name] = report | {"source_sha256": checksum}
        if name == "Disclosed":
            refusals = malformed_keys(native) + [malformed_physical_owner(native)]
            _, no_manager = compare_case(source, None, destination, exploded=False)
    data = {
        "schema": "kit.sw2026.disclosed-native-import-index.v1",
        "build_reference_sha256": BUILD,
        "baseline_revision": BASE,
        "observer_sha256": digest(Path(__file__).read_bytes()),
        "source_sha256": {path: digest((ROOT / path).read_bytes()) for path in OWNERS},
        "cases": reports,
        "native_index_without_manager": no_manager,
        "refusals": refusals,
        "retained_default_streams": prior_keyword_defaults(),
        "oracle_processes": 0,
        "heldout_cases": 0,
    }
    print(json.dumps(data, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
