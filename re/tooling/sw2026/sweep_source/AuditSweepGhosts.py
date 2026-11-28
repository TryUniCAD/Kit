from argparse import ArgumentParser
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from AuditSweepArchive import (
    CODEC_BASELINE, SDK_TREE, SOURCE_LOCK, SldprtArchive, ReadNativeLink,
    check_sdk, digest, guard_runtime, load_disclosed, observe,
)
from convert.Geometry.Parasolid import KTerminalFinSchema, ParaHeaderData
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from para.Partition import decode_active
from SweepArchiveOwners import SWEEP, ReadParents, read_owners
from SweepGhostGraph import component_roles, manager_rows, observe_path, read_ghost
from SweepModel import require
from SweepPathWire import make_path_wire
from SweepReplay import sweep_replay


def inspect(slot, role, source, phases):
    archive = SldprtArchive.from_bytes(source)
    with observe("linked"):
        link = ReadNativeLink(archive, 0)
    cfg, resolved = link.ConfigValue, link.ResolvedValue
    require(cfg.ReportValue["completed"] and resolved.ReportValue["completed"], "incomplete sweep input")
    semantic = read_owners(link, phases)
    sweep, = (node for node in resolved.RootsValue if node.ClassValue.NameValue == SWEEP)
    bindings = component_roles(link, sweep, *ReadParents(sweep))
    manager = manager_rows(cfg.RootValue, sweep, bindings)
    partition = read_ghost(archive, bindings, semantic)
    cfg_bytes, cfg_again = WriteConfigMut(cfg.RootValue, 19000, cfg.HeaderValue)
    with sweep_replay():
        resolved_bytes, again = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000,
                                             cfg_again.MapValue, resolved.ContextValue)
    require(cfg_bytes == archive.require(link.ConfigName) and cfg_again.MapValue == cfg.MapValue
            and resolved_bytes == archive.require(link.StreamName) and again.MapValue == resolved.MapValue,
            "complete linked sweep bytes or map changed during typed replay")
    return {"slot": slot + 1, "role": role, "source_sha256": digest(source), "native_phase": phases["proof"],
            "references": bindings, "manager": manager, "ghost_partition": partition,
            "exact_streams": {link.ConfigName: digest(cfg_bytes), link.StreamName: digest(resolved_bytes)},
            "exact_maps": {link.ConfigName: cfg.MapValue.CounterValue, link.StreamName: resolved.MapValue.CounterValue}}


def wire(radius):
    raw = make_path_wire(radius)
    header = ParaHeaderData(raw)
    require(header.schema == KTerminalFinSchema, "standalone path schema changed")
    rows = decode_active(raw[header.body_offset:])
    nodes = {row.index: XmtNode(row.index, row.kind, row.fields) for row in rows}
    require(len(nodes) == len(rows) == 11 and list(nodes) == list(range(1, 12))
            and all(node.Integer("attributes_features") == 0 for node in nodes.values())
            and nodes[1].Integer("owner") == nodes[1].Integer("next") == 0 and nodes[1].Integer("body_type") == 2,
            "model wire invented external or ghost ownership")
    model = {"driver": {"metres": radius}, "arc": {"start_m": (0.0, 0.0, 0.0),
             "center_m": (0.0, radius, 0.0), "end_m": (radius, radius, 0.0)}}
    shape = observe_path(nodes, nodes[1], model)
    require(make_path_wire(radius) == raw, "fresh analytic path wire is nondeterministic")
    return {"metres": radius, "transmit_sha256": digest(raw), "transmit_bytes": len(raw),
            "resident_nodes": len(nodes), "geometry": shape}


def refuse_inputs():
    refused = []
    for value in (-0.01, 0.0, 0.0003, 0.2, float("nan"), True):
        try:
            make_path_wire(value)
        except ValueError as error:
            refused.append(str(error))
        else:
            raise ValueError("invalid neutral path radius generated a wire")
    return refused


def main():
    parser = ArgumentParser(description="Observe linked sweep ghost ownership or emit independent neutral path transport")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--disclosed", type=Path)
    modes.add_argument("--wire-only", action="store_true")
    modes.add_argument("--raw-wire-radius-m", type=float)
    args = parser.parse_args()
    check_sdk()
    tools = {name: digest((HERE / name).read_bytes()) for name in (
        "AuditSweepGhosts.py", "SweepGhostGraph.py", "SweepPathWire.py", "SweepReplay.py",
        "AuditSweepArchive.py", "SweepArchiveLayout.py", "SweepArchiveOwners.py", "SweepSectionTransport.py",
    )}
    if args.disclosed:
        cases, lock, _ = load_disclosed(args.disclosed)
    blocked = guard_runtime()
    if args.raw_wire_radius_m is not None:
        raw = make_path_wire(args.raw_wire_radius_m)
        require(not blocked, "fresh analytic path input read")
        sys.stdout.buffer.write(raw)
        return
    result = {"schema": "kit.sw2026.ordinary-sweep-ghost-ownership.v1", "codec_baseline": CODEC_BASELINE,
              "sdk_tree": SDK_TREE, "tool_sha256": tools, "native_processes_started": 0,
              "private_sources_accessed": 0, "whole_sweep_candidates": 0}
    if args.disclosed:
        result.update(disclosed_source_lock_sha256=SOURCE_LOCK, disclosed_controls=lock["controls"],
                      cases=[inspect(*case) for case in cases])
    else:
        contrast = [wire(radius) for radius in (0.023201, 0.054087)]
        require(len({row["transmit_sha256"] for row in contrast}) == len(contrast), "neutral path lengths did not change output")
        result.update(model_only_wires=contrast, input_refusals=refuse_inputs())
    require(not blocked, "sweep ghost proof attempted external access after custody")
    result["blocked_runtime_calls"] = len(blocked)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
