from argparse import ArgumentParser
from collections.abc import Mapping
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


ROOT = Path(__file__).resolve().parents[5]
BUILD = "34.5.2.0604"
EXE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
MODU = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
SRC = dict(
    import_solid=(
        "ImportedBodySourceDisclosed03/DisclosedImported.SLDPRT",
        "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325",
        "moBaseBody_c", "ImportedBaseBodySourcesNative01",
    ),
    circle_boss=(
        "PartPropertySource01/Inspection/CircularPropertiesAuthor/CircularProperties.SLDPRT",
        "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23",
        "moExtrusion_c", "PartPropertySources01",
    ),
    full_revolve=(
        "GeneratedOrdinaryRevolveNative01/Control/RevolveFull.SLDPRT",
        "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0",
        "moRevolution_c", "SdkOrdinaryRevolveNative01",
    ),
)
SCENE_ROLES = ("environment", "ambient", "directional_first", "directional_second", "directional_third")
NORM = frozenset(("f08", "f2a0", "f2a4"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def evidence(kind, identity, record):
    if kind == "import_solid":
        entry = record["packets"]["disclosed"]
        require(entry["controls_healthy"] and entry["passed"]
                and entry["sources"]["Disclosed"]["source_sha256"] == identity,
                "import source no longer matches its disclosed observation")
        version, module = entry["oracle_version"], entry["oracle_sha256"]
    elif kind == "circle_boss":
        require(record["controls_healthy"] and record["source_observed"]
                and record["cases"]["CircularProperties"]["save_sha256"] == identity,
                "circle source no longer matches its authored observation")
        version, module = record["native_version"], record["oracle_sha256"]
    else:
        require(len(record["controls"]) == 2
                and all(item["file_sha256"] == identity and item["healthy"] for item in record["controls"]),
                "revolve source no longer matches its healthy disclosed controls")
        version, module = record["oracle"]["version"], record["oracle"]["executable_sha256"]
    require((version, module) == (BUILD, EXE), "source observations must share the exact native build")


def typed_value(value, roles):
    if isinstance(value, ArchiveNode):
        if id(value) in roles:
            return {"linked_scene_member": roles[id(value)]}
        require(value.ClassValue == RuntimeClass("moNodeName_c", 1),
                "unexpected nested scene class needs separate field ownership")
        return {"class": "moNodeName_c", "schema": 1, "fields": typed_value(value.FieldsValue, roles)}
    if isinstance(value, Mapping):
        require(all(type(key) is str for key in value), "unexpected scene record key domain")
        return {key: typed_value(member, roles) for key, member in value.items()}
    if type(value) is tuple:
        return {"tuple": [typed_value(item, roles) for item in value]}
    if type(value) is list:
        return [typed_value(item, roles) for item in value]
    require(type(value) in (str, int, float, bool, type(None)), "unknown or opaque scene cell")
    return value


def actual_scene(archive, expected_feature):
    native = ReadNativeLink(archive, 0)
    root = native.ConfigValue.RootValue
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    selected = manager.FieldsValue["f360"]
    require(root.ClassValue == RuntimeClass("moPart_c", 1)
            and native.ConfigName == "Contents/Config-0"
            and selected is manager.FieldsValue["f368"] and selected.FieldsValue["f08"] == 0,
            "scene must belong to the actual selected ordinary part configuration")
    folder = root.FieldsValue["f1e0"]
    roots = native.ResolvedValue.RootsValue
    require(folder.ClassValue == RuntimeClass("moEnvFolder_c", 1)
            and sum(node is folder for node in roots) == 1
            and roots[-1].ClassValue == RuntimeClass(expected_feature, 1),
            "scene owner or unrelated model family disagrees with typed roots")
    list_fields = folder.FieldsValue["f60"]
    rows = list_fields["list"]["items"]
    members = tuple(row["o"] for row in rows)
    require(list_fields["list"]["n"] == len(members) == 4 and len({id(node) for node in members}) == 4
            and all(not any(node is member for node in roots) for member in members)
            and tuple(node.ClassValue.NameValue for node in members) == ("moAmbientLight_c",) + ("moDirectionLight_c",) * 3
            and all(node.ClassValue.SchemaValue == 1 for node in members),
            "scene member list has unexpected counts classes or aliases")
    return (folder, *members), {"model_title": ReadNodeName(root), "configuration_title": ReadNodeName(selected),
                                "terminal_feature": expected_feature}


def observe(path, identity, terminal):
    raw = path.read_bytes()
    require(digest(raw) == identity, "disclosed source SHA-256 changed")
    archive = SldprtArchive.from_bytes(raw)
    nodes, meta = actual_scene(archive, terminal)
    role_map = {id(node): role for role, node in zip(SCENE_ROLES, nodes, strict=True)}
    complete = {}
    semantic = {}
    for role, node in zip(SCENE_ROLES, nodes, strict=True):
        epoch = ReadMemberTime(node)
        words = {key: node.FieldsValue[key] for key in ("f2a0", "f2a4")}
        require(MakeFeatTime(epoch) == words and type(node.FieldsValue["f08"]) is int,
                "excluded field lacks its documented epoch or identity owner")
        fields = {key: typed_value(value, role_map) for key, value in node.FieldsValue.items() if key not in NORM}
        complete[role] = {"class": node.ClassValue.NameValue, "schema": node.ClassValue.SchemaValue,
                          "typed_field_count": len(node.FieldsValue), "fields": fields,
                          "persistent_id": node.FieldsValue["f08"], "transmit_map_index": node.IndexValue,
                          "creation_filetime": words, "creation_value": asdict(epoch)}
        if role != "environment":
            light = asdict(ReadLightInput(node))
            require(light.pop("CreatedValue") == asdict(epoch), "portable light clock differs from typed source")
            semantic[role] = light
    config = archive.require("Contents/Config-0")
    resolved = archive.require("Contents/Config-0-ResolvedFeatures")
    require(digest(path.read_bytes()) == identity, "disclosed immutable source changed during audit")
    return meta | {"source_sha256": identity, "config_sha256": digest(config), "resolved_sha256": digest(resolved),
                   "scene": complete, "semantic_fields": semantic}


def field_census(cases):
    stable, differences = {}, {}
    for role in SCENE_ROLES:
        objects = {name: case["scene"][role] for name, case in cases.items()}
        keys = set(next(iter(objects.values()))["fields"])
        require(all(set(row["fields"]) == keys for row in objects.values()), "typed scene field inventory differs")
        stable[role], differences[role] = {}, {}
        for key in sorted(keys):
            values = {case: row["fields"][key] for case, row in objects.items()}
            first = next(iter(values.values()))
            if len({canonical(value) for value in values.values()}) == 1:
                stable[role][key] = first
            else:
                differences[role][key] = values
    require(len({canonical(case["semantic_fields"]) for case in cases.values()}) == 1,
            "complete portable scene fields differ within the three disclosed controls")
    return stable, differences


def producer():
    path = "re/solidworks/records/PartEnvironmentDirtyPropagation2026.json"
    raw = (ROOT / path).read_bytes()
    record = json.loads(raw)
    require(any(row["name"] == "sldmodu.dll" and row["sha256"] == MODU for row in record["modules"]),
            "native scene producer identity differs")
    symbols = {row["name"]: {key: row[key] for key in ("start", "end_exclusive", "sha256")}
               for row in record["functions"] if row["name"] in ("ModelCreateDefaultLights01", "ModelHasLights01")}
    require(len(symbols) == 2, "missing recorded native producer or gate")
    ctor_path = "re/solidworks/records/AuthoredAmbientConstruction2026.json"
    ctor_raw = (ROOT / ctor_path).read_bytes()
    ctor = json.loads(ctor_raw)
    require(ctor["release"] == [34, 5, 2, 604]
            and ctor["modules"][0]["sha256"] == MODU
            and not ctor["source_claims"]["default_light_parity"],
            "authored constructor has an unexpected scope")
    return {"module_sha256": MODU, "functions": symbols, "source_ledger": {path: digest(raw), ctor_path: digest(ctor_raw)}}


def audit(packet):
    sources = {}
    for label, (relative, identity, terminal, receipt) in SRC.items():
        locator = f"re/solidworks/measurements/2026/{receipt}.json"
        receipt_bytes = (ROOT / locator).read_bytes()
        evidence(label, identity, json.loads(receipt_bytes))
        sources[label] = observe(packet / relative, identity, terminal) | {
            "disclosed_root_relative_locator": relative,
            "prior_oracle_receipt": {locator: digest(receipt_bytes)},
        }
    fields, different = field_census(sources)
    for source in sources.values():
        for row in source["scene"].values():
            row["compared_retained_fields"] = len(row.pop("fields"))
    return {"schema": "kit.sw2026.ordinary-part-lighting-census.v1",
            "native_source_build": BUILD, "native_source_executable_sha256": EXE,
            "sources": sources, "only_excluded_serialized_fields": sorted(NORM),
            "stable_typed_fields_by_role": fields, "other_typed_differences_by_role": different,
            "existing_native_producer_evidence": producer(), "host_tool_sha256": digest(Path(__file__).read_bytes()),
            "source_independent_vendor_default_proven": False, "new_native_launches": 0, "heldout_reads": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Audit the complete typed scene across three pinned SOLIDWORKS native part controls")
    parser.add_argument("disclosed_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.disclosed_root), indent=2, sort_keys=True))
