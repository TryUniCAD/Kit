from argparse import ArgumentParser
from math import cos, dist, radians, sin
from pathlib import Path
from struct import unpack
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from AuditPatternEnvelope import SldprtArchive
from CheckPatternAngleOwners import annotation_catalog, check_angles, node_fields, require, roots_of_kind
from PatternAngleWire import ANGLE_PLANE, read_resolved, write_resolved
from PatternEnvelopeSpec import specification
from ProvePatternPlaneDirectionRule import Image, MEASUREMENTS, MODULES, checked, digest, document_rows, double_at, encode, module
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph


PROVEN_HINGE = "7c0f8111ce899b34bbac361f0e2c4394cc8b366a0e98311666d943b9d125c6d2"
SLOTS = {
    "constrained_init": (0x4CED1C20, 0xA0, 0x4B8ED160),
    "adornment_update": (0x4CED1C20, 0x240, 0x4B8EF0C0),
    "adornment_value": (0x4CED1C20, 0xC0, 0x4B8F5990),
    "angular_label_update": (0x4D247828, 0x9C0, 0x4C866BD0),
    "previous_label_update": (0x4D247828, 0x9C8, 0x4C866DB0),
    "label_radius_getter": (0x4D247828, 0x5F0, 0x4B349250),
}
RANGES = {
    "authoring_angle_normal": (0x4B8EE700, 0x4B8EEBDE, "49cbdd7653238a89f1e47da4ddac310658eb752856c9ffd2e94c5148528ebd3b"),
    "ordinary_angle_adornment": (0x4B8F4FA0, 0x4B8F5986, "a6edd279997adff6f12087cbaf5d0d209ad830959159741ea3d49ff940d20813"),
    "base_default_pick": (0x4C2D7920, 0x4C2D798A, "d4ab19f75ec6267897af4a9e88435504673c54bc471dfe6c058679f900bec08b"),
    "angle_wire_rebind": (0x4B8E2930, 0x4B8E29CD, "e3220c09ebe796dbe8c6b79aa810eeaf956cef3cbb58bedda0dcc6e8b8c723d9"),
    "append_annotation_view": (0x4C015440, 0x4C015454, "8354493aa33e7f1852f21bb54ab1415c16a4cec1983e32482f8865212ca75be1"),
    "label_radius_getter": (0x4B349250, 0x4B349259, "c27ef44139594d06138ccc8a976d550cd6bff034ec500b8247a24ece6504a7e5"),
    "read_actual_annotation_view": (0x4BA69760, 0x4BA697A6, "9b72f0eb0245c4b649825cecb02f83e4f5ee8ade302856a82df66b339116f4ea"),
    "find_registered_model_view": (0x4C026E90, 0x4C0270A0, "e04d0c047f13c1fa1e4d2f5ff33f98d5ec9e805070ea9cd5500e29a503cec0e3"),
    "record_annotation_membership": (0x4BA678E0, 0x4BA67A1F, "b37086e1c70e09ba205580706004c6fbd3e1f93262371321010b5a0aeda7e35a"),
}


def static_owners(directory):
    image = Image(directory / "sldmodu.dll")
    identified = module(image, MODULES[image.path.name])
    slots = {}
    for role, (table, offset, target) in SLOTS.items():
        require(unpack("<Q", image.bytes(table + offset, table + offset + 8))[0] == target,
                "build-bound constrained angle slot changed")
        slots[role] = tuple(hex(value) for value in (table, offset, target))
    spans = {}
    for role, (start, end, expected) in RANGES.items():
        actual = digest(image.bytes(start, end))
        require(actual == expected, "exact constrained angle code span changed")
        spans[role] = {"range": [hex(start), hex(end)], "sha256": actual}
    require(double_at(image, 0x4CDDCD28) == 0.001 and double_at(image, 0x4CD9A3C0) == 0.5,
            "angular witness length or selected midpoint seed changed")
    return {"module": identified, "slots": slots, "spans": spans,
            "native_witness_radius_m": {"address": "0x4cddcd28", "value": 0.001},
            "native_midpoint_seed": {"address": "0x4cd9a3c0", "value": 0.5}}


def exact_config(path, pin):
    archive = SldprtArchive.from_bytes(checked(path, pin))
    raws = [archive.require(name) for name in ("Contents/Config-0-ModelHeader", "Header2", "Contents/Config-0")]
    headers = tuple(ReadHeaderGraph(raw, 19000) for raw in raws[:2])
    config = ReadConfigMut(raws[2], 19000, headers[0])
    cfg_bytes, written = WriteConfigMut(config.RootValue, 19000, headers[0])
    require(cfg_bytes == raws[2] and config.MapValue == written.MapValue, "complete ordinary Config-0 graph changed bytes or aliases")
    return archive, headers, config, cfg_bytes


def catalog_status(model):
    rows = annotation_catalog(model)
    fields = model.FieldsValue
    require(rows and fields["feb0"] == max(row["f360"] for row in rows), "annotation ID frontier does not match the actual registered rows")
    return {"views": [{"name": row["f358"], "id": row["f360"]} for row in rows],
            "feb0": fields["feb0"], "feb4": fields["feb4"], "fec0": fields["fec0"]}


