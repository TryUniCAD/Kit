from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import sys

from BuildImportedLocalPart import ImportedPartSemantics, batch, make_part, verify_part
from BuildLocalBodyKernel import prism_model
from CheckPartTextReading import native_expected
from LocalBodyKernel import fingerprint, require
from ProjectDisclosedImport import active_configuration, decode_import, feature_type, project_import, rectangular_boundary
from ProjectImportedSemantics import project_import_semantics, project_part_text, read_local_names
from VerifyDisclosedImport import DISCLOSED
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Properties.CheckEmptyProps import CheckEmptyProps
from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropRoot
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadPartText import ReadPartText
from interchange import CadDocument
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ROOT = Path(__file__).resolve().parents[4]
TARGET = PureWindowsPath(r"C:\Kit\ImportedSemantics")
PROPERTY_STREAMS = ("docProps/core.xml", "docProps/custom.xml", "docProps/Config-0-Properties.xml")
CIRCLE = ("CircularProperties", "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23")
ADVANCED = ("RectangleProperties", "4377bf5680f30d1c9de52227928911e55604a75d30ceb987240df00d6b1b1805")
CIRCLE_ORACLE = "2d3e7c0fdb5e32d482e5fde77b7b8359bbed07dda8e937856fb3979c49e3ee7c"
MANAGER_STREAM = "Contents/CusProps"
MANAGER_HASH = "22ecc7dd4564532e71f54ca4b59e9aee9c6e98c62a2f9c7fecc6fe72d793134e"


def digest(value):
    raw = json.dumps(ToData(value), sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
    return sha256(raw).hexdigest()


def read_immutable(path, expected):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, "disclosed source SHA-256 differs")
    return raw


def reject(callback, expected):
    try:
        callback()
    except ValueError as error:
        require(expected in str(error), "refusal did not identify its expected owner: " + str(error))
        return str(error)
    raise ValueError("unsupported case emitted a result: " + expected)


def other_source_fields(document):
    attrs = {key: value for key, value in document.metadata.items()
             if key not in ("solidworks.part_text_properties", "document_summary", "custom_properties",
                            "solidworks_source_semantic_sha256")}
    configs = tuple(replace(config, attributes={key: value for key, value in config.attributes.items()
                                               if key != "custom_properties"})
                    for config in document.configurations)
    diagnostics = tuple(item for item in document.diagnostics if item.code != "solidworks.part_text_properties_unavailable")
    return digest(replace(document, metadata=attrs, configurations=configs, diagnostics=diagnostics))


def bags(props):
    return {"summary": dict(props.SummaryFields), "document": dict(props.DocumentFields),
            "configuration": dict(props.ConfigurationFields)}


def native_rows(packet):
    rows, inputs, documents = {}, {}, {}
    for role, (relative, expected) in DISCLOSED.items():
        path = packet / relative
        raw = read_immutable(path, expected)
        document = decode_import(raw)
        archive = SldprtArchive.from_bytes(raw)
        manager_stream = archive.require(MANAGER_STREAM)
        manager = ReadPropRoot(manager_stream, 19000)
        container = manager.FieldsValue["f20"][0]["o"].FieldsValue
        row = {"source_sha256": expected, "all_other_sdk_fields_sha256": other_source_fields(document),
               "all_sdk_fields_sha256": digest(document), "feature_timeline_sha256": digest(document.feature_timeline),
               "brep_sha256": digest(document.brep), "brep_payloads_sha256": digest(document.brep_payloads),
               "manager": fingerprint(manager_stream), "cut_list_is_absent": container["f10"] is None,
               "properties": bags(project_part_text(document)),
               "property_streams": {key: fingerprint(archive.require(key)) for key in PROPERTY_STREAMS},
               "source_unchanged": True}
        require(not any(row["properties"].values()), "native import property scopes are not empty")
        if role != "Control":
            require(row["cut_list_is_absent"] and row["manager"]["sha256"] == MANAGER_HASH,
                    "native import lacks its exact empty nullable manager")
            semantic = project_import_semantics(document)
            geometry = project_import(document)
            require(semantic.feature_name == geometry.feature_name and semantic.configuration_name == geometry.configuration_name,
                    "name and geometry source owners differ")
            inputs[role] = (replace_input(geometry.model, semantic.configuration_name), semantic)
            row.update(feature_name=semantic.feature_name, body_name=semantic.body_name,
                       body_name_is_authored=semantic.body_name_is_authored)
        require(read_immutable(path, expected) == raw, "disclosed source changed during observation")
        rows[role], documents[role] = row, document
    return rows, inputs, documents


