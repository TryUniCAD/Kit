import argparse
from dataclasses import replace
from hashlib import sha256
import json
from math import pi
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def refresh(candidate):
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import (
        WriteHeadGraph,
    )
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt

    config, graph = WriteConfigMut(
        candidate.SystemValue.RootValue, 19000, candidate.HeaderValue
    )
    resolved, resolved_graph = WriteResolMut(
        candidate.ResolvedValue.RootsValue,
        None,
        19000,
        graph.MapValue,
        {
            "model_compressed_stream": 1,
            "model_is_part": 1,
            "cmgr_f658": candidate.SystemValue.ManagerValue.FieldsValue["f658"],
        },
    )
    streams = dict(candidate.StreamsValue)
    streams.update(
        {
            "Contents/Config-0": config,
            "Contents/Config-0-ResolvedFeatures": resolved,
            "Contents/Config-0-ModelHeader": WriteHeadGraph(
                candidate.HeaderValue, 19000
            ),
            "Header2": WriteHeadGraph(candidate.TopHeader, 19000),
            "Contents/CMgr": WriteCmgrMut(candidate.SystemValue.ManagerValue, 19000),
        }
    )
    return replace(
        candidate,
        ConfigValue=graph,
        ResolvedValue=resolved_graph,
        StreamsValue=streams,
        BytesValue=BuildSldprt(streams, FormatVersion=4),
    )


def same_owners(candidate):
    root = candidate.SystemValue.RootValue.FieldsValue
    feature = candidate.BossValue.FeatureValue.FieldsValue
    folder = root["f1e0"].FieldsValue
    (atom,) = [row["o"] for row in feature["f528"]["items"]]
    return {
        "root_id": root["f08"],
        "root_flags": root["f0c"],
        "folder_id": folder["f08"],
        "folder_flags": folder["f0c"],
        "boss_id": feature["f08"],
        "boss_flags": feature["f0c"],
        "body_atom_id": atom.FieldsValue["f140"],
        "body_tag": atom.FieldsValue["f180"],
        "selected_mark": feature["f3d0"].FieldsValue["f18"],
        "activation_mark": root["fe38"].FieldsValue["f18"],
        "header_geometry_fields": {
            key: candidate.HeaderValue.FieldsValue[key] for key in ("f40", "f44", "f48")
        },
        "configuration_update": candidate.CurrentConfig.FieldsValue["f860"],
    }


