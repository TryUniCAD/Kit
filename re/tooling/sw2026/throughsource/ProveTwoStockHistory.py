from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
BASE = "9b323b383bcfaf69baad61d4ea70c1537e898a41"
SELECTED = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
UNRESTRICTED = "f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22"
KERNEL = "2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969"
STREAM = "Contents/Config-0-Partition"
REFUSALS = {
    "cross-selector": "history mark differs from actual chronological owner",
    "short-mark-count": "mark header counts disagree with physical rollback lists",
    "short-capacity": "rollback copy capacity or retained WORLD differs",
    "cross-deletion": "rollback slots overlap or differ from their actual current class",
    "cross-world": "kernel owner chain is not reciprocal",
    "cross-atom": "saved kernel body tag or producer differs from its surviving atom",
    "cross-qualifier": "inconsistent source-index selector for a rollback target",
    "cross-geometry": "rollback stock geometry does not follow its linked profile and D1",
}
MODES = ("selected", "unrestricted", *REFUSALS)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def substitute_row(frame, index, action):
    match = 0

    def modify(rows):
        nonlocal match
        result = []
        for row in rows:
            if row.node.IndexValue == index:
                row = action(row)
                match += 1
            result.append(row)
        return tuple(result)

    result = replace(
        frame, restored=modify(frame.restored), changed=modify(frame.changed)
    )
    require(
        match == 1, "negative alteration does not designate one actual physical row"
    )
    return result


def change_field(row, field, value):
    refs = tuple(
        replace(ref, index=value) if ref.field == field else ref for ref in row.refs
    )
    node = replace(row.node, FieldsValue={**row.node.FieldsValue, field: value})
    return replace(row, node=node, refs=refs)


def altered(root, frames, ordered, states, mode):
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
        ReadBodyAttrs,
    )

    cut, moving = ordered[:2]
    old_state = states[1]
    first_body, second_body = old_state.bodies
    result = dict(frames)
    target = cut
    if mode == "cross-selector":
        root = replace(
            root,
            FieldsValue={**root.FieldsValue, "current_pmark": moving.mark.IndexValue},
        )
    elif mode == "short-mark-count":
        mark = replace(
            cut.mark,
            FieldsValue={**cut.mark.FieldsValue, "n_new_nodes": len(cut.removed) - 1},
        )
        target = replace(cut, mark=mark)
    elif mode == "short-capacity":
        target = replace(cut, copy_capacity=len(cut.changed) - 1)
    elif mode == "cross-deletion":
        removed = tuple(
            (second_body.slot, kind) if index == first_body.slot else (index, kind)
            for index, kind in moving.removed
        )
        target = replace(moving, removed=removed)
    elif mode == "cross-world":
        target = substitute_row(
            cut,
            old_state.world.IndexValue,
            lambda row: change_field(row, "body", second_body.slot),
        )
    elif mode == "cross-atom":
        attributes = ReadBodyAttrs(old_state.nodes, old_state.nodes[second_body.slot])
        index = attributes["ATOM_ID_2001"].Indexes("fields")[1]
        result_atom = states[0].bodies[1].atom
        target = substitute_row(
            cut, index, lambda row: change_field(row, "values", (result_atom,))
        )
    elif mode == "cross-qualifier":
        uses = Counter(
            ref.index
            for row in (*cut.restored, *cut.changed)
            for ref in row.refs
            if ref.index
        )
        row = next(
            row for row in cut.changed if any(uses[ref.index] > 1 for ref in row.refs)
        )
        offset = next(
            offset for offset, ref in enumerate(row.refs) if uses[ref.index] > 1
        )
        before = row.refs[offset]
        after = replace(before, at_or_below_limit=not before.at_or_below_limit)
        target = substitute_row(
            cut,
            row.node.IndexValue,
            lambda value: replace(
                value, refs=(*value.refs[:offset], after, *value.refs[offset + 1 :])
            ),
        )
    elif mode == "cross-geometry":
        row = next(
            row
            for row in cut.changed
            if row.node.KindValue == 18
            and row.node.Integer("owner") == second_body.slot
        )
        ref = next(ref for ref in row.refs if ref.field == "point")
        flags = {
            value.index: value.at_or_below_limit
            for member in (*cut.restored, *cut.changed)
            for value in member.refs
        }
        other = next(
            index
            for node in old_state.nodes.values()
            if node.KindValue == 18 and node.Integer("owner") == second_body.slot
            for index in (node.Integer("point"),)
            if index != ref.index
            and flags.get(index, ref.at_or_below_limit) == ref.at_or_below_limit
        )
        target = substitute_row(
            cut, row.node.IndexValue, lambda value: change_field(value, "point", other)
        )
    result[target.mark.IndexValue] = target
    return root, result


