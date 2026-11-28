from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive

VERSION = 19000
CONFIG = "Contents/Config-0"
HEADER = "Contents/Config-0-ModelHeader"
DISCLOSED_LOCK = "aa3408803e08ea1a7e32f4117103f92eb5bd8132ff01648fbfc260839cff7a91"
CONTROL = "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"


def digest(data):
    return sha256(data).hexdigest()


def require(result, message):
    if not result:
        raise ValueError(message)


def owned_list(record):
    values = [row["o"] for row in record["items"]]
    require(len(values) == record["n"], "list does not own the declared objects")
    return values


def inspect_relation(graph, source_state):
    managers = [
        entry.EntryValue
        for entry in graph.MapValue.EntriesValue
        if isinstance(entry.EntryValue, ArchiveNode)
        and entry.EntryValue.ClassValue.NameValue == "moRelMgr_c"
    ]
    (manager,) = managers
    (relation,) = owned_list(manager.FieldsValue["f58"])
    rel_fields = relation.FieldsValue
    (api_row,) = source_state["equations"]
    require(rel_fields["f10"] == api_row["text"], "native relation text differs")
    require(
        rel_fields["f18"] & 0x0408 == 0 and not api_row["disabled"],
        "ordinary source relation is disabled or suppressed",
    )

    sides = []
    for slot in ("f58", "f60"):
        side = rel_fields[slot]
        fields = side.FieldsValue
        require(fields["fa0"] is relation, "equation side lost its relation alias")
        source_text = fields["f50"].lstrip()
        tokens = []
        for token in owned_list(fields["f10"]):
            token_fields = token.FieldsValue
            start, end = token_fields["f14"], token_fields["f18"]
            text = token_fields["f08"]
            require(
                0 <= start < end <= len(source_text) and source_text[start:end] == text,
                "equation token lost its range within the parsed side",
            )
            row = {
                "class": token.ClassValue.NameValue,
                "text": text,
                "start": start,
                "end": end,
                "element_type": token_fields["f1c"],
            }
            if token.ClassValue.NameValue == "moRelDimension_c":
                wrapper = token_fields["f80"]
                target = wrapper.FieldsValue["f58"]
                row.update(
                    binding_class=target.ClassValue.NameValue,
                    binding_map_slot=target.IndexValue,
                    cached_si=wrapper.FieldsValue["fb0"],
                    wrapper_f08=wrapper.FieldsValue["f08"],
                    local_reference=token_fields["f78"] is None,
                    dependency_count=token_fields["f30"]["n"],
                )
            tokens.append(row)
        sides.append({"side_map_slot": side.IndexValue, "tokens": tokens})

    bindings = [
        token
        for side in sides
        for token in side["tokens"]
        if token["class"] == "moRelDimension_c"
    ]
    require(
        [row["binding_class"] for row in bindings]
        == ["moFeatureDimHandle_c", "moSkDimHandleValG2_c"],
        "source uses a different dimension-owner profile",
    )
    by_name = {
        row["full_name"].rsplit("@", 1)[0]: row["system_value_m"]
        for row in source_state["dimensions"].values()
    }
    require(
        all(item["cached_si"] == by_name[item["text"].strip('"')] for item in bindings),
        "cached SI values disagree with the fresh native source observations",
    )
    return {
        "manager_map_slot": manager.IndexValue,
        "relation_map_slot": relation.IndexValue,
        "manager_dimension_cache_count": manager.FieldsValue["f10"]["n"],
        "flags": rel_fields["f18"],
        "following_signed_long": rel_fields["f48"],
        "sides": sides,
    }


def signature(graph):
    return (
        graph.MapBase,
        graph.MapValue.CounterValue,
        [
            (
                item.IndexValue,
                (
                    item.EntryValue.ClassValue
                    if isinstance(item.EntryValue, ArchiveNode)
                    else item.EntryValue
                ),
            )
            for item in graph.MapValue.EntriesValue
        ],
    )


def verify_resolved(document, config_graph, relation, observed):
    cmgr = ReadCmgrMut(document.Require("Contents/CMgr"), VERSION)
    context = {
        "cmgr_f658": cmgr.RootValue.FieldsValue["f658"],
        "model_compressed_stream": 1,
        "model_is_part": 1,
    }
    source = document.Require("Contents/Config-0-ResolvedFeatures")
    resolved = ReadResolvedMut(source, VERSION, config_graph.MapValue, context)
    rebuilt, written = WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        VERSION,
        config_graph.MapValue,
        context,
    )
    require(rebuilt == source, "typed ResolvedFeatures is not byte-exact")
    require(
        signature(resolved) == signature(written),
        "resolved writer changed map identity",
    )
    prefix = tuple(entry.EntryValue for entry in config_graph.MapValue.EntriesValue)
    require(
        all(
            item.EntryValue is adopted
            for adopted, item in zip(prefix, resolved.MapValue.EntriesValue)
        ),
        "resolved map replaced an inherited configuration object",
    )
    stamp = observed["update_stamp"]
    wrapper_stamps = [
        token["wrapper_f08"]
        for side in relation["sides"]
        for token in side["tokens"]
        if "binding_class" in token
    ]
    require(wrapper_stamps == [stamp, stamp], "wrapper cache epoch differs")
    return {
        "config_map_seed": resolved.MapBase,
        "resolved_map_counter": resolved.MapValue.CounterValue,
        "resolved_bytes": len(source),
        "resolved_sha256": digest(source),
        "inherited_objects": len(prefix),
        "native_update_stamp": stamp,
        "byte_exact": True,
    }


