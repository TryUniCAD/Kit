from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps
from math import prod
from pathlib import Path, PureWindowsPath
from sys import addaudithook

from .ArchiveAttachment import ACTIVE_HEADER, CONFIG, MANAGER, MODEL_HEADER, RESOLVED, FeatureUpdate, archive_for_oracle
from .CheckProjection import assert_face_ids, close, schedule
from .Geometry import plan_rectangle
from .RectangleAttributes import Appearance
from .RectanglePartition import project_rectangle
from builders.ConfigurationHeader import CONFIGURATION_MANAGER_HEADER
from builders.Metadata import FILE_VERSION
from builders.Part import construct_part
from Classes import registry
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KPartitionStream
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved
from para.CompareRectangle import native_geometry, ownership
from para.Partition import frame_payloads, read_partition, write_payloads
from Streams import load_rooted, store_rooted
from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput


CASE = (2.625, -12.75, 25.875, 1.75, 8.75)
VARIANTS = ("WithoutPartition", "WithAttachment")
CASE_NAME = "PartitionProbeChild.SLDPRT"
MODIFIED_AT = 1794700033


def neutral_request(path, extents=CASE, *, modified_at=MODIFIED_AT):
    x1, y1, x2, y2, depth = extents
    planar = tuple((x, y) for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)))
    request = MakePartInput([[x / 1000, y / 1000] for x, y in planar], depth / 1000, path.stem)
    request["document"].update(configuration_name="Default", density_kg_m3=1000.0, rectangle_dimensions={
        "width_text_m": [(x1 + x2) / 2000, (y1 - 4) / 1000],
        "height_text_m": [(x2 + 4) / 1000, (y1 + y2) / 2000],
        "route_centerline": False,
    })
    request["provenance"]["modified_at"] = modified_at
    request["output"] = {"path_name": str(path), "saved_at": modified_at + 28}
    return request


def verify_archive(data, registry, child, plan):
    archive = SldprtArchive.from_bytes(data)
    doc, read = load_config(archive.require(CONFIG), registry, FILE_VERSION, archive=archive)
    resolved, _ = load_resolved(archive.require(RESOLVED), registry, FILE_VERSION, archive=archive, name=RESOLVED, seed=read.map_state())
    restored, state = store_config_state(doc, registry, FILE_VERSION)
    assert restored == archive.require(CONFIG) and not doc.tail and state.count == read.count == resolved.head["base"]
    assert store_resolved(resolved, registry, FILE_VERSION, seed=read.map_state()) == archive.require(RESOLVED) and not resolved.tail
    assert state.count > child.configuration_map_count
    model, = doc.roots
    atom, = (row["o"] for row in model["fd88"]["atoms"])
    snapshot, = model["ffe0"]
    assert model["f1010"] == 1 and snapshot["k"] is atom and snapshot["v"] == 0 and not model["f0c"] & 1
    boss, = (feature for feature in resolved.roots if feature.cls == "moExtrusion_c")
    assert boss["has_f3d0"] == 1 and boss["f540"] == 3 and not boss["f0c"] & 1
    assert model["fd88"]["fa8"] == FILE_VERSION
    assert atom["f140"] == model["fd88"]["f260"] and atom["f12c"] == atom["f130"] == boss["f08"]
    rooted = {}
    for name in (ACTIVE_HEADER, MODEL_HEADER, MANAGER, CONFIGURATION_MANAGER_HEADER):
        record, _ = load_rooted(archive.require(name), registry, 1, FILE_VERSION)
        node, = record.roots
        assert not record.tail and store_rooted(record, registry, FILE_VERSION) == archive.require(name)
        rooted[name] = node
    config = rooted[MANAGER]["f360"]
    config_header, = (row["o"] for row in rooted[CONFIGURATION_MANAGER_HEADER]["f08"]["items"])
    assert config["f860"] == config_header["f38"] == rooted[ACTIVE_HEADER]["f40"] == rooted[MODEL_HEADER]["f40"]
    assert config_header["f50"] == model["f1300"]
    assert rooted[ACTIVE_HEADER]["fec"] == rooted[MODEL_HEADER]["fec"] == 1
    for key, value in plan.archive.active_header_fields.items():
        assert rooted[ACTIVE_HEADER][key] == rooted[MODEL_HEADER][key] == value
    stream = archive.require(KPartitionStream)
    partition = read_partition(stream)
    assert frame_payloads(write_payloads(partition)) == stream
    assert_face_ids(partition, child, plan, 1)
    owners = ownership(partition)
    assert (atom["f180"], atom["f1b0"]) == (owners["body_match_tag"],) * 2 and atom["f140"] == owners["atom_id"]
    assert boss["f08"] == owners["last_modifying_feature"] and rooted[MODEL_HEADER]["f44"] == owners["body_stamp"]
    assert boss["f3d0"]["f18"] == partition.history[0].mark.fields["id"]
    assert model["fe38"]["f18"] == partition.history[2].mark.fields["id"]
    return archive.streams, {
        "partition_sha256": sha256(stream).hexdigest(), "atom_id": atom["f140"],
        "shared_blanking_atom": True, "blanking_state": snapshot["v"], "body_match_tag": atom["f180"],
        "map_count": state.count, "cache_free_map_count": child.configuration_map_count,
        "model_mark": model["fe38"]["f18"], "boss_mark": boss["f3d0"]["f18"],
        "model_geometry_stamp": model["f1300"], "header_update_stamp": config["f860"],
        "boss_update_stamp": boss["f29c"], "boss_regeneration_status": boss["f540"],
        "owners": owners,
    }


