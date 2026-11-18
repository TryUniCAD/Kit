import argparse
from base64 import b64decode
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def scalar(value, seen=None):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue

    if seen is None:
        seen = {}
    if isinstance(value, ArchiveNode):
        if id(value) in seen:
            return {"object_ref": seen[id(value)]}
        seen[id(value)] = len(seen)
        return {"class": value.ClassValue.NameValue, "fields": {key: scalar(item, seen) for key, item in value.FieldsValue.items() if key in ("f08", "f10", "f18", "f20", "f28", "f30", "f40", "f48", "f4c", "f50", "f54", "f58", "f60", "f70", "items", "n")}}
    if isinstance(value, CStringValue):
        return value.TextValue
    if isinstance(value, dict):
        return {str(key): scalar(item, seen) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [scalar(item, seen) for item in value]
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": sha256(value).hexdigest()}
    require(value is None or type(value) in (str, bool, int, float), "unexpected typed scalar owner")
    return value


def audit(root, path):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
    from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(path.read_bytes(), path.name)
    streams = {row.name: row.data for row in archive.records}
    link = ReadNativeLink(archive, 0)
    model = link.ConfigValue.RootValue
    header = link.ConfigValue.HeaderValue
    manager = ReadCmgrMut(streams["Contents/CMgr"], 19000)
    config = manager.RootValue.FieldsValue["f360"]
    mgr_header = ReadMgrHdrMut(streams["Contents/CMgrHdr2"], 19000)
    top = ReadHeaderGraph(streams["Header2"], 19000)
    result = {"input_sha256": digest(path), "model_class": model.ClassValue.NameValue, "configuration": ReadNodeName(config),
              "model_state": {key: scalar(model.FieldsValue[key]) for key in ("f08", "f1300", "f1560", "fd44", "fd48", "f1a18", "f1a20", "f7f8") if key in model.FieldsValue},
              "configuration_state": {key: scalar(config.FieldsValue[key]) for key in ("f08", "f4b0", "f85c", "f860") if key in config.FieldsValue},
              "headers": {name: {key: scalar(node.FieldsValue[key]) for key in ("f08", "f40", "f48", "fc4", "fec")} for name, node in (("model", header), ("top", top))},
              "directory": scalar(header.FieldsValue["f30"]), "manager_header": scalar(mgr_header.RootValue),
              "resolved_features": [{"class": node.ClassValue.NameValue, "id": node.FieldsValue.get("f08"), "name": ReadNodeName(node)} for node in link.ResolvedValue.RootsValue if isinstance(node, ArchiveNode)]}
    actual = {}
    config_bytes, stored = WriteConfigMut(model, 19000, header)
    resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000, stored.MapValue, link.ResolvedValue.ContextValue)
    actual.update({"Contents/Config-0": config_bytes, "Contents/Config-0-ResolvedFeatures": resolved_bytes,
                   "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000), "Header2": WriteHeadGraph(top, 19000),
                   "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000), "Contents/CMgrHdr2": WriteMgrHdrMut(mgr_header.RootValue, 19000)[0]})
    if model.ClassValue.NameValue == "moAssembly_c":
        refs = tuple(row["o"] for row in model.FieldsValue["f68"]["list"]["items"])
        result["occurrences"] = [{"name": ReadNodeName(node), **{key: scalar(node.FieldsValue[key]) for key in ("f08", "f3c0", "f3e0", "f3e8", "f3f0", "f3f4", "f3f8", "f400", "f408", "f360", "f370")}} for node in refs]
        result["config_reference_rows"] = scalar(config.FieldsValue["fce8"])
        mates = ReadMatesMut(streams["Contents/Config-0-MatesList"], link.ResolvedValue)
        actual["Contents/Config-0-MatesList"] = WriteMatesMut(mates.RootsValue, resolved)[0]
        mate_rows = []
        for node in mates.RootsValue:
            row = {"name": ReadNodeName(node), "id": node.FieldsValue["f08"], "class": node.ClassValue.NameValue}
            if node.ClassValue.NameValue == "moMateDistanceDim_c":
                handle, = [value["o"] for value in node.FieldsValue["f4b8"].FieldsValue["f850"]]
                dimension = handle.FieldsValue["ff0"]
                row["dimension"] = {"id": dimension.FieldsValue["f50"], "name": ReadNodeName(dimension.FieldsValue["f28"]), "metres": dimension.FieldsValue["f28"].FieldsValue["f58"]}
            mate_rows.append(row)
        result["mates"] = mate_rows
    result["typed_stream_round_trips"] = {name: {"bytes": len(value), "sha256": sha256(value).hexdigest(), "byte_identity": value == streams[name]} for name, value in actual.items()}
    require(all(row["byte_identity"] for row in result["typed_stream_round_trips"].values()), "the scoped generated or native-saved archive changed on typed round trip")
    result["passed"] = True
    return result


def close_values(first, second):
    return len(first) == len(second) and all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10) for a, b in zip(first, second, strict=True))