def describe(root, states, ordered, marks, scope, active_payload, delta_payload):
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
        ReadBodyAttrs,
    )

    stages = []
    for state, frame in zip(states, ordered, strict=True):
        mark = frame.mark
        refs = [ref for row in (*frame.restored, *frame.changed) for ref in row.refs]
        stages.append(
            {
                "mark_id": state.mark_id,
                "wire_index": mark.IndexValue,
                "delta_key": mark.Integer("delta_key"),
                "decompressed_delta_offset": frame.offset,
                "world_head": state.world.Integer("body"),
                "node_count": len(state.nodes),
                "world_alive": bool(state.world.Integer("alive")),
                "header_mark_counts": [
                    mark.Integer(field)
                    for field in ("n_new_nodes", "n_del_nodes", "n_copy_mod_nodes")
                ],
                "restored_removed_changed": [
                    len(frame.restored),
                    len(frame.removed),
                    len(frame.changed),
                ],
                "copy_staging_count": frame.copy_capacity,
                "null_true_nonnull_true_nonnull_false": [
                    sum(not ref.index and ref.at_or_below_limit for ref in refs),
                    sum(bool(ref.index) and ref.at_or_below_limit for ref in refs),
                    sum(bool(ref.index) and not ref.at_or_below_limit for ref in refs),
                ],
                "removed_body_slots": [
                    index for index, kind in frame.removed if kind == 12
                ],
                "changed_body_slots": [
                    row.node.IndexValue
                    for row in frame.changed
                    if row.node.KindValue == 12
                ],
                "bodies": [
                    {
                        "wire_slot": body.slot,
                        "atom": body.atom,
                        "producer": body.feature,
                        "label": body.label,
                        "tag": body.tag,
                        "faces": len(body.faces),
                        "vertices": len(body.points),
                    }
                    for body in state.bodies
                ],
            }
        )
    cut_refs = [
        ref
        for row in (*ordered[0].restored, *ordered[0].changed)
        for ref in row.refs
        if ref.index
    ]
    high_true = max(ref.index for ref in cut_refs if ref.at_or_below_limit)
    low_false = min(ref.index for ref in cut_refs if not ref.at_or_below_limit)
    require(
        high_true > low_false, "a wire-index threshold unexpectedly explains qualifiers"
    )
    require(
        [stage["mark_id"] for stage in stages] == [21, 18, 16, 3, 1]
        and [stage["node_count"] for stage in stages] == [376, 311, 169, 27, 27]
        and stages[0]["restored_removed_changed"] == [19, 84, 73]
        and stages[0]["copy_staging_count"] == 76,
        "the actual two stock history differs",
    )
    old_state = states[1]
    consumed = old_state.bodies[1]
    attributes = ReadBodyAttrs(old_state.nodes, old_state.nodes[consumed.slot])
    first_restore = ordered[0].restored[0].node
    require(
        first_restore.KindValue == 98
        and attributes["SWIMPLICITBODYNAME_ID_U"].Indexes("fields")
        == (first_restore.IndexValue, 0),
        "the first restored name does not belong to the consumed physical body",
    )
    return {
        "scope_code": scope,
        "partition_wire_index": root.IndexValue,
        "native_mark_owners_map_index_and_id": [
            [mark.IndexValue, mark.FieldsValue["f18"]] for mark in marks
        ],
        "phase_frames": stages,
        "cut_refutes_wire_index_threshold": {
            "highest_true_slot": high_true,
            "lowest_false_slot": low_false,
        },
        "first_restored_owner": {
            "kernel_kind": first_restore.KindValue,
            "wire_slot": first_restore.IndexValue,
            "attribute": "SWIMPLICITBODYNAME_ID_U",
            "body_slot": consumed.slot,
            "atom": consumed.atom,
            "label": consumed.label,
        },
        "active_payload_bytes": len(active_payload),
        "delta_payload_bytes": len(delta_payload),
        "active_payload_sha256": sha256(active_payload).hexdigest(),
        "delta_payload_sha256": sha256(delta_payload).hexdigest(),
        "analytic_profiles_and_circle_match": True,
    }


