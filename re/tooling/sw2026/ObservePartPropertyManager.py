from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("part", type=Path)
    parser.add_argument("expected_sha256")
    parser.add_argument("expected_status", choices=("complete", "unsupported"))
    args = parser.parse_args()
    blob = args.part.read_bytes()
    digest = sha256(blob).hexdigest()
    if digest != args.expected_sha256:
        raise ValueError("disclosed source part digest differs")

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "src"))

    from convert import open_document
    from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
    from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
    from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
    from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
    from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Archive.Properties.ManagerFields import (
        KManagerFields,
        KManagerSchemas,
    )
    from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropRoot
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    stream = SldprtArchive.FromBytes(blob).Require("Contents/CusProps")
    graph = ReadPropRoot(stream, 19000)
    context = BodyContext(19000, KManagerFields, {}, KManagerSchemas, NewBodyUsage(19000, None))
    writer = BodyWriter(ArchiveMaps(1), context, WriteBodyMut)
    WriteNodeMut(writer, graph)
    if bytes(writer.OutputValue) != stream:
        raise ValueError("property manager was not encoded byte-for-byte")
    document = open_document(args.part)
    info = document.metadata["solidworks.part_text_properties"]
    if info["status"] != args.expected_status:
        raise ValueError("public property status differs from the independent expectation")
    if args.part.read_bytes() != blob:
        raise ValueError("disclosed source changed during inspection")

    print(
        json.dumps(
            {
                "case": args.case_id,
                "file_sha256": digest,
                "stream_sha256": sha256(stream).hexdigest(),
                "stream_bytes": len(stream),
                "stream_map_base": 1,
                "stream_map_counter": writer.MapValue.CounterValue,
                "keys_count": graph.FieldsValue["n20"],
                "exact_roundtrip": True,
                "public_projection": info,
                "input_unchanged": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