def compare(document, prediction, edited, child_sha):
    asm = document.assembly
    expected = prediction["edited" if edited else "initial"]
    require(asm is not None and len(asm.instances) == expected["body_count"] and len(asm.mates) == len(prediction["case"]["mates"]) and len(asm.mate_entities) == 2 * len(asm.mates) and len(asm.documents) == 1, "public typed read lost a complete group member or relationship")
    require([(row.name, row.active) for row in document.configurations] == [(prediction["assembly_configuration"], True)], "public parent configuration differs")
    child = asm.documents[0].document
    require(child.source.sha256 == child_sha and [(row.name, row.active) for row in child.configurations] == [(prediction["child_configuration"], True)], "public typed child identity or active configuration differs")
    sketch, = child.sketches
    boss, = [row for row in child.feature_timeline if str(row.kind) == "extrusion"]
    sketch_owners = {sketch.id, *(row.id for row in child.feature_timeline if row.sketch_id == sketch.id and row.name == sketch.name)}
    require(len(child.parameters) == 3 and all(row.owner_id in sketch_owners or row.owner_id == boss.id for row in child.parameters), "public child driving parameter owner differs")
    parameters = {("Sketch1" if row.owner_id in sketch_owners else boss.name, row.name): row for row in child.parameters}
    require(len(parameters) == 3, "public dimensioned child lost an actual driver")
    for parameter, value in prediction["child_parameters_m"].items():
        name, owner = parameter.split("@")
        row = parameters[owner, name]
        require(row.value.unit == "mm" and math.isclose(row.value.value * .001, value, rel_tol=1e-12), "public child driving value differs")
    instances = {row.name: row for row in asm.instances}
    require(set(instances) == set(prediction["occurrence_names"]), "public occurrence names differ")
    for index, name in enumerate(prediction["occurrence_names"]):
        row, matrix = instances[name], expected["occurrence_transforms"][index]
        target = [matrix[0], matrix[3], matrix[6], matrix[9] * 1000, matrix[1], matrix[4], matrix[7], matrix[10] * 1000, matrix[2], matrix[5], matrix[8], matrix[11] * 1000, 0., 0., 0., 1.]
        require(row.fixed == expected["fixed_flags"][index] and row.configuration_name == prediction["child_configuration"] and close_values(row.transform.values, target), "public occurrence placement configuration or anchor differs")
    entities = {row.id: row for row in asm.mate_entities}
    planes = {row.name: row.id for row in child.support_planes}
    for row, spec, length in zip(asm.mates, prediction["case"]["mates"], expected["mate_values_m"], strict=True):
        require((row.name, str(row.kind), str(row.alignment), row.suppressed) == (spec["name"], spec["kind"], "aligned", False), "public ordered mate identity differs")
        require(row.value is None if length is None else row.value is not None and row.value.unit == "mm" and math.isclose(row.value.value * .001, length, rel_tol=1e-12), "public driving mate distance differs")
        for identity, (index, datum) in zip(row.entity_ids, spec["planes"], strict=True):
            entity = entities[identity]
            require(str(entity.kind) == "plane" and entity.instance_path == (instances[prediction["occurrence_names"][index]].id,) and entity.source_entity_id == planes[datum] and entity.attributes["native_datum_name"] == datum, "public typed mate endpoint differs from its actual occurrence and child datum")
    report = document.metadata["solidworks.typed_mates_semantics"]
    require(report["status"] == "admitted" and report["full_selected_mate_graph"], "public reader did not admit the complete selected group graph")
    return {"passed": True, "occurrences": len(asm.instances), "mates": len(asm.mates), "entities": len(asm.mate_entities), "driver_count": len(parameters), "fixed_flags": [instances[name].fixed for name in prediction["occurrence_names"]], "diagnostic_codes": [row.code for row in document.diagnostics]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("read", "audit"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    path = args.file.resolve(strict=True)
    if args.mode == "audit":
        result = audit(root, path)
    else:
        sys.path.insert(0, str(root / "re/tooling/sw2026"))
        from ReadSdkOrderedNative import read_process
        result = read_process(root, path)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