def refusals(model, roots, headers, ends, angle, measured):
    key = measured["feature"]["id"]
    (feature,) = [root for root in roots_of_kind(roots, "moRefPlane_c") if root.FieldsValue["f08"] == key]
    data = node_fields(feature.FieldsValue["f6f8"], ANGLE_PLANE)
    display = node_fields(data["f150"], "moDisplayAngularDim_c")
    handle = node_fields(display["f850"][0]["o"], "moFeatureDimHandle_c")
    dimension = node_fields(handle["ff0"], "AngleDim_c")
    value = node_fields(dimension["f28"], "moAngleParameter_c")
    interface = node_fields(data["f88"], "moConstraintRefplaneInterfaceData_c")
    probes = (
        ("camera_id_as_annotation_id", display, "f2b0", [{"v": measured["driver"]["standard_view_id"]}]),
        ("crossed_constraint_row", interface, "f10", interface["f18"]),
        ("absent_third_geometry", interface, "f18", None),
        ("different_live_driver", value, "f58", angle / 2),
    )
    rejected = {}
    for name, owner, field, changed in probes:
        original = owner[field]
        owner[field] = changed
        try:
            check_angles(model, roots, headers, ends, angle)
        except ValueError as error:
            rejected[name] = str(error)
        finally:
            owner[field] = original
    require(len(rejected) == len(probes), "one malformed angle ownership path did not refuse")
    return rejected


def disclosed(share):
    hinge = json.loads(checked(MEASUREMENTS / "LocalLinearPatternFiniteHinge01.json", PROVEN_HINGE))
    ends = {name: tuple(map(tuple, case["from_authored_boxes"]["ordered_endpoints_m"]))
            for case in hinge["disclosed_cases"].values() for name in case["typed_saves"]}
    standard_rows, angles = {}, {}
    angle = specification()["direction_datum"]["arguments"][1]
    for path, pin, row in document_rows(share):
        if row["plane_data_class"] != ANGLE_PLANE and path.name not in ("D01X.SLDPRT", "D02Y.SLDPRT"):
            continue
        archive, headers, config, cfg_bytes = exact_config(path, pin)
        model = config.RootValue
        status = catalog_status(model)
        if row["plane_data_class"] != ANGLE_PLANE:
            standard_rows[path.name] = {"sha256": pin, **status}
            continue
        manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
        link = MakeLinkContext(config, manager)
        resolved = archive.require("Contents/Config-0-ResolvedFeatures")
        roots, extra, read_map = read_resolved(resolved, config.MapValue, link, source_replay=True)
        reconstructed, write_map = write_resolved(roots, extra, config.MapValue, link, source_replay=True)
        require(reconstructed == resolved and read_map == write_map and extra is not None,
                "constrained angle changed complete ResolvedFeatures bytes or its linked map")
        result = check_angles(model, roots, headers, ends[path.name], angle)
        result.update(sha256=pin, config_bytes=len(cfg_bytes), resolved_bytes=len(resolved), root_count=len(roots),
                      map_counters=[config.MapValue.CounterValue, write_map.CounterValue], annotation_catalog=status,
                      refusals=refusals(model, roots, headers, ends[path.name], angle, result))
        angles[path.name] = result
    require(len(angles) == 4 and len(standard_rows) == 2 and len({row["views"][1]["name"] for row in standard_rows.values()}) == 2,
            "the two unrelated annotation owner contrasts or the four angled disclosures changed")
    return angles, standard_rows


def predict(label, width, depth, angle_deg):
    angle = radians(angle_deg)
    request = {"plate_box_m": ((0.0, 0.0, 0.0), (width, 0.08875, 0.00475)),
               "raised_box_m": ((0.03125, 0.0185, 0.0), (0.0425, 0.03625, depth)),
               "angle_rad": angle, "reverse": False}
    raw = encode(request)
    argv = (sys.executable, "-I", "-B", str(HERE.with_name("PatternAngleModelProcess.py")))
    first, second = (run(argv, cwd=ROOT, input=raw, capture_output=True, check=True, timeout=10) for _ in range(2))
    require(not first.stderr and not second.stderr and first.stdout == second.stdout, "independent neutral angle prediction is not deterministic")
    receipt = json.loads(first.stdout)
    predicted = receipt["analytic_geometry"]
    center = predicted["witness_points_m"][2]
    independently_expected = (depth * 0.55 * sin(angle), depth * 0.55 * cos(angle), depth * 0.5)
    require(not receipt["archive_written"] and receipt["guarded_runtime_reads"] == 0 and len(receipt["refusals"]) == 3
            and dist(center, independently_expected) < 5e-17
            and abs(predicted["ray_separation_m"] - 0.002 * sin(angle * 0.5)) < 5e-17,
            "independent closed-form witness prediction or pure process scope differs")
    return {"case": label, "neutral_request_sha256": digest(raw), "independent_witness_center_m": independently_expected, **receipt}


def main():
    parser = ArgumentParser()
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    models = [predict("AcuteA", 0.12725, 0.017375, 28.625), predict("AcuteB", 0.148125, 0.026125, 63.125)]
    bindings = static_owners(args.binaries)
    sources, camera_contrasts = disclosed(args.disclosed_share)
    result = {"schema": "kit.sw2026.research-only.constrained-angle-owner.v1", "source_hinge_evidence_sha256": PROVEN_HINGE,
              "static_ownership": bindings, "disclosed_cases": sources, "principal_annotation_contrasts": camera_contrasts,
              "authored_predictions": models, "guarded_prediction_processes": 4, "generated_archives": 0,
              "native_calls": 0, "heldout_inputs_read": 0, "remaining_writer_gate": "derive and preserve model-owned annotation view publication and complete angular display placement state",
              "tools": {name: digest(HERE.with_name(name).read_bytes()) for name in (
                  "CheckPatternAngleOwners.py", "PatternAngleGeometry.py", "PatternAngleModelProcess.py", "PatternAngleWire.py", HERE.name)}}
    with args.output.open("xb") as stream:
        stream.write(encode(result))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
