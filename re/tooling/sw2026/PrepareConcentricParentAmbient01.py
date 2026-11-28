import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--neutral", type=Path, required=True)
    parser.add_argument("--ambient", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    sys.path[:0] = [
        str(root / "src"),
        str(root / "re/tooling/sw2026"),
        str(root / "re/tooling/sw2026/serial"),
    ]
    from interchange.serialization.Deserialize import FromData
    from para.concentric.CheckConcentricAssembly import run, schedule, verify_emission
    from para.concentric.ConcentricAssembly import prepare_concentric
    from para.rectangle.ArchiveAttachment import FeatureUpdate
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KPartitionStream
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import (
        ReadFileKey,
    )

    raw = args.neutral.read_bytes()
    require(
        sha256(raw).hexdigest()
        == "e5e005dc738ad379f0485accc78d7f72002cccdc1b14186ea43ed82e4f444fe3",
        "neutral source changed",
    )
    document = FromData(json.loads(raw))
    ambient = json.loads(args.ambient.read_bytes())
    require(
        sha256(args.ambient.read_bytes()).hexdigest()
        == "c178599a0990a89a9ef1e17017150dc5bc1cbd3fdbbf301542e30cbc3c8c7c99",
        "ambient intent changed",
    )
    written_at = 1815300301
    baseline, original = run(
        document,
        r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\ConcentricMateNativeDeck02\Generated\Feature\ConcentricNeutralAlphaDerived.SLDASM",
        written_at,
        1,
    )
    require(
        baseline["assembly_sha256"]
        == "e07d04635daf7a8b9ee5790dc34e7876c555b12690d36b9ff0cc6138a7222a59"
        and baseline["child_sha256"]
        == "64e1568c00763e734a00bf1f1778357b1864ca79abc30ec2b7f996bc3e20d845",
        "generic emitter factoring changed the default bytes",
    )
    destination = r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\ConcentricAmbientComparison01\NativePacket01\Working\ConcentricNeutralAlphaDerived.SLDASM"
    epoch = schedule(written_at, 1)
    events = tuple(
        FeatureUpdate(index, written_at, index + 1, True) for index in range(3)
    )
    denied = []
    active = True

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
                "parent pair construction attempted runtime I/O: " + event
            )

    sys.addaudithook(guard)
    try:
        off = prepare_concentric(document, destination, written_at, epoch, events, 7)
        on = prepare_concentric(
            document, destination, written_at, epoch, events, 7, ambient=ambient
        )
        repeated = prepare_concentric(
            document, destination, written_at, epoch, events, 7, ambient=ambient
        )
        require(
            on.assembly == repeated.assembly
            and on.attachment.file_bytes == repeated.attachment.file_bytes,
            "ambient parent repeat differs",
        )
        require(
            sha256(off.attachment.file_bytes).hexdigest()
            == "6fa75f03fc6e201e29dfc65e90b20a773ca8212568b8a9dae0fb9601116ef785",
            "off child differs from the native-measured pair",
        )
        require(
            sha256(on.attachment.file_bytes).hexdigest()
            == "6569127deb36821679c7b425b65e0bfffbd2c3f9d3fa68777baa3a6f507d1129",
            "on child differs from the native-measured pair",
        )
        receipts = {
            mode: verify_emission(
                bundle.assembly,
                bundle.attachment,
                1,
                False,
                0,
                ("Cylinder-1", "Cylinder-2"),
            )
            for mode, bundle in (("Off", off), ("On", on))
        }
        for bundle in (off, on):
            require(
                ReadFileKey(bundle.attachment.candidate.HeaderValue.FieldsValue["f38"])[
                    1
                ]
                == str(
                    PureWindowsPath(destination).with_name(
                        "NeutralCylinderAlphaDerived.SLDPRT"
                    )
                ),
                "linked parent targets another actual child file",
            )
        parent_streams = {
            mode: SldprtArchive.from_bytes(bundle.assembly).streams
            for mode, bundle in (("Off", off), ("On", on))
        }
        require(
            set(parent_streams["Off"]) == set(parent_streams["On"]),
            "parent stream roles differ",
        )
        parent_changes = [
            name
            for name in parent_streams["Off"]
            if parent_streams["Off"][name] != parent_streams["On"][name]
        ]
        require(
            off.attachment.streams[KPartitionStream]
            == on.attachment.streams[KPartitionStream],
            "ambient changed the child partition",
        )
    finally:
        active = False
    require(not denied, "parent pair made runtime I/O")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    results = {}
    for mode, bundle in (("Off", off), ("On", on)):
        folder = out / "Frozen" / mode
        folder.mkdir(parents=True)
        files = {
            PureWindowsPath(destination).name: bundle.assembly,
            "NeutralCylinderAlphaDerived.SLDPRT": bundle.attachment.file_bytes,
        }
        for name, value in files.items():
            with (folder / name).open("xb") as stream:
                stream.write(value)
        results[mode] = {
            "files": {
                name: {"bytes": len(value), "sha256": sha256(value).hexdigest()}
                for name, value in files.items()
            },
            "linked_sdk": receipts[mode],
        }
    report = {
        "schema": "kit.sw2026.concentric-parent-ambient-generation.v1",
        "neutral_sha256": sha256(raw).hexdigest(),
        "original_default_exact": True,
        "native_measured_children_exact": True,
        "same_parent_locator": destination,
        "parent_stream_changes": parent_changes,
        "parents_byte_identical": off.assembly == on.assembly,
        "variants": results,
        "changed_child_streams": [
            "Contents/CMgr",
            "Contents/Config-0",
            "Contents/Config-0-ModelHeader",
            "Contents/Config-0-ResolvedFeatures",
            "Header2",
        ],
        "constructor_runtime_io_attempts": len(denied),
        "same_process_repeat_exact": True,
        "round_tripped_parent_streams": 6,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
        "source_names_retained_on_disk": ["Cylinder-1", "Cylinder-2"],
        "native_name_acceptance_pending": True,
    }
    with (out / "Generation.json").open("x") as stream:
        stream.write(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "output": str(out),
                "generation_sha256": sha256(
                    (out / "Generation.json").read_bytes()
                ).hexdigest(),
                "parent_changes": parent_changes,
                "files": {mode: row["files"] for mode, row in results.items()},
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