def make_pair(path):
    reg = registry()
    for encoding in ("utf-8", "utf-16-le", "latin-1"):
        lookup(encoding)
    request = neutral_request(path)
    session = schedule(401, 3, 1, 2, 7, 2, 0, MODIFIED_AT, 3875201)
    events = (
        FeatureUpdate(5, MODIFIED_AT, 1263411, False),
        FeatureUpdate(6, MODIFIED_AT, 2426775, True),
        FeatureUpdate(9, MODIFIED_AT, 4075201, True),
    )
    reading_forbidden = True

    def deny_extra_files(event, arguments):
        if reading_forbidden and event == "open":
            raise RuntimeError("archive candidate accessed a file")

    addaudithook(deny_extra_files)
    try:
        child = construct_part(registry=reg, native_plane_roles=True, **request)
        plan = plan_rectangle(child, session)
        view = project_rectangle(child, plan, Appearance((77, 139, 191), 0.0, request["document"]["density_kg_m3"]))
        candidate = archive_for_oracle(registry=reg, child=child, plan=plan, projection=view, session=session, feature_updates=events)
        without, with_attachment = map(build_sldprt, (child.streams, candidate))
        before = SldprtArchive.from_bytes(without).streams
        after, attachment = verify_archive(with_attachment, reg, child, plan)
    finally:
        reading_forbidden = False
    assert before == child.streams and set(after) - set(before) == {KPartitionStream}
    effects = sorted(key for key in after if before.get(key) != after[key])
    assert set(effects) == {CONFIG, RESOLVED, MODEL_HEADER, MANAGER, ACTIVE_HEADER, CONFIGURATION_MANAGER_HEADER, KPartitionStream}
    x1, y1, x2, y2, depth = CASE
    width, height = x2 - x1, y2 - y1
    bounds = (x1, y1, 0, x2, y2, depth)
    measured = native_geometry(view.partition, bounds)
    assert close(measured["signed_volume_mm3"], prod((width, height, depth)))
    assert close(measured["area_mm2"], 2 * (width * height + width * depth + height * depth))
    assert all(close(a, b) for a, b in zip(measured["center_mm"], ((x1 + x2) / 2, (y1 + y2) / 2, depth / 2), strict=True))
    sets = dict(zip(VARIANTS, (without, with_attachment), strict=True))
    return sets, request, {
        "schema": "kit.sw2026.rectangle-populated-attachment-discovery.v1",
        "native_path": str(path), "standalone_native_acceptance": "unmeasured", "heldout_acceptance": False,
        "construction_and_readback_file_opens": 0,
        "variants": {name: sha256(data).hexdigest() for name, data in sets.items()},
        "geometry": measured, "attachment": attachment,
        "dimensions_m": {"D1@Sketch1": width / 1000, "D2@Sketch1": height / 1000, "D1@Boss-Extrude1": depth / 1000},
        "changed_streams": effects,
    }


def main():
    args = ArgumentParser()
    args.add_argument("output", type=Path)
    args.add_argument("native_path", type=PureWindowsPath)
    values = args.parse_args()
    output = values.output.resolve()
    path = values.native_path
    if output.is_relative_to(Path(__file__).resolve().parents[5]) or not path.is_absolute() or path.name != CASE_NAME:
        raise ValueError("use an external output directory and an absolute Windows PartitionProbeChild.SLDPRT path")
    bytes_by_variant, request, receipt = make_pair(path)
    output.mkdir(parents=True, exist_ok=False)
    (output / "NeutralRequest.json").write_text(dumps(request, indent=2) + "\n", encoding="utf-8")
    for name, data in bytes_by_variant.items():
        directory = output / name
        directory.mkdir()
        (directory / path.name).write_bytes(data)
    (output / "Freeze.json").write_text(dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
