from argparse import ArgumentParser
from functools import partial
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from struct import pack, unpack_from

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField as Field
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Mates.MakeMatesCtx import MakeMatesCtx
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def context(resolved):
    value = MakeMatesCtx(resolved, None)
    owners = {
        "moMateConcentric": (
            Field("Base", "moMate2Geoms_c"),
            Field("Scalar", "f4b8", "i32"),
            Field("Scalar", "f4c4", "i32"),
        ),
        "moRefWrapper_c": (
            Field("Node", "f58"),
            *value.LayoutsValue["moRefWrapper_c"][2:],
        ),
        "moCylinderRef_w": (
            Field("Base", "moSurfaceRef_w"),
            Field("Embed", "fd0", "mgPoint_c.restore"),
            Field("Embed", "fe8", "mgVector_c.restore"),
            Field("Scalar", "f100", "f64"),
            Field("Present", "has_f108", "u16", BodyValue=(Field("Embed", "f108", "mgVector_c.restore"),)),
        ),
        "moCompRefCylinder_c": (
            Field("Base", "moCompFeature_c"),
            Field("Node", "ff8", "moRefGeom_c"),
        ),
        "moCompFace_c": (
            Field("Base", "moCompRef_c"),
            Field("Scalar", "alias", "u8"),
            Field("Branch", "", BodyValue=(Field("Text", "f08"),), ModeValue="Expression",
                  ExpressionValue=("compare", ("NotEq",), ("lookup", ("scope",), ("literal", "alias")), ("literal", 0))),
            Field("Node", "fe8"),
            Field("Node", "ff0"),
        ),
        "moFaceRef_c": (
            Field("Base", "moBEntRef_c"),
            Field("Branch", "", BodyValue=(
                Field("Scalar", "nf0", "i32"),
                Field("Repeat", "ff0", BodyValue=(
                    Field("Scalar", "f08", "i32"), Field("Scalar", "f0c", "u32"),
                    Field("Scalar", "f10", "u32"), Field("Scalar", "f14", "i32"),
                ), CountValue="nf0", ModeValue="Positive"),
            ), ModeValue="Expression", ExpressionValue=("compare", ("Eq",),
                  ("BitAnd", ("lookup_or", ("context",), ("literal", "conditions"), ("literal", 0)), ("literal", 128)),
                  ("literal", 0))),
        ),
        "moFromSktEntSurfIdRep_c": (Field("Base", "er.FUN_4bbaa6a0"),),
        "moFacetedData_c": (
            Field("Present", "has_points", "u16", BodyValue=(
                Field("Scalar", "f10", "i32"),
                Field("Repeat", "f08", BodyValue=(Field("Embed", "p", "mgPoint_c.restore"),), CountValue="f10", ModeValue="Positive"),
            )),
            *(Field("Scalar", key, "i32") for key in ("f40", "f44", "f48", "f4c", "f14", "f50", "f54")),
            Field("Scalar", "f58_empty", "i32"),
            Field("Branch", "", BodyValue=(Field("Text", "f58"),), ModeValue="Expression",
                  ExpressionValue=("compare", ("Eq",), ("lookup", ("scope",), ("literal", "f58_empty")), ("literal", 0))),
        ),
        "moRefCylinder_c": (
            Field("Base", "moRefGeom_c"),
            Field("Embed", "f6f8", "mgPoint_c.restore"),
            Field("Embed", "f710", "mgVector_c.restore"),
            Field("Scalar", "f728", "f64"),
        ),
    }
    value.LayoutsValue = dict(value.LayoutsValue) | owners
    value.SchemasValue = dict(value.SchemasValue) | {n: (1,) for n in owners}
    value.VirtualValue = dict(value.VirtualValue) | {
        (name, slot): value.VirtualValue[("moMatePerpendicular", slot)]
        for name in ("moMateConcentric", "moRefCylinder_c")
        for slot in (1000, 1016, 1208, 1216)
    }
    return value



def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def checked(root, path, wanted):
    require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root), "mate source escapes custody")
    raw = path.read_bytes()
    require(digest(raw) == wanted, f"mate source changed: {path.name}")
    return raw


