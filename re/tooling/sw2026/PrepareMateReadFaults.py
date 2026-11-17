import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--child", type=Path, required=True)
    parser.add_argument("--wrong-child", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.root.resolve() / "src"))
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive, BuildSldprt
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    if args.output.exists():
        raise ValueError("fault preparation requires a new output directory")
    parent = args.parent.read_bytes()
    child = args.child.read_bytes()
    args.output.mkdir(parents=True)
    outcomes = []
    cases = {
        "TrailingMateByte": "trailing bytes",
        "WrongMatePrefix": "prefix differs",
        "StaleChildStamp": "child update is stale",
        "WrongChainOwner": "different assembly",
        "WrongEndpointOrdinal": "inconsistent ownership",
        "WrongChildDatum": "expected concrete moRefPlane_c",
        "CachedPlaneMismatch": "wrapper plane disagrees",
        "DistanceOption": "distance mate mode",
        "ConfigTail": "configuration has",
        "UnassignedMateId": "no assigned persistent identity",
        "MateIdCollision": "mate persistent identity collides",
        "DimensionIdCollision": "dimension identity collides",
        "NonlocalDistanceHandle": "expected concrete ParallelPlaneDistanceDim_c",
    }
    if args.wrong_child is not None:
        cases["WrongChildIdentity"] = "different part identity"
    for name, message in cases.items():
        archive = SldprtArchive.from_bytes(parent)
        streams = dict(archive.streams)
        if name == "WrongChildIdentity":
            pass
        elif name == "ConfigTail":
            streams["Contents/Config-0"] += b"\x00"
        elif name == "TrailingMateByte":
            streams["Contents/Config-0-MatesList"] += b"\x00"
        elif name == "WrongMatePrefix":
            raw = streams["Contents/Config-0-MatesList"]
            streams["Contents/Config-0-MatesList"] = (int.from_bytes(raw[:4], "little", signed=True) + 1).to_bytes(4, "little", signed=True) + raw[4:]
        else:
            link = ReadNativeLink(archive, 0)
            graph = ReadMatesMut(streams["Contents/Config-0-MatesList"], link.ResolvedValue)
            node = graph.RootsValue[0]
            wrapper = node.FieldsValue["f410"][0]["o"]
            if name == "StaleChildStamp":
                wrapper.FieldsValue["f08"] += 1
            elif name == "WrongChainOwner":
                component = wrapper.FieldsValue["f58"].FieldsValue["f58"]
                occurrence = component.FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"].FieldsValue["f50"]
                component.FieldsValue["owner"] = occurrence
            elif name == "WrongEndpointOrdinal":
                wrapper.FieldsValue["f78"] = 9
            elif name == "WrongChildDatum":
                wrapper.FieldsValue["f58"].FieldsValue["ff0"]["f00"] = -1
            elif name == "CachedPlaneMismatch":
                wrapper.FieldsValue["fd0"]["x"] += 0.0015
            elif name == "DistanceOption":
                if node.ClassValue.NameValue != "moMateDistanceDim_c":
                    raise ValueError("fault fixture requires a generated distance mate")
                node.FieldsValue["f4f4"] = 1
            elif name == "UnassignedMateId":
                node.FieldsValue["f08"] = -1
            elif name == "MateIdCollision":
                component = wrapper.FieldsValue["f58"].FieldsValue["f58"]
                occurrence = component.FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"].FieldsValue["f50"]
                node.FieldsValue["f08"] = occurrence.FieldsValue["f08"]
                for row in node.FieldsValue["f410"]:
                    row["o"].FieldsValue["f74"] = node.FieldsValue["f08"]
            elif name == "DimensionIdCollision":
                node.FieldsValue["f4b8"].FieldsValue["f850"][0]["o"].FieldsValue["ff0"].FieldsValue["f50"] = node.FieldsValue["f08"]
            elif name == "NonlocalDistanceHandle":
                node.FieldsValue["f4b8"].FieldsValue["f850"][0]["o"].FieldsValue["fe8"] = node.FieldsValue["f3c8"][0]["o"].FieldsValue["f58"].FieldsValue["f58"]
            streams["Contents/Config-0-MatesList"], _ = WriteMatesMut(graph.RootsValue, link.ResolvedValue)
        folder = args.output / name
        folder.mkdir()
        output = folder / args.parent.name
        output.write_bytes(BuildSldprt(streams, format_version=archive.format_version, file_id=archive.file_id))
        (folder / args.child.name).write_bytes(args.wrong_child.read_bytes() if name == "WrongChildIdentity" else child)
        outcomes.append({"case": name, "path": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "expected_error": message})
    if args.parent.read_bytes() != parent or args.child.read_bytes() != child:
        raise ValueError("diagnostic source input changed")
    receipt = {"schema": "solidworks-public-mate-read-fault-inputs-v1", "scope": "diagnostic copies only", "input_parent_sha256": hashlib.sha256(parent).hexdigest(), "input_child_sha256": hashlib.sha256(child).hexdigest(), "writer_output_count": 0, "diagnostic_output_count": len(outcomes), "cases": outcomes}
    (args.output / "Faults.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"prepared": len(outcomes), "manifest_sha256": hashlib.sha256((args.output / "Faults.json").read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
