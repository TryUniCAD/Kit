from argparse import ArgumentParser
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProveLocalPatternContainer import ROOT, digest, document_rows, encode, require
from CheckPatternAngleOwners import check_angles, node_fields, point
from ProveTypedLinearPatternArchive import CFG, RESOLVED, measure_controls, verify_link
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive


PREVIOUS = "b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3"
SOURCE_NAMES = {
    "DirectionEnvelope.SLDPRT", "DirectionEnvelopeSpacing.SLDPRT",
    "DatumHeightShort.SLDPRT", "DatumHeightTall.SLDPRT",
}
WIRE_ROOTS = ("moICE_c", "moRefAxis_c", "moRefPlane_c", "moLPattern_c")
PROFILES = ("model_cases", "warm_replay", "static_owners", "changed_streams_for_each_independent_edit", "guarded_processes")


def measure(path, pin, angle):
    raw = path.read_bytes()
    require(digest(raw) == pin, "file differs from the pinned construction or disclosure")
    archive = SldprtArchive.from_bytes(raw)
    link, repeated = verify_link(archive)
    graph = link.ResolvedValue
    roots = graph.RootsValue
    row = {
        "name": path.name, "sha256": pin, "root_count": len(roots),
        "map_base": graph.MapBase, "map_counter": repeated.MapValue.CounterValue,
        "streams": {name: {"bytes": len(archive.require(name)), "sha256": digest(archive.require(name))}
                    for name in (CFG, RESOLVED)},
    }
    if angle is not None:
        require(len(roots) == 24 and tuple(root.ClassValue.NameValue for root in roots[-4:]) == WIRE_ROOTS,
                "shared grammar changed the angular feature inventory")
        axis_data = node_fields(roots[-3].FieldsValue["f700"], "moPlaneInterAxisData_c")
        ends = tuple(point(axis_data[key]) for key in ("f18", "f30"))
        headers = tuple(ReadHeaderGraph(archive.require(name), 19000)
                        for name in (CFG + "-ModelHeader", "Header2"))
        proof = check_angles(link.ConfigValue.RootValue, roots, headers, ends, angle)
        row["selected_ids"] = proof["selected_ids"]
        row["driver"] = proof["driver"]
        row["max_geometric_error"] = max(proof["geometry_errors"].values())
    return row


def main():
    parser = ArgumentParser()
    for name in ("share", "previous", "generation", "candidates", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    previous = args.previous.read_bytes()
    generation = args.generation.read_bytes()
    require(digest(previous) == PREVIOUS, "previous guarded generation differs from the native-tested pin")
    old, current = json.loads(previous), json.loads(generation)
    require(all(current[key] == old[key] for key in PROFILES), "using the shared writer changed prior generation evidence")
    model = current["model_cases"]
    require(len(model) == 2 and all(set(states) == {"original", "pitch_only", "count_only"} for states in model.values()),
            "guarded model contrast is incomplete")
    generated = [measure(args.candidates / (name + ".SLDPRT"), cases["original"]["native_container"]["sha256"],
                         cases["original"]["modeled_input"]["plane"]["angle_rad"])
                 for name, cases in model.items()]
    angle = 0.7853981633974483
    native = [measure(path, pin, angle if path.name in SOURCE_NAMES else None)
              for path, pin, _ in document_rows(args.share)]
    require(SOURCE_NAMES == {row["name"] for row in native if "driver" in row} and len(native) == 10,
            "native archive contrast is incomplete")
    controls = list(measure_controls())
    directory = ROOT / "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved"
    codecs = ("AnchorFields", "AnglePlaneFields", "AxisFields", "ResolvedLayouts", "ResolvedSchemas", "ResolvedVirtuals")
    report = {
        "schema": "kit.sw2026.shared-angular-pattern-wire.v1", "build": "34.5.2.0604",
        "previous_generation_sha256": PREVIOUS, "shared_generation_sha256": digest(generation),
        "all_model_and_disclosed_rows_unchanged": True,
        "model_only_archives_matched": sum(map(len, model.values())), "guarded_generation_processes": current["guarded_processes"],
        "codec_file_sha256": {name: digest((directory / (name + ".py")).read_bytes()) for name in codecs},
        "linked_streams_exact": 2 * (len(generated) + len(native) + len(controls)),
        "generated": generated, "disclosed_native": native, "legacy_controls": controls,
        "native_lifecycles_started": 0, "heldout_inputs_read": 0,
    }
    payload = encode(report)
    with args.output.open("xb") as target:
        target.write(payload)
    print(json.dumps({"sha256": digest(payload), "linked_streams_exact": report["linked_streams_exact"]}))


if __name__ == "__main__":
    main()
