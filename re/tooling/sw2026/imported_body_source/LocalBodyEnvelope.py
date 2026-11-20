from argparse import ArgumentParser
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from convert.Geometry.Parasolid import DecodePartData, EncodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString
from convert.adapters.solidworks.Container.Container import SldprtArchive
from para.Partition import frame_payloads, read_partition, write_payloads
from ReplayImportedBaseBody import SOURCE, require
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


LOCAL = "Config-0-FeatureBodies/LocalBodies"
PARTITION = "Contents/Config-0-Partition"
SCHEMA = "SCH_3701250_37102_13006"
BODY_DESCRIPTION = ": TRANSMIT FILE created by modeller version 3701250"


@dataclass(frozen=True)
class LocalBody:
    storage_key: str
    kernel_stream: bytes


def validate_key(text):
    require(type(text) is str and bool(text) and "\0" not in text,
            "the local body requires one nonempty feature storage key")


def check_kernel(raw):
    head = ParaHeaderData(raw)
    require(head is not None and (head.schema, head.description) == (SCHEMA, BODY_DESCRIPTION),
            "local body requires the measured bare Parasolid schema")


def decode(stream):
    cursor = BinaryReader(stream)
    require(cursor.ReadUnsigned(4) == 1, "expected a single local body group")
    name = ReadCStringMut(cursor)
    validate_key(name.TextValue)
    require(name.IsUnicode, "the local body group needs a wide storage key")
    high, low = cursor.ReadUnsigned(4), cursor.ReadUnsigned(4)
    require((high << 32) | low == 1, "expected a single grouped body")
    require(cursor.ReadUnsigned(4) == 0 and cursor.ReadUnsigned(1) == 0,
            "expected an ordinary present local body")
    record_size = cursor.ReadUnsigned(4)
    require(1 < record_size < 1 << 31 and record_size == cursor.GetRemaining(),
            "the local body's declared length differs from its record")
    require(cursor.ReadUnsigned(1) == 0, "expected the measured Parasolid kernel selector")
    encoded = cursor.TakeBytes(record_size - 1)
    payload, = DecodePartData(encoded, LOCAL)
    require(payload.wrapper_offset == 0 and payload.stored_size == len(encoded),
            "the Parasolid wrapper does not fill the declared body record")
    check_kernel(payload.data)
    return LocalBody(name.TextValue, payload.data)


def encode(body):
    validate_key(body.storage_key)
    check_kernel(body.kernel_stream)
    payload = EncodePartData(body.kernel_stream)
    record_size = 1 + len(payload)
    require(record_size < 1 << 31, "local body record size exceeds the signed archive word")
    return b"".join((
        pack("<i", 1),
        EncodeString(CStringValue(body.storage_key, True)),
        pack("<iiiBiB", 0, 1, 0, 0, record_size, 0),
        payload,
    ))


def inspect(source):
    data = source.read_bytes()
    require(sha256(data).hexdigest() == SOURCE, "use the exact disclosed imported source witness")
    archive = SldprtArchive.from_bytes(data)
    native_local = archive.require(LOCAL)
    local = decode(native_local)
    require(encode(local) == native_local, "typed local envelope changed on re-emission")
    native_partition = archive.require(PARTITION)
    partition = read_partition(native_partition)
    require(frame_payloads(write_payloads(partition)) == native_partition,
            "the active configuration partition changed on re-emission")
    world, = partition.nodes
    require(world.kind == 101 and world.fields["body"] == 0, "expected a body-free active WORLD")
    link = ReadNativeLink(archive, 0)
    feature, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moBaseBody_c")
    fields = feature.FieldsValue
    atom, = (row["o"] for row in fields["f528"]["items"])
    identifier, = (row["v"] for row in fields["f498"])
    mark = fields["f3d0"].FieldsValue["f18"]
    require(atom.ClassValue.NameValue == "moAtom_c" and atom.FieldsValue["f140"] == identifier
            and atom.FieldsValue["f130"] == atom.FieldsValue["f12c"] == fields["f08"]
            and mark == world.fields["current_id"] == partition.history[0].mark.fields["id"],
            "the import's atom, feature or mark ownership differs")
    require(fields["local_storage_key"] == local.storage_key,
            "the disclosed import text and local feature storage key differ")
    return {
        "schema": "kit.sw2026.imported-local-body-envelope.v1",
        "source_sha256": SOURCE,
        "local_body": {"stream": LOCAL, "bytes": len(native_local), "sha256": sha256(native_local).hexdigest(),
                       "raw_kernel_bytes": len(local.kernel_stream),
                       "raw_kernel_sha256": sha256(local.kernel_stream).hexdigest(), "storage_key": local.storage_key},
        "configuration_partition": {"stream": PARTITION, "bytes": len(native_partition),
                                    "sha256": sha256(native_partition).hexdigest(), "active_world_body": 0},
        "observed_resolved_link": {"feature_id": fields["f08"], "atom_id": identifier,
                                   "current_mark_id": mark, "atom_display_mode": atom.FieldsValue["f19c"]},
        "exact_linked_frames": 2,
        "native_writer_outputs": 0,
        "heldout_payloads_read": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure the local-body and empty-partition frames on the disclosed source")
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.source), indent=2, sort_keys=True))
