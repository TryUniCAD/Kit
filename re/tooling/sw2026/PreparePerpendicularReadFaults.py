import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def modify(name, mate, model):
    fields = mate.FieldsValue
    resolved = [row["o"] for row in fields["f410"]]
    selected = [row["o"] for row in fields["f3c8"]]
    actual_plane = resolved[0].FieldsValue["f58"]
    detached_plane = selected[0].FieldsValue["f58"]
    if name == "InternalAligned":
        fields["f3b4"] = 1
    elif name == "Unsolved":
        fields["f3b8"] = 0
    elif name == "UnqualifiedNodeFlag":
        fields["f0c"] = 1
    elif name == "AuxiliaryText":
        fields["f488"] = "unsupported auxiliary state"
    elif name == "DetachedOrder":
        fields["f3c8"][0]["k"] = 1
    elif name == "DetachedOwner":
        detached_plane.FieldsValue["f58"].FieldsValue["owner"] = actual_plane
    elif name == "DetachedOriginalDatum":
        detached_plane.FieldsValue["f9c"] += 1
    elif name == "DetachedAllocatedId":
        detached_plane.FieldsValue["ff8"].FieldsValue["f08"] = 2
    elif name == "DetachedAbsoluteGeometry":
        detached_plane.FieldsValue["ff8"].FieldsValue["f6f8"].FieldsValue["root"]["x"] += 0.001
    elif name == "DetachedSentinel":
        selected[0].FieldsValue["f74"] = fields["f08"]
    elif name == "DetachedParentStamp":
        selected[0].FieldsValue["f08"] += 1
    elif name == "DetachedCreationEpoch":
        detached_plane.FieldsValue["ff0"]["f08"] += 1
    elif name == "ResolvedOwner":
        actual_plane.FieldsValue["f58"].FieldsValue["owner"] = actual_plane
    elif name == "ResolvedMateId":
        resolved[0].FieldsValue["f74"] += 1
    elif name == "DuplicateWrapperId":
        resolved[1].FieldsValue["f78"] = resolved[0].FieldsValue["f78"]
    elif name == "StaleChildStamp":
        resolved[0].FieldsValue["f08"] += 1
    elif name == "WrongChildConfiguration":
        resolved[0].FieldsValue["f0c"] += 1
    elif name == "WrongChildDatum":
        actual_plane.FieldsValue["ff0"]["f00"] = 9999
    elif name == "WrongDatumCreationEpoch":
        actual_plane.FieldsValue["ff0"]["f08"] += 1
    elif name == "WrongPrincipalKind":
        actual_plane.FieldsValue["f100"] = 0
    elif name == "ResolvedPlaneGeometry":
        resolved[0].FieldsValue["fd0"]["x"] += 0.001
    elif name == "NonorthogonalGeometry":
        resolved[1].FieldsValue["fe8"] = dict(resolved[0].FieldsValue["fe8"])
    else:
        raise ValueError("unknown perpendicular diagnostic mutation")


def prepare(root, parent, child, output):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
    from convert.adapters.solidworks.Container.Container import SldprtArchive, BuildSldprt
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    names = ("InternalAligned", "Unsolved", "UnqualifiedNodeFlag", "AuxiliaryText", "DetachedOrder", "DetachedOwner",
             "DetachedOriginalDatum", "DetachedAllocatedId", "DetachedAbsoluteGeometry", "DetachedSentinel",
             "DetachedParentStamp", "DetachedCreationEpoch", "WrongDatumCreationEpoch", "WrongPrincipalKind",
             "ResolvedOwner", "ResolvedMateId", "DuplicateWrapperId", "StaleChildStamp", "WrongChildConfiguration",
             "WrongChildDatum", "ResolvedPlaneGeometry", "NonorthogonalGeometry", "DuplicateMate", "TrailingMateByte", "WrongMapPrefix", "TruncatedMate", "RepackedControl")
    parent_bytes, child_bytes = parent.read_bytes(), child.read_bytes()
    require(not output.exists(), "diagnostic copies require a new destination")
    output.mkdir(parents=True)
    rows = []
    for name in names:
        archive = SldprtArchive.from_bytes(parent_bytes)
        streams = dict(archive.streams)
        stream = streams["Contents/Config-0-MatesList"]
        if name == "TrailingMateByte":
            stream += b"\x00"
        elif name == "WrongMapPrefix":
            stream = (int.from_bytes(stream[:4], "little", signed=True) + 1).to_bytes(4, "little", signed=True) + stream[4:]
        elif name == "TruncatedMate":
            stream = stream[:-1]
        else:
            link = ReadNativeLink(archive, 0)
            graph = ReadMatesMut(stream, link.ResolvedValue)
            roots = graph.RootsValue
            if name == "DuplicateMate":
                roots = (*roots, roots[0])
            elif name == "RepackedControl":
                pass
            else:
                modify(name, roots[0], FindModelRoot(link.ResolvedValue.MapValue))
            stream, _ = WriteMatesMut(roots, link.ResolvedValue)
        streams["Contents/Config-0-MatesList"] = stream
        folder = output / name
        folder.mkdir()
        target = folder / parent.name
        target.write_bytes(BuildSldprt(streams, template=parent_bytes, format_version=archive.format_version, file_id=archive.file_id))
        (folder / child.name).write_bytes(child_bytes)
        rows.append({"case": name, "path": str(target), "sha256": sha256(target.read_bytes()).hexdigest()})
    require(parent.read_bytes() == parent_bytes and child.read_bytes() == child_bytes, "immutable source inputs changed")
    result = {"schema": "kit.sw2026.perpendicular-reader-diagnostic-copies.v1", "writer_output_count": 0,
              "diagnostic_output_count": len(rows), "repacked_disclosed_control_only": True,
              "source_parent_sha256": sha256(parent_bytes).hexdigest(),
              "source_child_sha256": sha256(child_bytes).hexdigest(), "cases": rows}
    (output / "Faults.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--child", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.root.resolve(), args.parent, args.child, args.output)
    print(json.dumps({"diagnostic_output_count": result["diagnostic_output_count"], "writer_output_count": 0}))


if __name__ == "__main__":
    main()
