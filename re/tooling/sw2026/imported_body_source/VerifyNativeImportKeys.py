from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
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
from convert.Geometry.Parasolid import DecodeBrepModel
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
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
    KeywordsStream,
)
from convert.adapters.solidworks.Core.Adapter import (
    KSourceSemanticShaTwoFive,
    NativePartModel,
    SemanticShaTwo,
)
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseXml
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import (
    ReadLightInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import (
    ReadNotesInput,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import (
    ReadLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.FindLocalOwner import (
    FindLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import (
    ReadLocalWrap,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalKeys import (
    ReadLocalKeys,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalPay,
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
TOPOLOGY_BASE = "c0b962453fd467d8a807aff3629351536a018dc2"
BODY_BINDER = (
    "src/convert/adapters/solidworks/Core/TypedResolved/BodyNames/BindBodyName.py"
)
BUILD = "728ab68458024189e9a6d54530a801c34e07985d53d73c5e7f2bae90f1dba1e4"
SAVED_BUILD = "9c2625cc8a1eb59e60e3dacf835c304479bd3b3a690156ad181fc97cf3740f32"
SAVED_NATIVE = "767e3f65aa98d85a1aa8ac2ce4eaf416a70e4b2d369662a9c2f5e243700a6249"
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
        "Archive/Construction/Metadata/KeywordConfig.py",
    )
) + (BODY_BINDER,)


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
    wire_material = config.properties.get("Material")
    require(
        ReadLocalKeys(archive) == (True, source_id),
        "source keyword index does not bind its actual import",
    )
    require(
        not document.materials
        and root.attrib["Name"] == ReadNodeName(linked.ConfigValue.RootValue)
        and wire_material in (None, material)
        and document.configurations[0].attributes["native_properties"].get("Material")
        == wire_material,
        "source title or unassigned material differs from its physical owners",
    )
    return (
        ImportKeyInput(root.attrib["Name"], int(root.attrib["id"]), wire_material),
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
        and config.properties.get("Material") == keyword.MaterialValue,
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
        "empty_material",
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
        elif change == "empty_material":
            config.set("Material", "")
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


def reject_nonempty_material(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (folder,) = (
        node
        for node in link.ResolvedValue.RootsValue
        if node.ClassValue.NameValue == "moMaterialFolder_c"
    )
    folder.FieldsValue["f378"] = "Explicit Alloy"
    resolved = link.ResolvedValue
    data, _ = WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        19000,
        link.ConfigValue.MapValue,
        resolved.ContextValue,
    )
    malformed = using_streams(archive, {link.StreamName: data})
    typed = ReadNativeLink(malformed, 0)
    (folder,) = (
        node
        for node in typed.ResolvedValue.RootsValue
        if node.ClassValue.NameValue == "moMaterialFolder_c"
    )
    require(
        folder.FieldsValue["f378"] == "Explicit Alloy"
        and ReadLocalKeys(malformed) == (True, None)
        and FindLocalOwner(NativePartModel(malformed, None), malformed) is None,
        "missing material admitted an unproven physical material owner",
    )


def generated_omission(source, destination, present):
    inputs, lights, notes, keyword, _, _ = prepare_inputs(source, destination)
    omitted = render(inputs, lights, notes, replace(keyword, MaterialValue=None), True)
    archive = SldprtArchive.from_bytes(omitted.BytesValue)
    prior = SldprtArchive.from_bytes(present)
    old = ParseXml(prior.require(KeywordsStream))
    del old[0].attrib["Material"]
    changed = sorted(
        name
        for name in archive.streams.keys() | prior.streams.keys()
        if archive.get(name) != prior.get(name)
    )
    require(
        changed == [KeywordsStream]
        and archive.require(KeywordsStream) == FrameKeywords(old, True)
        and ReadLocalKeys(archive) == (True, 18),
        "explicit omission changed data beyond the configuration label",
    )
    try:
        render(
            inputs, lights, notes, replace(keyword, MaterialValue="Contradictory"), True
        )
    except ValueError as error:
        require(
            "material differs" in str(error),
            "contradictory input failed outside the material guard",
        )
    else:
        raise ValueError("constructor accepted a contradictory explicit material label")
    reject_nonempty_material(omitted.BytesValue)
    return {
        "file_sha256": digest(omitted.BytesValue),
        "material_present": False,
        "changed_streams": changed,
        "bound_import_id": 18,
        "contradictory_input_refused": True,
        "nonempty_material_owner_refused": True,
    }


def previous_body_binder():
    source = subprocess.check_output(
        ["git", "show", f"{TOPOLOGY_BASE}:{BODY_BINDER}"], cwd=ROOT
    )
    scope = {}
    exec(compile(source, BODY_BINDER, "exec"), scope)
    return scope["BindBodyName"], digest(source)


def read_with_binders(raw, module, previous_binder):
    current_binder = module.BindBodyName
    with guard_build():
        current = decode_import(raw)
        try:
            module.BindBodyName = previous_binder
            previous = decode_import(raw)
        finally:
            module.BindBodyName = current_binder
    return previous, current


def ordinary_local_model(document):
    ordinary_models = tuple(
        (payload.source_stream, model)
        for payload in document.brep_payloads
        if payload.data is not None
        and (model := DecodeBrepModel(payload.data)) is not None
    )
    require(
        tuple(stream for stream, _ in ordinary_models) == (KLocalBodyStream,),
        "replay requires one ordinary local stream decode",
    )
    return ordinary_models[0][1]


def replay_body_counts(raw, module, previous_binder, feature_id):
    previous, document = read_with_binders(raw, module, previous_binder)
    ordinary = ordinary_local_model(document)
    (before,) = previous.bodies
    (body,) = document.bodies
    (kernel_body,) = document.brep.bodies
    counts = {
        "solid_count": 1,
        "shell_count": 1,
        "face_count": 6,
        "edge_count": 12,
        "vertex_count": 8,
    }
    proof = document.metadata["solidworks.native_body_names"]
    prior_digest = previous.metadata[KSourceSemanticShaTwoFive]
    current_digest = document.metadata[KSourceSemanticShaTwoFive]
    normalized = replace(
        document,
        bodies=(replace(body, topology=before.topology),),
        metadata=dict(document.metadata) | {KSourceSemanticShaTwoFive: prior_digest},
    )
    require(
        before.topology.solid_count == 0
        and body.topology == replace(before.topology, **counts)
        and normalized == previous
        and prior_digest != current_digest
        and SemanticShaTwo(normalized) == prior_digest
        and SemanticShaTwo(document) == current_digest
        and replace(document.brep, bodies=ordinary.bodies) == ordinary
        and kernel_body.design_body_id == body.id
        and proof["profile"] == "current_single_local_solid_names"
        and proof["complete_brep_binding"]
        and proof["last_modifying_feature_id"] == feature_id
        and kernel_body.provenance == body.provenance
        and tuple(span.record_kind for span in body.provenance.spans)
        == ("typed-native-body-atom", "native-local-body"),
        "proved local projection changed more than the design body counts",
    )
    return document, {
        "file_sha256": digest(raw),
        "selected_stream": KLocalBodyStream,
        "design_body_id": body.id,
        "previous_solid_count": before.topology.solid_count,
        "topology": counts,
        "only_topology_counts_and_derived_digest_changed": True,
        "body_proof": dict(proof),
        "body_provenance": {
            "native_id": body.provenance.native_id,
            "spans": [
                {
                    "stream": span.stream,
                    "offset": span.offset,
                    "length": span.length,
                    "record_kind": span.record_kind,
                }
                for span in body.provenance.spans
            ],
        },
        "runtime_reads": 0,
    }


def missing_body_owner(archive, module, previous_binder):
    link = ReadNativeLink(archive, 0)
    resolved = link.ResolvedValue
    (feature,) = tuple(
        node
        for node in resolved.RootsValue
        if node.ClassValue.NameValue == "moBaseBody_c"
    )
    feature.FieldsValue["n494"] = 0
    feature.FieldsValue["f498"] = []
    changed, _ = WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        19000,
        link.ConfigValue.MapValue,
        resolved.ContextValue,
    )
    raw = BuildSldprt(
        dict(archive.streams) | {link.StreamName: changed},
        FormatVersion=archive.format_version,
    )
    malformed = SldprtArchive.from_bytes(raw)
    require(
        {
            name
            for name in archive.streams
            if archive.require(name) != malformed.require(name)
        }
        == {link.StreamName},
        "missing atom control changed other archive streams",
    )
    previous, document = read_with_binders(raw, module, previous_binder)
    ordinary = ordinary_local_model(document)
    local, mark = ReadLocalPay(
        document.brep_payloads, malformed.require(KPartitionStream)
    )
    group = ReadLocalWrap(malformed.require(KLocalBodyStream), local)
    owner_link = ReadNativeLink(malformed, 0)
    try:
        ReadLocalOwner(owner_link, group, mark)
    except ValueError as error:
        reason = str(error)
        require(
            reason == "local body atom identities disagree",
            "control hit a different guard",
        )
    else:
        raise ValueError("local counts admitted a missing atom reference")
    (body,) = document.bodies
    require(
        document == previous
        and document.brep == ordinary
        and body.topology.solid_count == 0
        and "solidworks.native_body_names" not in document.metadata,
        "ordinary geometry or counts changed without native ownership proof",
    )
    return {
        "control_sha256": digest(raw),
        "changed_stream": link.StreamName,
        "selected_stream": KLocalBodyStream,
        "storage_key": group,
        "rollback_mark": mark,
        "reason": reason,
        "design_body_id": body.id,
        "solid_count": body.topology.solid_count,
        "ordinary_document_unchanged": True,
        "runtime_reads": 0,
    }


def replay_saved_packet(packet, source_packet):
    native = json.loads(checked(packet / "Native.json", SAVED_NATIVE))
    build = json.loads(checked(packet / "Build.json", SAVED_BUILD))
    require(
        native["controls_healthy"] and native["distinct_native_processes"] == 11,
        "saved packet controls or native process inventory changed",
    )
    module = import_module(
        "convert.adapters.solidworks.Core.TypedResolved.BodyNames.WithBodyNames"
    )
    previous_binder, previous_binder_sha = previous_body_binder()
    reports = {}
    for name, source_sha in SOURCES.items():
        source = checked(source_packet / "Sources" / f"{name}.SLDPRT", source_sha)
        saved_sha = native["observations"][name + "Generated"]["saved_sha256"]
        raw = checked(packet / "SavedCopies" / f"{name}.SLDPRT", saved_sha)
        archive = SldprtArchive.from_bytes(raw)
        link = ReadNativeLink(archive, 0)
        _, source_topology = replay_body_counts(source, module, previous_binder, 26)
        document, saved_topology = replay_body_counts(raw, module, previous_binder, 18)
        index, saved_roles, owners = project_index(archive, link, document)
        actual = FindLocalOwner(NativePartModel(archive, None), archive)
        destination = PureWindowsPath(build[name]["native_path"])
        present, candidate = compare_case(source, None, destination)
        (present_config,), present_rows = ParseKeywords(
            SldprtArchive.from_bytes(present).require(KeywordsStream)
        )
        require(
            digest(present) == build[name]["file"]["sha256"]
            and present_config.properties["Material"] == candidate["config_material"]
            and saved_roles == roles(present_rows)
            and len(saved_roles) == 25,
            "saved replay changed role parity or the frozen present candidate",
        )
        require(
            index.MaterialValue is None
            and index.TitleValue == destination.stem
            and index.SavedAt == EPOCH
            and actual is not None
            and actual.object_id == 18
            and len(document.brep.bodies) == 1
            and document.bodies[0].final_feature_id == "sldprt:feature:18",
            "saved omission did not retain its actual import and normalized index identity",
        )
        reports[name] = {
            "saved_sha256": saved_sha,
            "present_candidate_sha256": digest(present),
            "strict_brep_bodies": len(document.brep.bodies),
            "bound_import_id": actual.object_id,
            "material_present": False,
            "keyword_title": index.TitleValue,
            "keyword_epoch": index.SavedAt,
            "roles_equal": True,
            "keyword_rows": len(saved_roles),
            "owner_ids": owners,
            "source_topology": source_topology,
            "saved_topology": saved_topology,
        }
        if name == "Disclosed":
            omission = generated_omission(source, destination, present)
            omitted_owner = missing_body_owner(archive, module, previous_binder)
    return {
        "native_receipt_sha256": SAVED_NATIVE,
        "build_sha256": SAVED_BUILD,
        "cases": reports,
        "model_only_omission": omission,
        "topology_baseline_revision": TOPOLOGY_BASE,
        "topology_baseline_binder_sha256": previous_binder_sha,
        "missing_body_owner": omitted_owner,
    }


def main():
    parser = ArgumentParser(
        description="Verify the disclosed import keyword index and model-only stream deltas"
    )
    parser.add_argument("packet", type=Path)
    parser.add_argument("--saved-packet", type=Path)
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
    if args.saved_packet is not None:
        data["saved_material_replay"] = replay_saved_packet(
            args.saved_packet, args.packet
        )
    print(json.dumps(data, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