def worker(mode):
    sys.path.insert(0, str(REPO / "src"))
    sys.path.insert(0, str(HERE.parent))
    from convert.Geometry.Parasolid import DecodePartData
    from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import (
        ReadXmtHistory,
    )
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import (
        ReadStockData,
    )
    from ReadTwoStockHistory import decode_history, verify_history

    for name in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        codecs.lookup(name)
    for name in (
        "interchange.brep.Curves.BrepCurves",
        "interchange.brep.Validation.BrepValidate",
    ):
        import_module(name)
    attempts = []

    def protect(event, _):
        if event in {
            "open",
            "os.listdir",
            "os.scandir",
            "os.system",
            "os.exec",
            "os.fork",
            "os.posix_spawn",
            "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError("two stock rollback tried external access: " + event)

    sys.addaudithook(protect)
    raw = sys.stdin.buffer.read()
    require(
        sha256(raw).hexdigest()
        == (UNRESTRICTED if mode == "unrestricted" else SELECTED),
        "worker received a different disclosed source",
    )
    archive = SldprtArchive.from_bytes(raw)
    active, _ = ReadStockData(archive, STREAM)
    active_payload, delta_payload = DecodePartData(archive.require(STREAM), STREAM)
    root, frames = decode_history(delta_payload.data)
    states, ordered, marks, scope = verify_history(archive, active, root, frames)
    if mode in REFUSALS:
        root, frames = altered(root, frames, ordered, states, mode)
        try:
            verify_history(archive, active, root, frames)
        except ValueError as error:
            require(str(error) == REFUSALS[mode], f"unexpected {mode} refusal: {error}")
            result = {"refusal": str(error)}
        else:
            raise ValueError(f"altered rollback condition qualified: {mode}")
    else:
        require(
            scope == int(mode == "selected"),
            "semantic scope was inferred from kernel identity",
        )
        result = describe(
            root, states, ordered, marks, scope, active_payload.data, delta_payload.data
        )
        try:
            ReadXmtHistory(delta_payload.data, active)
        except ValueError as error:
            require(
                str(error) == "current kernel framing differs",
                "original narrow reader changed its refusal",
            )
            result["legacy_single_body_refusal"] = str(error)
        else:
            raise ValueError(
                "the ordinary reader unexpectedly widened its rollback scope"
            )
    require(not attempts, "worker accessed an external dependency")
    return {**result, "external_access_attempts": len(attempts)}


def prove(selected, unrestricted):
    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    tool_hashes = {name: sha256((HERE.parent / name).read_bytes()).hexdigest() for name in ("ReadTwoStockHistory.py", "ProveTwoStockHistory.py")}
    sources = {}
    for path, lane, digest in (
        (selected, "ThroughMultiStock03", SELECTED),
        (unrestricted, "ThroughAllBodies02", UNRESTRICTED),
    ):
        source = path.resolve(strict=True)
        require(
            source.parts[-3:] == (lane, "DisclosedNative", "ThroughMultiStock.SLDPRT")
            and not path.is_symlink(),
            "pass only the exact disclosed saved pair",
        )
        raw = source.read_bytes()
        require(sha256(raw).hexdigest() == digest, "disclosed source hash differs")
        sources[digest] = (source, raw)
    evidence = {}
    for mode in MODES:
        digest = UNRESTRICTED if mode == "unrestricted" else SELECTED
        process = run(
            (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
            input=sources[digest][1],
            capture_output=True,
        )
        require(process.returncode == 0, process.stderr.decode())
        evidence[mode] = json.loads(process.stdout)
    require(
        evidence["selected"]["phase_frames"]
        == evidence["unrestricted"]["phase_frames"],
        "selected and unrestricted saves have different body histories",
    )
    require(
        evidence["selected"]["delta_payload_sha256"]
        != evidence["unrestricted"]["delta_payload_sha256"],
        "distinct saves unexpectedly collapse to one payload digest",
    )
    require(
        all(
            sha256(path.read_bytes()).hexdigest() == digest
            for digest, (path, _) in sources.items()
        ),
        "disclosed source changed",
    )
    require(
        check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip() == head
        and all(sha256((HERE.parent / name).read_bytes()).hexdigest() == digest for name, digest in tool_hashes.items()),
        "the rollback implementation changed during verification",
    )
    return {
        "schema": "kit.sw2026.two-stock-physical-rollback.v1",
        "baseline": BASE,
        "implementation_head": head,
        "selected_sha256": SELECTED,
        "unrestricted_sha256": UNRESTRICTED,
        "static_kernel_sha256": KERNEL,
        "tools_sha256": tool_hashes,
        "worker_count": len(evidence),
        "external_access_attempts": sum(
            value["external_access_attempts"] for value in evidence.values()
        ),
        "native_processes_run": 0,
        "generated_files": 0,
        "heldout_sources": 0,
        "writer_qualified": False,
        "evidence": evidence,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--selected", type=Path)
    parser.add_argument("--unrestricted", type=Path)
    parser.add_argument("--worker", choices=MODES)
    args = parser.parse_args()
    if args.worker:
        result = worker(args.worker)
    else:
        require(
            args.selected is not None and args.unrestricted is not None,
            "pass both pinned disclosed saves",
        )
        result = prove(args.selected, args.unrestricted)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