def verify_geom(actual, native):
    for field, label in (("fd0", "point"), ("fe8", "axis")):
        point = actual[field]
        require(all(isclose(point[c], v, abs_tol=1e-11, rel_tol=1e-10)
                    for c, v in zip("xyz", native[label], strict=True)), "active cylinder geometry differs from COM")
    require(isclose(actual["f100"], native["radius_m"], abs_tol=1e-12, rel_tol=1e-10),
            "active cylinder radius differs from COM")


def endpoints(model, root, live):
    fields = root.FieldsValue
    order = live["ordered_endpoints"]
    require(fields["f08"] == live["native_feature_id"] and fields["f3b4"] == live["alignment"] + 1
            and (fields["f4b8"], fields["f4c4"]) == (int(live["rotation_locked"]), -1),
            "stored mate identity, alignment or lock differs from COM")
    seen = []
    for index, (snapshot_row, active_row, native) in enumerate(zip(fields["f3c8"], fields["f410"], order, strict=True)):
        snapshot = RequireNode(snapshot_row["o"], "moCylinderRef_w")
        active = RequireNode(active_row["o"], "moCylinderRef_w")
        end = active.FieldsValue
        saved = snapshot.FieldsValue
        require(snapshot_row["k"] == index and active is not snapshot and end["f74"] == fields["f08"],
                "ordinary concentric endpoint ordering or owner differs")
        require(end["has_f108"] == 1 and saved["has_f108"] == 0
                and all(end[k] == saved[k] for k in ("fd0", "fe8", "f100")), "separate cylinder geometries disagree")
        verify_geom(end, native)
        component = RequireNode(saved["f58"], "moCompRefCylinder_c").FieldsValue
        reference = RequireNode(component["ff8"], "moRefCylinder_c")
        for one, other in (("f6f8", "fd0"), ("f710", "fe8"), ("f728", "f100")):
            require(reference.FieldsValue[one] == saved[other], "snapshot reference cylinder geometry differs")
        facet = RequireNode(component["fb0"], "moFacetedData_c")
        face = RequireNode(end["f58"], "moCompFace_c")
        require(facet.FieldsValue["has_points"] == 0 and face.FieldsValue["alias"] == 0,
                "unqualified faceted point collection or face alias")
        occurrence = ReadChain(model, face)
        require(occurrence.FieldsValue["f08"] == native["occurrence_native_id"],
                "persistent cylinder face selected another actual occurrence")
        face_ref = RequireNode(face.FieldsValue["fe8"], "moFaceRef_c")
        face_ids = face_ref.FieldsValue["f10"]
        require(face_ref.FieldsValue["nf0"] == 0 and len(face_ids) > 0,
                "unqualified additional face records or missing persistent identity")
        surface = RequireNode(face_ids[0]["f08"], "moFromSktEntSurfIdRep_c")
        owner = RequireNode(surface.FieldsValue["f10"]["f10"], "moFR_c")
        seen.append({
            "api_occurrence_id": native["occurrence_native_id"],
            "archive_occurrence_slot": occurrence.IndexValue,
            "snapshot_slot": snapshot.IndexValue, "active_slot": active.IndexValue,
            "observed_local_axis": end["f108"], "observed_face_identity": {
                "sketch_feature": owner.FieldsValue["f10"]["f00"],
                "feature_creation": owner.FieldsValue["f10"]["f08"],
                "sketch_entity": surface.FieldsValue["f38"],
                "facet_entity_id": facet.FieldsValue["f40"],
                "facet_identifier_text": str(facet.FieldsValue["f58"]),
            },
        })
    require(len(seen) == 2 and seen[0]["archive_occurrence_slot"] != seen[1]["archive_occurrence_slot"],
            "concentric endpoints do not identify two separate occurrences")
    return seen