def property_source_rows(packet):
    result = {}
    for role, expected in (CIRCLE, ADVANCED):
        folder = packet / "PartPropertySource01" / "Inspection" / (role + "Author")
        path = folder / (role + ".SLDPRT")
        raw = read_immutable(path, expected)
        document = decode_import(raw)
        if role == CIRCLE[0]:
            recorded = native_expected(folder / "Record.json")
            require(recorded["expected_record_sha256"] == CIRCLE_ORACLE, "independent native property observation changed")
            actual = bags(project_part_text(document))
            require(actual == {"summary": recorded["summary"], "document": recorded["document"],
                               "configuration": recorded["configured"]},
                    "SDK text values differ from independent native observation")
            result[role] = {"source_sha256": expected, "native_author_sha256": CIRCLE_ORACLE,
                            "projected_property_counts": {key: len(bag) for key, bag in actual.items()}}
        else:
            error = reject(lambda: project_part_text(document), "no complete compatible projection")
            result[role] = {"source_sha256": expected, "refusal": error,
                            "native_property_diagnostic": document.metadata["solidworks.part_text_properties"]["diagnostic"]}
        require(read_immutable(path, expected) == raw, "disclosed property source changed during observation")
    return result


def replace_input(model, name):
    return CadDocument(CadSource("kit.neutral", "", ""), (Configuration("active", name, True),),
                       (), (), (), (), (), (), brep=model)


def build(document, semantics, role):
    return make_part(document, str(TARGET / (role + ".SLDPRT")), "Owned", completed=True, semantics=semantics)


def observe_build(document, semantics, role):
    blob, streams = build(document, semantics, role)
    structure = verify_part(blob, streams)
    native = decode_import(blob)
    feature, = (entry for entry in native.feature_timeline if entry.kind == "imported" and feature_type(entry) == "Imported")
    body, = native.bodies
    config = active_configuration(native)
    require(body.final_feature_id == feature.id, "generated body lost its actual source feature owner")
    require((feature.name, read_local_names(native, feature, body), config.name)
            == (semantics.feature_name, (semantics.body_name, semantics.body_name_is_authored), semantics.configuration_name),
            "generated typed local label owners disagree with their neutral inputs")
    require(rectangular_boundary(native.brep, body.id) == rectangular_boundary(document.brep),
            "generated name or text changed the input geometry")
    readback = ReadPartText(native, SldprtArchive.from_bytes(blob))
    actual = {"summary": readback.SummaryFields or {}, "document": readback.DocumentFields or {},
              "configuration": readback.ConfigFields.get(0, {})}
    require(actual == bags(semantics.properties), "generated property owners disagree with their neutral inputs")
    if any(actual.values()):
        require(project_part_text(native) == semantics.properties, "public sdk omitted a generated text field")
    return streams, {"part": fingerprint(blob), "neutral_sha256": digest((document, semantics)),
                     "feature": structure["feature"], "body": body.name, "configuration": config.name,
                     "properties": {key: len(value) for key, value in actual.items()},
                     "property_streams": {key: fingerprint(streams[key]) for key in PROPERTY_STREAMS if key in streams}}


def neutral_positives(document):
    scope = {"Finish": "shop & inspect", "Order Ref": "C-917"}
    configured = {"Finish": "position <2> Ω", "Disposition": "Inspect"}
    summary = {"title": "Local transfer study", "comments": "Model Δ47"}
    label = "Transfer neutral Δ47"
    config, = document.configurations
    metadata = ImportedPartSemantics(label, label, False, config.name, PartTextInput(summary, scope, configured))
    alternate_doc = replace(metadata, properties=replace(metadata.properties,
                            DocumentFields={**scope, "Finish": "independently revised shop finish"}))
    alternate_config = replace(metadata, properties=replace(metadata.properties,
                               ConfigurationFields={**configured, "Finish": "independently revised fixture finish"}))
    base, result = observe_build(document, metadata, "NeutralText")
    changes = {}
    for alternate, stream in ((alternate_doc, PROPERTY_STREAMS[1]), (alternate_config, PROPERTY_STREAMS[2])):
        modified, evidence = observe_build(document, alternate, "NeutralText")
        changed = {key for key in {*base, *modified} if base.get(key) != modified.get(key)}
        require(changed == {stream} and len(base[stream]) != len(modified[stream]),
                "a literal property edit affected another owner or fixed the wire length")
        changes[stream] = evidence["property_streams"][stream]
    return metadata, result | {"edited_only_streams": changes}


