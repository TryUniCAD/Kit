from hashlib import sha256

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.History.ReadHistGraph import ReadHistGraph
from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Container.Bookkeeping import EncodePartMeta, PartStamps
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import decode_partition_stream
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import ChmfRoleKey
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Shells.ReadOpenShell import ReadOpenShell

PARTITION = "Contents/Config-0-Partition"
VERSION = 19000


def demand(ok, why):
    if not ok:
        raise ValueError(why)


def fingerprint(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def prove_sidecars(archive, header):
    rows = {}
    name = "Contents/Definition"
    definition = ReadModelDef(archive.require(name), VERSION)
    encoded = WriteModelDef(definition.GraphValue)
    demand(encoded.OutputValue == archive.require(name), "Definition typed replay differs")
    demand(definition.MapValue.CounterValue == encoded.MapValue.CounterValue, "Definition map differs")
    rows[name] = fingerprint(encoded.OutputValue) | {
        "root_class": definition.GraphValue.DocumentValue.ClassValue.NameValue,
        "root_fields": len(definition.GraphValue.DocumentValue.FieldsValue),
        "map_counter": definition.MapValue.CounterValue,
    }
    for kind in ("History", "Biography"):
        name = f"_MO_VERSION_{VERSION}/{kind}"
        loaded = ReadHistGraph(archive.require(name), VERSION)
        data, written = WriteHistGraph(loaded.RootValue, VERSION)
        demand(data == archive.require(name) and loaded.MapValue.CounterValue == written.MapValue.CounterValue,
               f"{kind} typed replay or map differs")
        rows[name] = fingerprint(data) | {
            "root_class": loaded.RootValue.ClassValue.NameValue,
            "map_counter": loaded.MapValue.CounterValue,
        }
    fields = header.FieldsValue
    stamps = PartStamps(fields["f70"], fields["f40"], fields["f44"])
    for name, data in EncodePartMeta(VERSION, stamps).items():
        demand(data == archive.require(name), f"{name} differs from actual header-derived metadata")
        rows[name] = fingerprint(data)
    return rows, {"creation_time": stamps.creation_time, "update": stamps.update, "body": stamps.body}


def witness(archive):
    proof = ReadOpenShell(archive, 0)
    link, stock = proof.LinkValue, proof.StockValue
    owner, shell, atom = stock.OwnerValue.NodeValue, proof.ShellNode, proof.AtomValue
    controllers = link.ConfigValue.RootValue.FieldsValue["fe38"], owner.FieldsValue["f3d0"], shell.FieldsValue["f3d0"]
    box = stock.BoundsValue
    bounds = tuple(tuple(getattr(point, axis) / 1000 for axis in ("x", "y", "z")) for point in (box.minimum, box.maximum))
    header = ReadHeaderGraph(archive.require("Header2"), VERSION)
    creator = NativeNodeId(owner)
    creation_time = DatumTime(header, creator)
    demand(creation_time == DatumTime(link.ConfigValue.HeaderValue, creator), "creator event headers differ")
    return {
        "controller_marks": [node.FieldsValue["f18"] for node in controllers],
        "controller_slots": [node.IndexValue for node in controllers],
        "creator_id": creator,
        "creator_name": ReadNativeName(owner),
        "modifier_id": NativeNodeId(shell),
        "modifier_name": ReadNativeName(shell),
        "creator_time": creation_time,
        "atom_id": atom.FieldsValue["f140"],
        "kernel_body_tag": atom.FieldsValue["f180"],
        "stock_bounds_metres": bounds,
        "selected_ref_slot": proof.FaceValue.IndexValue,
        "selected_ref_tag": proof.FaceValue.FieldsValue["f70"],
        "selected_carriers": [ChmfRoleKey(row["f08"]) for row in proof.FaceValue.FieldsValue["f10"] if row["f08"] is not None],
        "unknown_end_words": {name: stock.OwnerValue.EndValue.FieldsValue[name] for name in ("f150", "f154")},
    }, header


def read_shell_save(raw):
    archive = SldprtArchive.from_bytes(raw)
    facts, header = witness(archive)
    sidecars, stamps = prove_sidecars(archive, header)
    active, delta = decode_partition_stream(archive.require(PARTITION), PARTITION)
    try:
        ReadHistMarks(delta.data, ReadActiveNodes(active.data))
    except ValueError as error:
        demand(str(error) == "current kernel framing differs", "delete-only refusal moved")
    else:
        raise ValueError("delete-only rollback incorrectly accepted retained stock")
    caches = {
        name: fingerprint(archive.require(name))
        for name in (PARTITION, "Contents/Config-0-LWDATA", "Contents/DisplayLists")
    }
    return {
        "owners": facts,
        "bookkeeping": stamps,
        "archive_replays": sidecars,
        "cache_inventory": caches,
        "delete_only_refusal": "current kernel framing differs",
    }