def verify_disclosed(packet, lock, observations, role, linked):
    path = packet / "Disclosed" / "D02" / "Native" / (role + ".SLDPRT")
    saved = lock["source_files"][role]
    raw = path.read_bytes()
    require(
        digest(raw) == saved["sha256"] and len(raw) == saved["bytes"],
        "disclosed native source differs from its lock",
    )
    document = SldprtArchive.FromBytes(raw)
    config = document.Require(CONFIG)
    header = ReadHeaderGraph(document.Require(HEADER), VERSION)
    try:
        ReadConfigMut(config, VERSION, header)
    except BodyUnsupported as error:
        require("moRelation_c schema 1" in str(error), "unexpected ordinary refusal")
    else:
        raise ValueError(
            "the ordinary profile unexpectedly admitted a populated relation"
        )
    graph = ReadConfigMut(config, VERSION, header, PartRelations=True)
    require(graph.RootValue.FieldsValue["fb4"] == VERSION, "source version differs")
    relation = inspect_relation(graph, observations[role])
    returned, written = WriteConfigMut(
        graph.RootValue, VERSION, header, PartRelations=True
    )
    require(returned == config, "typed Config-0 is not byte-exact")
    require(
        signature(graph) == signature(written), "writer changed archive map identity"
    )
    again = ReadConfigMut(returned, VERSION, header, PartRelations=True)
    require(signature(graph) == signature(again), "reopen changed archive map identity")
    require(digest(path.read_bytes()) == saved["sha256"], "disclosed input changed")
    result = {
        "source_sha256": saved["sha256"],
        "config_bytes": len(config),
        "config_sha256": digest(config),
        "map_base": graph.MapBase,
        "map_counter": graph.MapValue.CounterValue,
        "ordinary_profile_refused": True,
        "byte_exact": True,
        "relation": relation,
    }
    if linked:
        result["linked"] = verify_resolved(
            document, graph, relation, observations[role]
        )
    return result


def verify_control(packet):
    path = packet / "Control.SLDPRT"
    source = path.read_bytes()
    require(digest(source) == CONTROL, "the disclosed pristine control differs")
    document = SldprtArchive.FromBytes(source)
    config = document.Require(CONFIG)
    header = ReadHeaderGraph(document.Require(HEADER), VERSION)
    ordinary = ReadConfigMut(config, VERSION, header)
    alternative = ReadConfigMut(config, VERSION, header, PartRelations=True)
    a, _ = WriteConfigMut(ordinary.RootValue, VERSION, header)
    b, _ = WriteConfigMut(alternative.RootValue, VERSION, header, PartRelations=True)
    require(a == b == config, "empty-manager regression changed config bytes")
    require(
        signature(ordinary) == signature(alternative), "control archive map differs"
    )
    return {
        "config_sha256": digest(config),
        "config_bytes": len(config),
        "byte_exact": True,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed-packet", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--linked", action="store_true")
    args = parser.parse_args()
    require(not args.output.exists(), "use an unused receipt path")
    packet = args.disclosed_packet
    lock_bytes = (packet / "Progress/D02/Lock/Record.json").read_bytes()
    require(digest(lock_bytes) == DISCLOSED_LOCK, "the disclosed source lock differs")
    lock = json.loads(lock_bytes)
    native = (packet / "Disclosed/D02/Inspection/Author/Result.json").read_bytes()
    require(
        digest(native) == lock["phases"]["Author"]["result_sha256"],
        "native evidence differs",
    )
    cases = {
        role: verify_disclosed(
            packet, lock, json.loads(native)["observed"], role, args.linked
        )
        for role in ("Original", "Edited")
    }
    proof = {
        "schema": "kit.sw2026.part-equation-config-replay.v1",
        "disclosed_lock_sha256": DISCLOSED_LOCK,
        "native_observation_sha256": digest(native),
        "typed_configs": cases,
        "total_source_bytes": sum(row["config_bytes"] for row in cases.values()),
        "unchanged_control": verify_control(packet),
        "sealed_inputs_read": 0,
        "native_oracle_starts": 0,
        "generated_native_files": 0,
    }
    if args.linked:
        proof["linked_resolved_bytes"] = sum(
            row["linked"]["resolved_bytes"] for row in cases.values()
        )
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(proof, out, indent=2, sort_keys=True, allow_nan=False)
        out.write("\n")
    print(
        json.dumps({"passed": True, "receipt_sha256": digest(args.output.read_bytes())})
    )


if __name__ == "__main__":
    main()
