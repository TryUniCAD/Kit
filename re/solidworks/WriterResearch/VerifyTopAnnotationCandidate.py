from argparse import ArgumentParser
from base64 import b64decode
from io import BytesIO
from pathlib import Path
from struct import unpack_from
import subprocess
import sys

from ComposeTopAnnotation import (
    KResolvedFeaturesStream, REQUEST_SCHEMA, ROOT, SpaceVector, Transform,
    canonical_json, digest, read_record, read_request, ToData, SldprtArchive,
)
from convert import open_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative


def make_request(neutral: dict) -> bytes:
    configuration, = neutral["configurations"]["$tuple"]
    origin = SpaceVector(0.0, 0.0, 0.0)
    x_axis = SpaceVector(1.0, 0.0, 0.0)
    y_axis = SpaceVector(0.0, 0.0, 1.0)
    z_axis = SpaceVector(0.0, -1.0, 0.0)
    return canonical_json({
        "schema": REQUEST_SCHEMA,
        "document": neutral,
        "annotation_view": {
            "configuration_id": configuration["id"],
            "role": "top",
            "projection": "orthographic",
            "frame_direction": "view_to_model",
            "origin_unit": "mm",
            "transform": ToData(Transform(origin, x_axis, y_axis, z_axis)),
        },
    })


def replay(request: Path, scratch: Path, locator: str, epoch: int) -> tuple[bytes, dict]:
    process = subprocess.run([
        sys.executable, str(Path(__file__).with_name("ComposeTopAnnotation.py")),
        "--request", str(request), "--native-locator", locator,
        "--written-at", str(epoch), "--scratch", str(scratch),
    ], check=True, stdout=subprocess.PIPE)
    result = read_record(process.stdout)
    archive_path = scratch / result["archive"]["path"]
    manifest_path = scratch / result["manifest"]["path"]
    archive = archive_path.read_bytes()
    manifest = manifest_path.read_bytes()
    if digest(archive) != result["archive"]["sha256"] or digest(manifest) != result["manifest"]["sha256"]:
        raise ValueError("fresh process custody hashes differ from its published bytes")
    return archive, read_record(manifest)


def compare_readback(before, after, scope: tuple[str, ...], delta: int) -> dict:
    report = {"owner_indexes": 0, "retained_records": 0, "compact_class_tags": 0}

    def compare(left, right, path):
        if left == right:
            return
        if type(left) is dict and type(right) is dict and left.keys() == right.keys():
            for key, value in left.items():
                compare(value, right[key], (*path, key))
            return
        if type(left) is list and type(right) is list and len(left) == len(right):
            for index, (first, second) in enumerate(zip(left, right, strict=True)):
                compare(first, second, (*path, index))
            return
        archive_owner_index = (
            "typed_archive_owner" in path
            and path[-1] in ("object_index", "dimension_index", "handle_index", "display_index")
        )
        point_handle_index = "native_point_rows" in path and "line_handles" in path and path[-1] == "object_index"
        if archive_owner_index or point_handle_index:
            if type(left) is int and type(right) is int and right - left == delta:
                report["owner_indexes"] += 1
                return
        if path[0] == "feature_timeline" and path[-4:] == ("definition", "object_data", "record_data", "$bytes"):
            original, relocated = b64decode(left, validate=True), b64decode(right, validate=True)
            if len(original) == len(relocated):
                offsets = [i for i, (a, b) in enumerate(zip(original, relocated, strict=True)) if a != b]
                if all(i + 1 < len(original) and original[i + 1] == relocated[i + 1] == 0x80
                       and unpack_from("<H", relocated, i)[0] - unpack_from("<H", original, i)[0] == delta
                       for i in offsets):
                    report["retained_records"] += 1
                    report["compact_class_tags"] += len(offsets)
                    return
        raise ValueError(f"strict SDK readback differs outside expected archive relocation at {path}")

    left, right = before.to_dict(), after.to_dict()
    for field in scope:
        compare(left[field], right[field], (field,))
    return report


def run(scratch: Path) -> dict:
    scratch.mkdir(parents=True, exist_ok=False)
    neutral = ROOT / "re/solidworks/measurements/2026/EncoderRoundTrip/Requests/BaselineReconstruction.json"
    request_path = scratch / "Request.json"
    request = make_request(read_record(neutral.read_bytes()))
    request_path.write_bytes(request)
    document, _ = read_request(request)
    locator, epoch = r"C:\KitA12bResearch\reconstruction.SLDPRT", 1785626030
    if sys.platform == "win32" and Path(locator).exists():
        raise ValueError("research contrast requires its synthetic locator to be absent")
    annotated, receipt = replay(request_path, scratch / "First", locator, epoch)
    repeated, second = replay(request_path, scratch / "Second", locator, epoch)
    if annotated != repeated or receipt != second:
        raise ValueError("fresh persisted-JSON writers did not reproduce the candidate")

    plain = PrepareNative(document, BytesIO(), epoch, WriteOptions(values={"final_destination": locator}))
    archive = SldprtArchive.from_bytes(annotated, locator)
    changed = sorted(name for name, stream in plain.StreamsValue.items() if archive.Require(name) != stream)
    if changed != ["Contents/Config-0", KResolvedFeaturesStream] or set(plain.StreamsValue) != set(receipt["streams"]):
        raise ValueError("adding the Top annotation altered an unrelated stream")
    baseline = open_document(plain.BytesValue, source_format="solidworks.sldprt", strict=True)
    candidate = open_document(annotated, source_format="solidworks.sldprt", strict=True)
    compared = ("configurations", "parameters", "support_planes", "sketches", "feature_timeline", "bodies", "brep")
    delta = receipt["typed_readback"]["config_next_slot"] - plain.ConfigValue.MapValue.CounterValue
    if delta != 2:
        raise ValueError("Top annotation did not allocate exactly its class and object")
    relocation = compare_readback(baseline, candidate, compared, delta)
    plain_dir = scratch / "Plain"
    plain_dir.mkdir(exist_ok=False)
    plain_path = plain_dir / receipt["archive"]["path"]
    plain_path.write_bytes(plain.BytesValue)
    return {
        "candidate": receipt,
        "changed_streams": changed,
        "exact_child_processes": 2,
        "plain_archive_sha256": digest(plain.BytesValue),
        "plain_config_next_slot": plain.ConfigValue.MapValue.CounterValue,
        "strict_sdk_fields_compared": compared,
        "strict_sdk_archive_relocations": relocation,
        "sdk_depth_mm": candidate.parameters[0].value.value,
        "sdk_volume_mm3": candidate.bodies[0].topology.volume,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Replay a whole-part Top annotation candidate in two fresh offline processes")
    parser.add_argument("--scratch", type=Path, required=True)
    sys.stdout.buffer.write(canonical_json(run(parser.parse_args().scratch)))
