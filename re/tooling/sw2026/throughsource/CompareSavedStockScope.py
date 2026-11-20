from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent.parent)]

from AuditThroughAllDisclosed import graph, node_ref, require, roundtrip

SOURCES = {
    "resolved_selection": (
        "ThroughMultiStock03",
        "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3",
    ),
    "unrestricted": (
        "ThroughAllBodies02",
        "f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22",
    ),
}
ROLES = ("SteadyStock", "MovingStock", "ThroughFeature")


def digest(raw):
    return sha256(raw).hexdigest()


def atoms(fields, lane):
    group = fields.get(lane)
    return [] if group is None else [row["o"] for row in group["items"]]


def examine(root, packet, source_sha):
    path = root / packet / "DisclosedNative/ThroughMultiStock.SLDPRT"
    original = path.read_bytes()
    require(not path.is_symlink() and digest(original) == source_sha, "wrong disclosed native save")
    archive, link, _, names = graph(original)
    require(archive.format_version == 4 and link.ConfigValue.VersionValue == 19000,
            "the exact current format is required")
    for report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue):
        require(report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"],
                "the typed archive is incomplete")

    manager = [row["o"] for row in link.ConfigValue.RootValue.FieldsValue["fd88"]["atoms"]]
    steps = [names[name] for name in ROLES]
    owned, spared, cut = steps
    fields = cut.FieldsValue
    require(len(manager) == 3 and len(set(manager)) == 3, "the three managed atoms must be distinct")
    for feature, atom in zip(steps, reversed(manager), strict=True):
        require(atoms(feature.FieldsValue, "f528") == [atom] and atom.FieldsValue["f12c"] == feature.FieldsValue["f08"],
                "a producing feature lost the actual managed atom")
    require(atoms(fields, "f530") == [manager[-1]] and not atoms(spared.FieldsValue, "f530"),
            "the initial cut must consume only the actual stationary stock")
    wrappers = atoms(fields, "f548")
    if wrappers:
        wrapper, = wrappers
        require(wrapper.FieldsValue["f18"] == manager[-1].FieldsValue["f140"]
                and wrapper.FieldsValue["f108"] == owned.FieldsValue["f08"]
                and wrapper.FieldsValue["f58"].FieldsValue["owner"] is link.ConfigValue.RootValue,
                "the scope wrapper lost its selected producer or document identity")
    streams = roundtrip(archive, link)
    require(len(streams) == 6 and all(row["byte_identity"] for row in streams.values()),
            "linked streams did not replay exactly")
    require(digest(path.read_bytes()) == source_sha, "the original save changed")
    return {
        "source_sha256": source_sha,
        "contained_bytes": len(original),
        "f544": fields["f544"],
        "has_f548": fields["has_f548"],
        "selected_wrappers": [node_ref(row) for row in wrappers],
        "operation_f810": [feature.FieldsValue["f810"] for feature in steps],
        "atom_map": [[atom.IndexValue, atom.FieldsValue["f140"], atom.FieldsValue["f12c"],
                      atom.FieldsValue["f144"]] for atom in manager],
        "initial_consumed_map_slot": manager[-1].IndexValue,
        "initial_unconsumed_map_slot": manager[1].IndexValue,
        "initial_cut_result_map_slot": manager[0].IndexValue,
        "linked_streams": streams,
        "container_stream_hashes": {row.name: digest(row.data) for row in archive.records},
    }


def main():
    parser = ArgumentParser(description="Compare exact disclosed scoped and unrestricted native saves")
    parser.add_argument("--disclosed-root", type=Path, required=True)
    args = parser.parse_args()
    cases = {label: examine(args.disclosed_root, *source) for label, source in SOURCES.items()}
    selected, unrestricted = cases.values()
    require((selected["f544"], selected["has_f548"], len(selected["selected_wrappers"])) == (1, 1, 1)
            and (unrestricted["f544"], unrestricted["has_f548"], len(unrestricted["selected_wrappers"])) == (0, 0, 0),
            "the exact observed scope alternatives differ")
    for field in ("operation_f810", "atom_map", "initial_consumed_map_slot",
                  "initial_unconsumed_map_slot", "initial_cut_result_map_slot"):
        require(selected[field] == unrestricted[field], "initial body ownership differs across the scope contrast")
    outcome = {
        "schema": "kit.sw2026.disclosed-through-all-saved-scope-contrast.v1",
        "cases": cases,
        "native_files_written": 0,
        "sealed_payloads_read": 0,
        "production_coverage": 0,
        "heldout_coverage": 0,
    }
    print(json.dumps(outcome, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