def roundtrip(raw, live):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    resolved = link.ResolvedValue
    name = link.ConfigName + "-MatesList"
    stream = archive.require(name)
    base, = unpack_from("<i", stream)
    count, offset = ReadCount(stream, 4)
    require(base == resolved.MapValue.CounterValue and count == 1, "native mate-list base or row count differs")
    cursor = BinaryReader(stream)
    cursor.OffsetValue = offset
    reader = GraphReader(cursor, ArchiveMaps(base, resolved.MapValue), partial(ReadBodyMut, context(resolved)))
    root = RequireNode(ReadNodeMut(reader), "moMateConcentric")
    require(cursor.GetRemaining() == 0, "unconsumed bytes in disclosed concentric mate stream")
    bindings = endpoints(link.ConfigValue.RootValue, root, live)
    cfg, seed = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    resolved_bytes, emitted = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000,
                                             seed.MapValue, resolved.ContextValue)
    require(cfg == archive.require(link.ConfigName) and resolved_bytes == archive.require(link.StreamName),
            "inherited Config or Resolved write differs")
    require(emitted.MapValue.CounterValue == base, "reconstructed inherited map has the wrong base")
    writer = BodyWriter(ArchiveMaps(base, emitted.MapValue), context(emitted), WriteBodyMut)
    writer.OutputValue.extend(pack("<i", base))
    writer.OutputValue.extend(EncodeCount(count))
    WriteNodeMut(writer, root)
    require(bytes(writer.OutputValue) == stream, "complete typed mate stream differs")
    loaded_map = reader.MapValue.Snapshot()
    saved_map = writer.MapValue.Snapshot()
    require(loaded_map.CounterValue == saved_map.CounterValue
            and len(loaded_map.EntriesValue) == len(saved_map.EntriesValue)
            and all(a.IndexValue == b.IndexValue and (
                a.EntryValue is b.EntryValue if isinstance(a.EntryValue, ArchiveNode)
                else a.EntryValue == b.EntryValue
            ) for a, b in zip(loaded_map.EntriesValue, saved_map.EntriesValue, strict=True)),
            "read/write identity maps differ")
    added = [entry for entry in loaded_map.EntriesValue if entry.IndexValue >= base]
    types = [entry.EntryValue.NameValue for entry in added if not isinstance(entry.EntryValue, ArchiveNode)]
    objects = sum(isinstance(entry.EntryValue, ArchiveNode) for entry in added)
    require(len(added) == loaded_map.CounterValue - base, "mate map growth is not owned by actual nodes and classes")
    return {
        "archive_sha256": digest(raw), "mate_alignment": live["alignment"], "rotation_locked": live["rotation_locked"],
        "inherited_counter": base, "mate_counter": loaded_map.CounterValue,
        "mate_added_object_count": objects, "mate_added_class_names": types, "actual_endpoint_bindings": bindings,
        "exact_streams": {path: {"sha256": digest(data), "bytes": len(data)} for path, data in (
            (link.ConfigName, cfg), (link.StreamName, resolved_bytes), (name, stream),
        )},
    }


def main():
    parser = ArgumentParser(description="Verify the linked archive and persistent face ownership of disclosed concentric mates")
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    root = args.packet.resolve(strict=True).parent
    packet = json.loads(checked(root, args.packet, args.packet_sha256))
    require(packet["schema"] == "kit.sw2026.concentric-mate-source-phases.v1",
            "use the exact measured concentric source packet")
    results = {}
    for role in ("D01", "D02", "D03"):
        transport_path = root / "RootCaseTransport01" / role / "Result.json"
        transport = json.loads(transport_path.read_bytes())
        require(transport["passed"] and transport["source_locked"] and transport["inventory_unchanged"]
                and transport["packet_sha256"] == args.packet_sha256, "disclosed source custody is incomplete")
        author = root / "Progress" / role / "author" / "Record.json"
        progress = json.loads(checked(root, author, transport["outcomes"]["author"]["record_sha256"]))
        case = root / "Disclosed" / role
        record = json.loads(checked(root, case / "SavedAuthor.json", progress["saved_author_sha256"]))
        results[role] = {}
        for phase in ("source", "edited"):
            paths = list((case / "Native" / phase.title()).glob("*.SLDASM"))
            require(len(paths) == 1, "expected one disclosed assembly per native phase")
            raw = checked(root, paths[0], record["saved_files"][phase]["parent"]["sha256"])
            results[role][phase] = roundtrip(raw, record[phase]["mate"])
    evidence = {
        "schema": "kit.sw2026.disclosed-concentric-archive-proof.v1", "packet_sha256": args.packet_sha256,
        "observer_sha256": digest(Path(__file__).read_bytes()), "passed": True,
        "heldout_inputs_read": 0, "new_native_processes": 0, "generative_writer_qualified": False,
        "cases": results,
    }
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "cases": 6, "exact_streams": 18, "result_sha256": digest(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
