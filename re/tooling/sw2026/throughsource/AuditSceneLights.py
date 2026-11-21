from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from struct import pack_into, unpack_from
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent.parent)]

from AuditThroughAllDisclosed import graph, node_ref, require, roundtrip, values
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut


PINS = {"One":"b2772eebfd9f11038f72c76fe3a6ace4b9cd45373425f75921be45174943edb7","Two":"287f64869f8d037ebf3c92712453440e3f162beb6d1ac9226afd215d965b7dba","Properties":"e9100de35950b69eb0397ae86d28b800809c2bcfdc440a7f2a54c6b80c8db1c5"}
SCENE_POSITIONS = {"One": (20822, 21668), "Two": (20822, 21989), "Properties": (20822, 22033)}
STREAM = "Contents/Config-0"
BAG_WINDOW = (21509, 21557)
BAG_SHA = "21d2b9b2a930cf37417c11486aa6a9ffc131de2bc26f3049c44194d5374579a5"


def digest(data):
    return sha256(data).hexdigest()


def property_wire(data):
    start, end = BAG_WINDOW
    bag = data[start:end]
    count, real_kind, real, integer_kind, integer, text_kind = unpack_from("<iIfIiI", bag)
    marker, characters = bag[24:27], bag[27]
    require((count, real_kind, integer_kind, text_kind) == (3, 0, 1, 2)
            and marker == b"\xff\xfe\xff" and len(bag) == 28 + characters * 2, "typed property frame differs")
    text = bag[28:].decode("utf-16-le")
    require(digest(bag) == BAG_SHA and (real, integer, text) == (0.375, -73, "frame-λ-21"),
            "the native light property values differ")
    return {"window": BAG_WINDOW, "sha256": BAG_SHA, "wide_characters": characters,
            "rows": {"n": count, "props": [{"kind": 0, "v": real}, {"kind": 1, "v": integer}, {"kind": 2, "v": text}]}}


def bad_kind_refusals(data, header):
    outcomes = []
    for pos in (4, 12, 20):
        corrupt = bytearray(data)
        pack_into("<I", corrupt, BAG_WINDOW[0] + pos, 3)
        try:
            ReadConfigMut(bytes(corrupt), 19000, header)
        except ValueError as error:
            require("user property kind" in str(error), "unsupported property refused at the wrong boundary")
            outcomes.append({"kind_word_offset": BAG_WINDOW[0] + pos, "diagnostic": str(error)})
        else:
            raise ValueError("unsupported user property kind was admitted")
    return outcomes


def read_part(root, label, pin):
    source = root / (label + "Lights.SLDPRT")
    raw = source.read_bytes()
    require(not source.is_symlink() and digest(raw) == pin, "wrong disclosed native source")
    archive, link, _, _ = graph(raw)
    config = link.ConfigValue
    require(config.ReportValue["completed"] and not config.ReportValue["missing_schemas"]
            and not config.ReportValue["provisional_schemas"], "the current configuration graph is incomplete")
    scene = config.RootValue.FieldsValue["f1e0"]
    children = tuple(row["o"] for row in scene.FieldsValue["f60"]["list"]["items"])
    names = ["Ambient", "Directional1"] + ([] if label == "One" else ["Directional2"])
    classes = ["moAmbientLight_c", *["moDirectionLight_c"] * (len(names) - 1)]
    member_rows = [node_ref(node) | {"properties": values(node.FieldsValue["f500"])} for node in children]
    require((scene.StartOffset, scene.EndOffset) == SCENE_POSITIONS[label]
            and [row["name"] for row in member_rows] == names and [row["class"] for row in member_rows] == classes,
            "the original scene owners or physical boundaries differ")
    streams = roundtrip(archive, link)
    require(len(streams) == 6 and all(row["byte_identity"] for row in streams.values()),
            "the six linked streams did not replay")
    data = archive.require(STREAM)
    output = {"source_sha256": pin, "configuration_sha256": digest(data),
              "scene": node_ref(scene), "children": member_rows, "replayed_streams": streams}
    if label == "Properties":
        frame = property_wire(data)
        require(member_rows[1]["properties"] == frame["rows"], "typed properties disagree with independent wire read")
        output["properties_wire"] = frame
        output["bad_kinds"] = bad_kind_refusals(data, config.HeaderValue)
    require(digest(source.read_bytes()) == pin, "the original native file changed")
    return output


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed-root", type=Path, required=True)
    args = parser.parse_args()
    result = {name: read_part(args.disclosed_root, name, pin) for name, pin in PINS.items()}
    print(json.dumps({"cases": result, "heldout_coverage": 0, "native_files_written": 0,
                      "sealed_payloads_read": 0, "production_conversion_coverage": 0},
                     indent=2, sort_keys=True, ensure_ascii=True))


if __name__ == "__main__":
    main()
