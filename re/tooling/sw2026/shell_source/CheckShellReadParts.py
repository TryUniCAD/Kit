from argparse import ArgumentParser
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from math import isclose, ulp
from pathlib import Path
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent)]

from CheckPartitionMarks import CONTROLS, NATIVE, guard_runtime, load_case
from MakeShellReadShape import build_shell
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import ReadXmtStages
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep, EncodeBrep
from convert.adapters.solidworks.Core.Partition.PartTopology import LinearPartBox
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.CheckShellCache import CheckShellCache
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.SummarizeShell import SummarizeShell
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellFootprint import ShellFootprint
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


def refusal(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), str(error)
        return str(error)
    raise ValueError("unexpected shell reader admission")


def history():
    active, delta, source = load_case(CONTROLS["one_light"])
    old_active, old_delta, _ = load_case(NATIVE["ladder"])
    accesses = guard_runtime()
    nodes = ReadActiveNodes(active)
    stages = ReadXmtStages(delta, nodes, (3, 10, 13))
    marks = [row.MarkValue.Integer("id") for row in stages]
    live = [row.NodesValue[1].Integer("body") for row in stages]
    counts = [len(row.NodesValue) for row in stages]
    effect = stages[0].UndoValue
    assert effect is not None
    rows = [len(effect.RestoredValue), len(effect.RemovedValue), len(effect.PreviousValue), effect.CopyCapacity]
    assert (marks, live, counts, rows) == ([13, 10, 3, 1], [2, 2, 0, 0], [207, 169, 27, 27], [6, 44, 32, 35])
    assert stages[1].NodesValue[2] is not nodes[2] and stages[1].NodesValue[2] in effect.PreviousValue
    assert ReadHistMarks(old_delta, ReadActiveNodes(old_active)) == (7, 3)
    wrong_owner = refusal(lambda: ReadXmtStages(delta, nodes, (3, 10, 14)), "actual controller")
    legacy = refusal(lambda: ReadHistMarks(delta, nodes), "current kernel framing differs")
    assert not accesses
    return {
        "source_sha256": source["source_sha256"], "active_sha256": sha256(active).hexdigest(),
        "history_sha256": sha256(delta).hexdigest(), "marks": marks, "body_slots": live,
        "node_counts": counts, "retained_rows": rows, "other_controller_refused": wrong_owner,
        "delete_only_refusal": legacy, "delete_only_control_marks": [7, 3], "runtime_data_reads": 0,
    }


def rounding():
    import_module("interchange.brep.Validation.BrepValidate")
    accesses = guard_runtime()
    bounds = BoundingBox(SpaceVector(-12.45, -9.15, 0.0), SpaceVector(27.125, 32.375, 29.6))
    thickness = 1.35
    footprint = ShellFootprint(bounds, thickness)
    edge = bounds.maximum.x
    exact, near, far = (
        DecodeBrep(EncodeBrep(build_shell(bounds, thickness, right)))
        for right in (edge, edge + 4 * ulp(edge), edge + 80 * ulp(edge))
    )
    assert exact is not None and near is not None and far is not None
    check = []
    for model in (exact, near, far):
        actual = LinearPartBox(model)
        assert actual is not None
        check.append(actual.maximum.x - bounds.maximum.x)
    tolerance = footprint.CornerTolerance()
    assert abs(check[0]) <= tolerance and 0 < check[1] <= tolerance < check[2]
    for model in (exact, near):
        CheckShellCache(model, footprint)
    rejected = refusal(lambda: CheckShellCache(far, footprint), "matching footprint position")
    summary, centre = SummarizeShell(near, footprint)
    assert summary.bounding_box == LinearPartBox(near)
    assert summary.bounding_box.maximum.x > bounds.maximum.x
    volume, area = summary.volume, summary.surface_area
    dx, dy, dz = 39.575, 41.525, 29.6
    inner_x, inner_y, inner_z = dx - 2 * thickness, dy - 2 * thickness, dz - thickness
    expected_volume = dx * dy * dz - inner_x * inner_y * inner_z
    expected_area = 2 * (dx * dy + dz * (dx + dy) + inner_z * (inner_x + inner_y))
    expected_centre = (
        bounds.minimum.x + dx / 2,
        bounds.minimum.y + dy / 2,
        (dx * dy * dz**2 - inner_x * inner_y * inner_z * (dz + thickness))
        / (2 * expected_volume),
    )
    assert isclose(volume, expected_volume, rel_tol=1e-13)
    assert isclose(area, expected_area, rel_tol=1e-13)
    assert all(isclose(actual, expected, rel_tol=1e-13)
               for actual, expected in zip(centre, expected_centre, strict=True))
    assert not accesses
    return {
        "complete_topology": [len(near.faces), len(near.edges), len(near.vertices)],
        "extent_differences_mm": check, "tolerance_mm": tolerance, "out_of_budget_refusal": rejected,
        "mass_properties": {"volume_mm3": volume, "area_mm2": area, "centroid_mm": centre},
        "runtime_data_reads": 0,
    }


def main():
    parser = ArgumentParser()
    modes = {"history": history, "rounding": rounding}
    parser.add_argument("mode", choices=("measure", *modes))
    args = parser.parse_args()
    if args.mode == "measure":
        answer = {
            name: loads(check_output(
                (sys.executable, "-I", "-B", str(HERE), name), timeout=45,
            ))
            for name in modes
        }
    else:
        answer = modes[args.mode]()
    print(dumps(answer, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
