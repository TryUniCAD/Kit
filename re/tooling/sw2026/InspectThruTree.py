import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def portable(document):
    value = document.to_dict()
    value["metadata"].pop("solidworks_source_semantic_sha256", None)
    value["metadata"]["solidworks.typed_resolved_semantics"].pop("native_tree", None)
    return value


def project(args, archive, source):
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.ProjectTree import (
        ProjectTree,
    )

    model = NativePartModel(archive, None)
    link = ReadNativeLink(archive, 0)
    nodes = IndexFeatures(link)
    if args.mutation:
        sys.path.insert(0, str(Path(__file__).parent / "throughpresentation"))
        from Mutate import mutate

        model, link, nodes = mutate(
            args.mutation, model, link, nodes, ReadNativeLink(archive, 0)
        )
    features = {value.object_id: value for value in model.features}
    result = ProjectTree(model, link, nodes, features)
    ids = tuple(value.object_id for value in result.FeaturesValue)
    original_ids = tuple(value.object_id for value in model.features)
    if ids != original_ids:
        raise ValueError("projector dropped or reordered actual public owners")
    if args.mutation:
        if result.EvidenceValue["status"] != "unqualified":
            raise ValueError("malformed ownership unexpectedly qualified")
    return {
        "source_sha256": sha256(source).hexdigest(),
        "mutation": args.mutation,
        "status": result.EvidenceValue["status"],
        "diagnostic": result.EvidenceValue.get("diagnostic"),
        "public_ids": ids,
        "all_public_ids_retained": True,
        "native_oracle_used": False,
        "writer_output_count": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutation")
    parser.add_argument("--from-bytes", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.root / "src"))
    source = args.source.read_bytes()
    if sha256(source).hexdigest() != args.source_sha256:
        raise ValueError("declared disclosed source changed")
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    if args.mutation:
        record = project(args, SldprtArchive.from_bytes(source), source)
    else:
        from convert import open_document

        document = open_document(source if args.from_bytes else args.source)
        document.assert_valid()
        report = document.metadata["solidworks.typed_resolved_semantics"]["native_tree"]
        record = {
            "source_sha256": args.source_sha256,
            "status": report["status"],
            "tree": report,
            "public_ids": tuple(value.id for value in document.feature_timeline),
            "portable_sha256": sha256(canonical(portable(document))).hexdigest(),
            "history_count": len(document.feature_timeline),
            "parameter_names_values": tuple(
                (value.id, value.name, value.value.value)
                for value in document.parameters
            ),
            "selection_ids": tuple(value.id for value in document.selections),
            "native_oracle_used": False,
            "writer_output_count": 0,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": record["status"],
                "record_sha256": sha256(args.output.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