def prepare(args):
    root = args.root.resolve(strict=True)
    sys.path[:0] = [
        str(root / "src"),
        str(root / "re/tooling/sw2026"),
        str(root / "re/tooling/sw2026/serial"),
    ]
    from interchange.serialization.Deserialize import FromData
    from para.concentric.CheckConcentricAssembly import run, schedule
    from para.prism.SdkPrismAttachment import install_light
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import (
        WriteHeadGraph,
    )
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )

    neutral_raw = args.neutral.read_bytes()
    ambient_raw = args.ambient.read_bytes()
    require(
        sha256(neutral_raw).hexdigest()
        == "e5e005dc738ad379f0485accc78d7f72002cccdc1b14186ea43ed82e4f444fe3",
        "only the declared disclosed Feature neutral input is admitted",
    )
    require(
        sha256(ambient_raw).hexdigest() == args.ambient_sha256,
        "authored ambient intent changed",
    )
    document = FromData(json.loads(neutral_raw))
    light = json.loads(ambient_raw)
    epoch = 1815300301
    original_destination = r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\ConcentricMateNativeDeck02\Generated\Feature\ConcentricNeutralAlphaDerived.SLDASM"
    original, baseline = run(document, original_destination, epoch, 1)
    require(
        original["child_sha256"]
        == "64e1568c00763e734a00bf1f1778357b1864ca79abc30ec2b7f996bc3e20d845"
        and original["assembly_sha256"]
        == "e07d04635daf7a8b9ee5790dc34e7876c555b12690d36b9ff0cc6138a7222a59",
        "untouched current construction does not reproduce the frozen native inputs",
    )
    out = args.output.resolve()
    require(not out.exists(), "choose an unused ambient packet root")
    child_path = PureWindowsPath(args.native_child)
    require(
        child_path.is_absolute()
        and child_path.name == "NeutralCylinderAlphaDerived.SLDPRT",
        "expected the exact new absolute cylinder locator",
    )
    destination = str(child_path.with_name("ConcentricNeutralAlphaDerived.SLDASM"))
    off_receipt, off_bundle = run(document, destination, epoch, 1)
    on_receipt, on_bundle = run(document, destination, epoch, 1)
    off = off_bundle.attachment.candidate
    on = on_bundle.attachment.candidate
    require(
        off.BytesValue == on.BytesValue,
        "the independent new baseline constructions differ",
    )
    owners = same_owners(off)
    old_next = on.HeaderValue.FieldsValue["f08"]
    active = True
    denied = []

    def guard(event, values):
        if active and event in (
            "open",
            "subprocess.Popen",
            "os.system",
            "os.posix_spawn",
            "socket.connect",
        ):
            denied.append(event)
            raise RuntimeError(
                "ambient construction attempted runtime operation: " + event
            )

    sys.addaudithook(guard)
    try:
        install_light(on, light, schedule(epoch, 1).update_second)
        on = refresh(on)
        restored = SldprtArchive.from_bytes(on.BytesValue)
        require(
            restored.streams == on.StreamsValue,
            "complete generated ambient container did not round trip",
        )
        linked = ReadNativeLink(restored, 0)
        emitted, _ = WriteConfigMut(
            linked.ConfigValue.RootValue, 19000, linked.ConfigValue.HeaderValue
        )
        require(
            emitted == restored.require("Contents/Config-0"),
            "typed ambient Config-0 did not round trip",
        )
        require(
            same_owners(on) == owners,
            "authored ambient changed geometry owners or update flags",
        )
        require(
            on.HeaderValue.FieldsValue["f38"] is on.TopHeader.FieldsValue["f38"],
            "ambient headers lost the actual common file definition",
        )
        members = linked.ConfigValue.RootValue.FieldsValue["f1e0"].FieldsValue["f60"][
            "list"
        ]["items"]
        require(
            len(members) == 1
            and members[0]["o"].ClassValue.NameValue == "moAmbientLight_c",
            "ambient member is not its actual nested concrete owner",
        )
        require(
            members[0]["o"].FieldsValue["f08"] == old_next,
            "ambient member did not use the actual next persistent ID",
        )
        require(
            off.StreamsValue["Contents/Definition"]
            == on.StreamsValue["Contents/Definition"],
            "ambient changed the part Definition",
        )
    finally:
        active = False
    require(not denied, "ambient generation made runtime I/O")
    changed = {
        name
        for name in off.StreamsValue
        if off.StreamsValue[name] != on.StreamsValue[name]
    }
    expected = {
        "Header2",
        "Contents/Config-0-ModelHeader",
        "Contents/Config-0",
        "Contents/CMgr",
        "Contents/Config-0-ResolvedFeatures",
    }
    require(
        set(off.StreamsValue) == set(on.StreamsValue) and changed == expected,
        "ambient has an unclassified stream delta",
    )
    require(
        off.StreamsValue["Contents/Config-0-Partition"]
        == on.StreamsValue["Contents/Config-0-Partition"],
        "authored ambient changed the generated kernel partition",
    )
    out.mkdir(parents=True)
    for mode, candidate in (("Off", off), ("On", on)):
        path = out / "Frozen" / mode / child_path.name
        path.parent.mkdir(parents=True)
        with path.open("xb") as stream:
            stream.write(candidate.BytesValue)
    write_json(out / "BaselineReproduction.json", original)
    circle = off.PlanValue.CircleValue
    depth = off.PlanValue.DepthValue
    radius = circle.RadiusValue
    prediction = {
        "volume": pi * radius * radius * depth,
        "area": 2 * pi * radius * (radius + depth),
        "com": [*circle.CenterValue, depth / 2],
        "radius_m": radius,
        "depth_m": depth,
        "radial_parameter": "D1@RoundProfile",
        "radial_value_m": 2 * radius,
        "depth_parameter": "D1@RoundBoss",
        "child_configuration": off.PlanValue.ConfigName,
        "bodies": 1,
    }
    write_json(out / "GeometryPrediction.json", prediction)
    difference = {
        "schema": "kit.sw2026.concentric-ambient-stream-diff.v1",
        "neutral_sha256": sha256(neutral_raw).hexdigest(),
        "ambient_intent_sha256": sha256(ambient_raw).hexdigest(),
        "default_route_exact": True,
        "same_encoded_child_locator": str(child_path),
        "same_owners": owners,
        "allocated_light_id": old_next,
        "next_id_after_light": on.HeaderValue.FieldsValue["f08"],
        "new_configuration_progress": on.CurrentConfig.FieldsValue["f85c"],
        "changed_streams": sorted(changed),
        "streams": {
            name: {
                mode: {
                    "bytes": len(candidate.StreamsValue[name]),
                    "sha256": sha256(candidate.StreamsValue[name]).hexdigest(),
                }
                for mode, candidate in (("Off", off), ("On", on))
            }
            for name in sorted(off.StreamsValue)
        },
        "same_process_repeat_exact": True,
        "construction_runtime_io_attempts": 0,
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "parameter_edits": 0,
        "native_processes_started": 0,
    }
    write_json(out / "StreamDifference.json", difference)
    copyfile(args.neutral, out / "Neutral.json")
    copyfile(args.ambient, out / "AmbientIntent.json")
    return {
        "output": str(out),
        "difference_sha256": digest(out / "StreamDifference.json"),
        "off_sha256": sha256(off.BytesValue).hexdigest(),
        "on_sha256": sha256(on.BytesValue).hexdigest(),
        "native_acceptance": False,
        "changed_streams": sorted(changed),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--neutral", type=Path, required=True)
    parser.add_argument("--ambient", type=Path, required=True)
    parser.add_argument("--ambient-sha256", required=True)
    parser.add_argument("--native-child", required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
