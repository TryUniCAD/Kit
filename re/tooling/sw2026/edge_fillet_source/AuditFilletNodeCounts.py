from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from AuditFilletArchive import BUILD, ORACLE, checked, digest, guard_runtime, require
from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.BodyTrackIn import (
    BodyTrackIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrDefs import (
    KCylAttrDefs,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylSpan import (
    CylSpan,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.MakeCylTrans import (
    MakeCylTrans,
)
from convert.adapters.solidworks.Archive.Partition.History.CountRollNodes import (
    CountRollNodes,
)
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import (
    ReadXmtStages,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletHist import (
    ReadFilletHist,
)

BASE = "8ea2fa45b285499f1f50c61f04b29c7f0649ebf4"
BASELINE = "a8b954ac2eab2d5064055282cf1f029bec4d0a2ba83c4b09e1023d646f06b849"
AXIAL = "2c29407f931e290fa0cd1262f20af19cb345052432a7ee8f544bc91615b6d743"
DEFINITION_FIELDS = {
    **{name: spec.FieldKinds for name, spec in KCylAttrDefs.items()},
    "FACE_AUTOMATION_2_2001": (9, 1),
}


def pointer_slots(graph, allocated):
    slots, roles = {}, Counter()
    for row in allocated:
        if row.KindValue != 81:
            continue
        definition = RequireXmt(graph, row.Integer("definition"), 80)
        shape = definition.Indexes("fields")
        positions = tuple(index for index, kind in enumerate(shape) if kind == 9)
        if not positions:
            continue
        name = RequireXmt(graph, definition.Integer("identifier"), 79).String("string")
        require(DEFINITION_FIELDS.get(name) == shape, "unqualified pointer allocation")
        slots[row.IndexValue] = positions
        roles[name] += len(positions)
    return slots, dict(roles)


def compare_count(graph, allocated, expected):
    slots, roles = pointer_slots(graph, allocated)
    count = CountRollNodes(allocated, graph, slots)
    require(
        count == expected, "attribute allocations do not account for the PMARK count"
    )
    return {
        "wire_rows": len(allocated),
        "hidden_pointer_slots": roles,
        "header_count": count,
    }


def measure_saved(raw):
    history = ReadFilletHist(SldprtArchive.from_bytes(raw))
    result = {}
    for name, current, earlier in zip(
        ("fillet", "stock", "activation"),
        history.StagesValue[:-1],
        history.StagesValue[1:],
        strict=True,
    ):
        delta, active, prior = current.UndoValue, current.NodesValue, earlier.NodesValue
        removed = tuple(
            RequireXmt(active, index, kind) for index, kind in delta.RemovedValue
        )
        result[name] = {
            "mark_id": current.MarkValue.Integer("id"),
            "new": compare_count(
                active, removed, current.MarkValue.Integer("n_new_nodes")
            ),
            "deleted": compare_count(
                prior, delta.RestoredValue, current.MarkValue.Integer("n_del_nodes")
            ),
            "processed_copy_count": current.MarkValue.Integer("n_copy_mod_nodes"),
            "physical_copy_rows": len(delta.PreviousValue),
            "copy_staging_capacity": delta.CopyCapacity,
            "different_copy_rows": sum(
                row != active[row.IndexValue] for row in delta.PreviousValue
            ),
        }
    return {"source_sha256": digest(raw), "transitions": result}


def refusal(action):
    try:
        action()
    except ValueError as error:
        return str(error)
    raise ValueError("invalid generated rollback allocation was accepted")


def measure_authored(request):
    x, y, radius, height, label = request
    span = CylSpan(
        (x, y, 0.0), (x, y, height), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), radius
    )
    track = BodyTrackIn(24, 1795654321, label, 1, 101, 19, 27)
    built = MakeCylTrans(span, track)
    require(
        MakeCylTrans(span, track) == built,
        "fresh cylinder partition is nondeterministic",
    )
    active, delta = DecodePartData(built.BytesValue, KPartitionStream)
    graph = ReadActiveNodes(active.data)
    selected, *_ = ReadXmtStages(
        delta.data, graph, (built.ActivationId, built.SelectedId)
    )
    ReadXmtHistory(delta.data, graph)
    undo = selected.UndoValue
    removed = tuple(RequireXmt(graph, index, kind) for index, kind in undo.RemovedValue)
    slots, _ = pointer_slots(graph, removed)
    index = next(iter(slots))
    owner = graph[index]
    absent = tuple(row for row in removed if row is not owner)
    resident = next(
        position for position, target in enumerate(owner.Indexes("fields")) if target
    )
    recipe = next(
        row
        for row in removed
        if row.KindValue == 81
        and graph[graph[row.Integer("definition")].Integer("identifier")].String(
            "string"
        )
        == "BODY_RECIPE_2001"
    )
    require(recipe.Indexes("fields") == (0, 0), "authored recipe changed value framing")
    return {
        "partition_sha256": digest(built.BytesValue),
        "new": compare_count(graph, removed, selected.MarkValue.Integer("n_new_nodes")),
        "deleted": compare_count({}, (), selected.MarkValue.Integer("n_del_nodes")),
        "refusals": {
            "duplicate_physical_allocation": refusal(
                lambda: CountRollNodes((*removed, owner), graph, slots)
            ),
            "detached_physical_allocation": refusal(
                lambda: CountRollNodes((*absent, replace(owner)), graph, slots)
            ),
            "hidden_owner_not_in_transition": refusal(
                lambda: CountRollNodes(absent, graph, slots)
            ),
            "duplicate_hidden_slot": refusal(
                lambda: CountRollNodes(removed, graph, {index: (0, 0)})
            ),
            "resident_value_slot": refusal(
                lambda: CountRollNodes(removed, graph, {index: (resident,)})
            ),
            "null_nonpointer_field": refusal(
                lambda: CountRollNodes(removed, graph, {recipe.IndexValue: (1,)})
            ),
        },
    }


def launch(mode, data):
    result = subprocess.run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
        input=data,
        capture_output=True,
        timeout=90,
    )
    require(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return json.loads(result.stdout)


def run(capture, axial):
    path = ROOT / "re/solidworks/measurements/2026/EdgeFilletRollbackRead01.json"
    baseline = json.loads(checked(path, BASELINE))
    saved = {}
    for row in baseline["results"]:
        name = row["case"]
        stem = name + ("Edited" if row["edited"] else "")
        saved[stem] = launch(
            "saved", checked(capture / name / (stem + ".SLDPRT"), row["source_sha256"])
        )
    saved["GeneratedAxialNativeSave"] = launch("saved", checked(axial, AXIAL))
    authored = [
        launch("authored", json.dumps(values).encode())
        for values in (
            (0.00871, -0.00341, 0.00623, 0.02939, "First radius"),
            (-0.00562, 0.00287, 0.00919, 0.04012, "Second radius with longer label"),
        )
    ]
    require(
        authored[0]["partition_sha256"] != authored[1]["partition_sha256"],
        "authored geometry does not change the partition",
    )
    return {
        "schema": "kit.sw2026.fillet-rollback-node-counts.v1",
        "sdk_base": BASE,
        "oracle_build": BUILD,
        "oracle_executable_sha256": ORACLE,
        "previous_rollback_receipt_sha256": BASELINE,
        "hidden_pointer_kernel_sha256": "2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969",
        "saved": saved,
        "authored": authored,
        "fresh_guarded_workers": len(saved) + len(authored),
        "native_launches": 0,
        "new_heldout_credit": 0,
        "fillet_archives_written": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("authored", "saved"))
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--generated-axial", type=Path)
    args = parser.parse_args()
    if args.worker:
        data = sys.stdin.buffer.read()
        audit = guard_runtime()
        report = (
            measure_saved(data)
            if args.worker == "saved"
            else measure_authored(json.loads(data))
        )
        require(not audit, "fillet count worker used an external input")
        report["guarded_external_access_attempts"] = len(audit)
    else:
        require(
            args.capture is not None and args.generated_axial is not None,
            "supply only the disclosed capture and generated axial save",
        )
        report = run(args.capture, args.generated_axial)
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