def neutral_negatives(document, metadata, authored_value, source_document):
    def mutated_props(**change):
        return replace(metadata, properties=replace(metadata.properties, **change))

    def malformed(name, value):
        return mutated_props(DocumentFields={name: value})

    wrong_owner = replace(document, configurations=(replace(document.configurations[0], attributes={"appearance": "unsupported"}),))
    source_body, = source_document.bodies
    forged_source = replace(source_document, bodies=(replace(source_body, name="Detached label"),))
    builds = (
        ("number", document, malformed("Finish", 2), "explicit xml text"),
        ("formula", document, malformed("Finish", "=2+2"), "literal unlinked"),
        ("link", document, malformed("Finish", "$PRP:Other"), "literal unlinked"),
        ("duplicate_name", document, mutated_props(ConfigurationFields={"Name": "one", "name": "two"}), "distinct within a scope"),
        ("unknown_summary", document, mutated_props(SummaryFields={"extra": "other"}), "unsupported field"),
        ("malformed_summary_bag", document, mutated_props(SummaryFields=[]), "three typed literal text bags"),
        ("unowned_configuration_data", wrong_owner, metadata, "without unowned fields"),
        ("wrong_configuration", document, replace(metadata, configuration_name="Reassigned"), "selected neutral configuration"),
        ("unequal_derived_label", document, replace(metadata, body_name="Dedicated size"), "must agree with the actual feature"),
        ("unqualified_native_authored_body", authored_value[0], authored_value[1], "qualified compatibility carrier"),
    )
    return {role: reject(lambda: build(model, semantics, "Rejected"), error) for role, model, semantics, error in builds} | {
        "detached_source_body_label": reject(lambda: project_import_semantics(forged_source), "does not match its native feature key")
    }


def check_cut_owner(packet):
    relative, expected = DISCLOSED["DisclosedImported"]
    raw = read_immutable(packet / relative, expected)
    stream = SldprtArchive.from_bytes(raw).require(MANAGER_STREAM)
    manager = ReadPropRoot(stream, 19000)
    owner = manager.FieldsValue["f20"][0]["o"].FieldsValue
    owner["f10"] = owner["f08"]
    wrong_class = reject(lambda: CheckEmptyProps(manager), "unexpected native owner")
    empty = {"n08": 0, "f08": [], "n38": 0, "f38": []}
    owner["f10"] = ArchiveNode(RuntimeClass("moCutListPropContainer_c", 1), empty | {"n38": 1, "f38": [{"key": 1, "o": None}]})
    populated = reject(lambda: CheckEmptyProps(manager), "populated advanced property manager")
    owner["f10"], owner["f08"] = None, None
    missing_file = reject(lambda: CheckEmptyProps(manager), "unexpected native owner")
    return {"wrong_cut_list_class": wrong_class, "populated_cut_list": populated, "missing_file_owner": missing_file}


def measure(packet):
    source_rows, inputs, documents = native_rows(packet)
    property_rows = property_source_rows(packet)
    cut_negatives = check_cut_owner(packet)
    legacy, legacy_denied = batch(TARGET / "Legacy", completed=True)
    for codec in ("ascii", "utf-16-le", "utf-8", "latin-1"):
        lookup(codec)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    running = True

    def guard(event, args):
        if running:
            audit.InspectEvent(event, args)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError("imported part computation reached " + event)

    sys.addaudithook(guard)
    try:
        candidates = {role: observe_build(document, semantic, role)[1]
                      for role, (document, semantic) in inputs.items() if not semantic.body_name_is_authored}
        points = ((3., -7.), (22., -7.), (22., 5.), (3., 5.))
        neutral = replace_input(prism_model("neutral-text-solid", points, (2., 11.)), "Clearance A")
        metadata, synthetic = neutral_positives(neutral)
        rejections = neutral_negatives(neutral, metadata, inputs["RenamedBody"], documents["DisclosedImported"])
    finally:
        running = False
    require(not audit.DeniedReads and not legacy_denied, "generated outputs attempted a runtime source read")
    return {"schema": "kit.sw2026.imported-local-part-semantics.v1", "oracle_version_of_disclosed_sources": "34.5.2.0604",
            "disclosed_imports_and_control": source_rows, "property_sources": property_rows,
            "cut_owner_refusals": cut_negatives, "generated_source_scope_candidates": candidates,
            "independent_neutral_text": synthetic, "source_and_neutral_refusals": rejections,
            "unchanged_geometry_path_candidates": {key: fingerprint(blob) for key, (blob, _) in legacy.items()},
            "construction_denied_reads": len(audit.DeniedReads) + legacy_denied, "heldout_sources_read": 0,
            "native_candidate_runs": 0, "public_import_writer_changes": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure disclosed import labels and literal part text ownership offline")
    parser.add_argument("disclosed_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.disclosed_root), indent=2, ensure_ascii=False, sort_keys=True))
