import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import struct
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert digest(args.input) == args.input_sha256
    assert digest(args.source_manifest) == args.source_sha256
    source_manifest = json.loads(args.source_manifest.read_bytes())
    assert all(
        digest(args.root / relative) == expected
        for relative, expected in source_manifest["files_sha256"].items()
    )
    manifest = json.loads(args.input.read_bytes())
    sys.path.insert(0, str(args.root / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
        ReadNodeName,
    )
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import (
        ReadFileKey,
    )

    def text(value):
        if isinstance(value, CStringValue):
            return value.TextValue
        if type(value) is str:
            return value
        raise ValueError("the actual optional name owner is not text")

    def walk(value, seen=None):
        seen = set() if seen is None else seen
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, ArchiveNode):
            yield value
            yield from walk(value.FieldsValue, seen)
        elif isinstance(value, dict):
            for item in value.values():
                yield from walk(item, seen)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from walk(item, seen)

    rows = []
    for source in manifest["files"]:
        path = Path(source["path"])
        assert digest(path) == source["sha256"]
        archive = SldprtArchive.from_bytes(path.read_bytes())
        linked = ReadNativeLink(archive, 0)
        references = [
            node
            for node in walk(
                (linked.ConfigValue.RootValue, linked.ResolvedValue.RootsValue)
            )
            if node.ClassValue.NameValue == "moReference_c"
        ]
        assert len(references) == 2
        entries = []
        for reference in references:
            fields = reference.FieldsValue
            external = ArchiveNode.RequireNode(fields["f3b0"])
            key = ReadFileKey(external)
            entries.append(
                {
                    "id": fields["f08"],
                    "name": ReadNodeName(reference),
                    "feature_flags": fields["f0c"],
                    "runtime_f540_in_wire_fields": "f540" in fields,
                    "reference_fields": {
                        key: value
                        for key, value in fields.items()
                        if isinstance(value, (int, float, str, bool))
                    },
                    "f500": text(fields["f500"]),
                    "f508": text(fields["f508"]),
                    "external": {
                        "object_identity": (
                            references.index(reference)
                            if external is not references[0].FieldsValue["f3b0"]
                            else 0
                        ),
                        "name": key[0],
                        "path_leaf": PureWindowsPath(key[1]).name,
                        "path_sha256": sha256(key[1].encode("utf-8")).hexdigest(),
                        "kind": key[2],
                        "created": key[3],
                        "fields": {
                            key: value
                            for key, value in external.FieldsValue.items()
                            if isinstance(value, (int, float, str, bool))
                        },
                        "override_sync_bit": bool(external.FieldsValue["f58"] & 0x10),
                        "f58_wire_width_bytes": 1,
                        "f58_u8_hex": struct.pack(
                            "<B", external.FieldsValue["f58"]
                        ).hex(),
                    },
                }
            )
        rows.append(
            {
                "label": source["label"],
                "sha256": source["sha256"],
                "bytes": path.stat().st_size,
                "archive_version": 19000,
                "container_version": archive.format_version,
                "references": entries,
                "name_hits": {
                    name: {
                        role: {
                            "utf16le_offsets": [
                                at
                                for at in range(len(stream))
                                if stream.startswith(name.encode("utf-16-le"), at)
                            ],
                            "stream_sha256": sha256(stream).hexdigest(),
                        }
                        for role, stream in archive.streams.items()
                        if name.encode("utf-16-le") in stream
                    }
                    for name in source["names"]
                },
                "source_unchanged": digest(path) == source["sha256"],
            }
        )
    result = {
        "schema": "kit.sw2026.component-instance-name-wire-audit.v1",
        "rows": rows,
        "tool_sha256": digest(Path(__file__)),
        "manifest_sha256": digest(args.input),
        "source_manifest_sha256": digest(args.source_manifest),
        "native_calls": 0,
        "writer_outputs": 0,
        "heldout_inputs_read": 0,
        "acceptance": False,
    }
    with args.output.open("x") as stream:
        stream.write(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    print(json.dumps({"rows": len(rows), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
