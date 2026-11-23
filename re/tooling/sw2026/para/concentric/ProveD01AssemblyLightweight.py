from argparse import ArgumentParser
from dataclasses import replace
import json
from math import isclose
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01AssemblyMotion import (
    KInfoXml, MEASUREMENTS, MODEL, MODEL_PIN, MODULES, PRIOR, PRIOR_PIN, PROOF, PROOF_PIN, SDK_INFO,
    SDK_INFO_PIN, checked, compose_streams, fingerprint, generate, model_inputs,
    neutral_request, prepare_package, refuse, registry, require, source_cases, stream_diff, wire,
)
from AssemblyLightweight import ENGLISH_HATCH, MEMBER, bounds, build, decode, encode, select_planes, stamp
from CollectDrawingViewSupportEvidence import Image
from ProveD01ParentDisplay import build_arguments

from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmGraphs import MakeAsmGraphs
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.AsmInfoInput import AsmInfoInput
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.MakeAsmInfo import MakeAsmInfo
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


BASE = "3a2e1db923ad404fa51e25ddd8aa3304cf1fb786"
PREVIOUS_CACHE_PROOF = "ConcentricAssemblyCacheOwnership01.json"
PREVIOUS_CACHE_PIN = "8a9289e4d6a8ddae4c55aa4d29df650f2634cec49cf3e126d3e35e51bf457734"
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
MATES = CONFIG + "-MatesList"
UNSET = (0.0, 0.0, 0.0, -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, -2.0)
CONTRAST = 0.01737
HATCH_CONTEXT = {"locale": "en-US", "hatch_name": ENGLISH_HATCH}


def static_owners(directory, previous):
    model = Image(directory / "sldmodu.dll")
    storage = Image(directory / "doccplu.dll")
    require(fingerprint(model.data) == MODULES["sldmodu.dll"]
            and fingerprint(storage.data) == MODULES["doccplu.dll"],
            "licensed lightweight images differ")
    calls = {
        "assembly_update_stamp": (0x4CE69B30, 0x1030, 0x4BDAC640),
        "assembly_model_box": (0x4CE69B30, 0x1350, 0x4B6960C0),
        "assembly_lazy_hatch": (0x4CE69B30, 0x15F0, 0x4B69ED30),
        "assembly_nonpart_predicate": (0x4CE69B30, 0x1A0, 0x4B27CBE0),
        "datum_bounds_accessor": (0x4D16F278, 0x19B0, 0x4C2D4E70),
        "datum_cached_visibility": (0x4D16F278, 0x18D0, 0x4C2CECA0),
        "datum_cached_suppression": (0x4D16F278, 0x1958, 0x4BB4BF50),
        "lightweight_datum_serializer": (0x4D219648, 0x28, 0x4C792010),
        "lightweight_base_serializer": (0x4D0E8698, 0x28, 0x4C791F40),
        "default_border_size": (0x4D138FF0, 0x188, 0x4C2F65A0),
    }
    for table, slot, address in calls.values():
        require(model.unpack("Q", model.offset(table - model.base + slot)) == address,
                "exact lightweight virtual owner differs")
    require(storage.imports[0x180051668]["symbol"].startswith("??0moLWdataHelper_c@@")
            and storage.imports[0x1800517D8]["symbol"].startswith("?Serialize@moLWdataHelper_c@@")
            and model.imports[0x4CD3B538]["symbol"].endswith("@AEAVmgXform_c@@@Z")
            and model.imports[0x4CD385F0]["symbol"].startswith("?getBodies@gcPartition_w@@"),
            "static archive or physical partition owner differs")
    methods = {"model_helper_constructor": 0x4C7902C0, "helper_serialize": 0x4C792350,
               "plane_cache_constructor": 0x4C78FED0, "actual_plane_corners": 0x4C2E57C0,
               "read_plane_border_words": 0x4C2E3570, "read_plane_transform": 0x4C2E8A20}
    rows = {name: model.function(address) for name, address in methods.items()}
    prior = previous["static"]["routine_bounds"]
    require(rows["helper_serialize"] == prior["serialize_lw_helper"]
            and storage.function(0x18002FFC0) == prior["save_lw_data"],
            "native lightweight routine hash differs from the previous cache audit")
    return {"module_sha256": {name: MODULES[name] for name in ("doccplu.dll", "sldmodu.dll")},
            "rea_identity": "ev_9bfcca546a90b1270c75953c6f6818fa1d10981d8b1e90a78e5bcd753506ae9e",
            "functions": rows | {name: model.function(address) for name, (_, _, address) in calls.items()},
            "vtable_cells": {name: list(map(hex, item)) for name, item in calls.items()}}


def model_axes(archive):
    require(not any("Partition" in name for name in archive.streams),
            "lightweight assembly scope requires no locally owned native partitions")
    link = ReadNativeLink(archive, 0)
    require(link.ConfigName == CONFIG, "lightweight member has an unsupported configuration locator")
    headers = (link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require("Header2"), 19000))
    return link, headers


def compare_sources(disclosures, properties, known, cache_ledger):
    results = {}
    for name, path, pin in source_cases(disclosures, properties):
        require(known[name]["source_sha256"] == pin, "disclosed parent identity differs")
        archive = SldprtArchive.from_bytes(checked(path, pin))
        member = archive.require(MEMBER)
        graph, cached_planes = decode(member)
        link, headers = model_axes(archive)
        root = link.ConfigValue.RootValue
        planes = select_planes(link.ResolvedValue.RootsValue)
        require(encode(graph) == member and graph.FieldsValue["f70"] == stamp(headers)
                and [row.FieldsValue["f18"] for row in cached_planes] == [row.FieldsValue["f08"] for row in planes],
                "saved lightweight header or plane order differs from its model")
        if name in ("D01/Source", "D01/Edited"):
            key = "concentric_d01_" + name.partition("/")[2].lower()
            previous = cache_ledger["inputs"][key]["streams"][MEMBER]
            require(previous == {"bytes": len(member), "sha256": fingerprint(member)}, "prior named member differs")
        normalized, varied = None, None
        if name == "A12SyncedEmpty.SLDASM":
            require(root.FieldsValue["f1560"] == 0
                    and tuple(graph.FieldsValue["f08"].values()) == UNSET,
                    "empty assembly lost the native unset bounding-box state")
        else:
            for row in cached_planes:
                row.FieldsValue["fb8"]["words"][19]["w"] = 0
            normalized = build(root, headers, link.ResolvedValue.RootsValue, **HATCH_CONTEXT)
            require(normalized == encode(graph), "a real data field differs from the independent model projection")
            varied = sum(a != b for a, b in zip(member, normalized, strict=True))
        results[name] = {"source_sha256": pin, "lwdata_sha256": fingerprint(member), "member_bytes": len(member),
                         "byte_exact_typed_replay": True, "actual_datum_id_count": len(planes),
                         "stamp": graph.FieldsValue["f70"], "local_partition_present": False,
                         "canonical_projection_sha256": None if normalized is None else fingerprint(normalized),
                         "raw_padding_only_byte_count": varied}
    require(len(results) == 12 and sum(row["canonical_projection_sha256"] is not None for row in results.values()) == 11,
            "scoped source contrast inventory changed")
    return results


def with_lightweight(bundle, recipe, streams):
    require(MEMBER not in streams and not any("Partition" in name for name in streams),
            "lightweight generation needs a fresh slot and no locally owned native partitions")
    state = bundle.StateValue
    headers = bundle.HeaderValue, bundle.TopHeader
    data = build(state.RootValue, headers, state.FeatureValues, fresh=True, **HATCH_CONTEXT)
    generations = MakeAsmGraphs(state, recipe, headers[0], bundle.MateValues)
    require(generations.ConfigBytes == streams[CONFIG] and generations.MatesBytes == streams[MATES],
            "sizing lightweight datum displays changed an unrelated linked archive")
    return BuildSldprt(streams | {MEMBER: data, RESOLVED: generations.ResolvedBytes}, FormatVersion=4)


def inspect_variant(baseline, output, child, dimensions):
    before, after = (SldprtArchive.from_bytes(value) for value in (baseline, output))
    require(stream_diff(before, after) == {MEMBER, RESOLVED},
            "lightweight sizing changed an unrelated stream")
    link, headers = model_axes(after)
    root = link.ConfigValue.RootValue
    member = after.require(MEMBER)
    _, planes = decode(member)
    regenerated = build(root, headers, link.ResolvedValue.RootsValue, **HATCH_CONTEXT)
    mates = ReadMatesMut(after.require(MATES), link.ResolvedValue).RootsValue
    require(member == regenerated and len(mates) == 1 and mates[0].ClassValue.NameValue == "moMateConcentric",
            "fresh linkage disagrees with lightweight owner or loses the actual concentric mate")
    _, low, high = bounds(root)
    observed = tuple(b - a for a, b in zip(low, high, strict=True))
    require(observed == dimensions, "readback assembly extent differs from the generated geometry")
    return {"prior_parent_sha256": fingerprint(baseline), "parent_sha256": fingerprint(output),
            "child_sha256": fingerprint(child), "parent_stream_count": len(after.streams),
            "matched_member_bytes": len(member), "lwdata_sha256": fingerprint(member),
            "resolved_sha256": fingerprint(after.require(RESOLVED)), "extent_m": dimensions,
            "datum_ids": [node.FieldsValue["f18"] for node in planes],
            "changed_members": sorted(stream_diff(before, after))}


def translated(placements, end_indexes, moving, intent, amount):
    original = placements[moving]
    frame = original.FrameValue
    local = intent.LocalAxes[end_indexes.index(moving)]
    offset = tuple(sum(coordinate * basis for coordinate, basis in zip(local, row, strict=True)) * amount
                   for row in zip(frame.AxisU, frame.AxisV, frame.NormalValue, strict=True))
    origin = tuple(a + b for a, b in zip(frame.OriginValue, offset, strict=True))
    updated = replace(original, FrameValue=replace(frame, OriginValue=origin))
    return tuple(updated if index == moving else row for index, row in enumerate(placements))


def measured_extent(state):
    _, low, high = bounds(state.RootValue)
    return tuple(b - a for a, b in zip(low, high, strict=True))


def refusals(bundle, contrast, measured):
    state = bundle.StateValue
    headers = bundle.HeaderValue, bundle.TopHeader
    bad_top = ArchiveNode(headers[1].ClassValue, headers[1].FieldsValue | {"f40": headers[1].FieldsValue["f40"] + 1})
    swapped = tuple(contrast.StateValue.PlaneValues["z"] if p is state.PlaneValues["z"] else p
                    for p in state.FeatureValues)
    payload = SldprtArchive.from_bytes(measured).require(MEMBER)
    graph, _ = decode(payload)
    graph.FieldsValue["f108"] = 1
    return {
        "foreign_plane_owner": refuse(lambda: build(state.RootValue, headers, swapped, fresh=True, **HATCH_CONTEXT),
                                      "actual generated root and its paired self file"),
        "crossed_update_stamp": refuse(lambda: build(state.RootValue, (headers[0], bad_top),
                                                        state.FeatureValues, **HATCH_CONTEXT), "update stamp differs"),
        "nonempty_local_body_store": refuse(lambda: decode(encode(graph)), "exact three-plane empty-auxiliary branch"),
        "unsupported_locale": refuse(lambda: build(state.RootValue, headers, state.FeatureValues,
                                                     locale="de-DE", hatch_name=ENGLISH_HATCH), "selected localized assembly hatch"),
        "already_sized": refuse(lambda: build(state.RootValue, headers, state.FeatureValues,
                                                fresh=True, **HATCH_CONTEXT), "unset generated datum display"),
    }


def worker(payload, pins):
    require(set(payload) == {"model", "contrast_m"} and payload["contrast_m"] == CONTRAST,
            "lightweight worker accepts only the authored model and frozen placement contrast")
    model = payload["model"]
    request, documents, models, properties, _ = prepare_package(model["neutral"])
    reg = registry()
    earlier, child, observed, accesses = generate(model, pins[0])
    require(observed["parent_sha256"] == pins[1], "the previous exact model exchange changed")
    _, bundle = compose_streams(request["models"], request["chronology"], documents, models, reg)
    authored = build_arguments(request["models"]["after"], documents[1], models[1])
    candidate, recipe, placements, end_indexes, tag, intent = authored
    headers = bundle.HeaderValue, bundle.TopHeader
    information = MakeAsmInfo(bundle.StateValue, headers, recipe.OutputValue,
                              AsmInfoInput(properties.created_at, properties.save_actor, -480, "en-US"))
    base_streams = SldprtArchive.from_bytes(earlier).streams | {KInfoXml: information}
    baseline = BuildSldprt(base_streams, FormatVersion=4)
    require(fingerprint(baseline) == pins[2] and fingerprint(child) == pins[3]
            and len(base_streams) == 35, "the prior complete 35-stream D01 graph changed")
    measured = with_lightweight(bundle, recipe, base_streams)
    main = inspect_variant(baseline, measured, child, measured_extent(bundle.StateValue))
    neutral_control = MakeCylAsm(*authored)
    moved = translated(placements, end_indexes, 1 - models[1].FixedIndex, intent, payload["contrast_m"])
    second = MakeCylAsm(candidate, recipe, moved, end_indexes, tag, intent)
    alternate = with_lightweight(second, recipe, dict(second.StreamsValue))
    contrast = inspect_variant(second.BytesValue, alternate, second.ChildValue.BytesValue,
                               measured_extent(second.StateValue))
    control_extent = measured_extent(neutral_control.StateValue)
    require(neutral_control.ChildValue is second.ChildValue is candidate
            and control_extent[:2] == contrast["extent_m"][:2]
            and isclose(control_extent[2] - contrast["extent_m"][2], payload["contrast_m"],
                        rel_tol=0.0, abs_tol=1e-15),
            "the independent axial shift differs from its model-only unshifted control")
    contrast.update(neutral_control_extent_m=control_extent, authored_axial_shift_m=payload["contrast_m"],
                    unchanged_neutral_child=True)
    negatives = refusals(bundle, second, measured)
    require(main["lwdata_sha256"] != contrast["lwdata_sha256"] and main["extent_m"] != contrast["extent_m"]
            and not accesses, "the independent placement contrast failed or read external data")
    return {"baseline_exact": True, "disclosed_model": main, "independent_placement": contrast,
            "refusals": negatives, "runtime_external_accesses": len(accesses)}


def main():
    parser = ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--disclosures", type=Path)
    action.add_argument("--worker", nargs=4)
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin), args.worker)))
        return
    require(args.output is not None and args.native_dir is not None, "supply module directory and fresh receipt path")
    pins = {PRIOR: PRIOR_PIN, PROOF: PROOF_PIN, MODEL: MODEL_PIN, SDK_INFO: SDK_INFO_PIN,
            PREVIOUS_CACHE_PROOF: PREVIOUS_CACHE_PIN}
    receipts = {name: json.loads(checked(MEASUREMENTS / name, pin)) for name, pin in pins.items()}
    history = receipts[PREVIOUS_CACHE_PROOF]
    scope = receipts[SDK_INFO]
    source = compare_sources(args.disclosures, receipts[PROOF], scope["source_controls"], history)
    neutral = neutral_request(args.disclosures, receipts[PROOF])
    model = model_inputs(neutral, receipts[PRIOR])
    request = wire({"model": model, "contrast_m": CONTRAST})
    prior, current = (receipts[name]["generated"] for name in (MODEL, SDK_INFO))
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", prior["prior_parent_sha256"],
               prior["parent_sha256"], current["parent_sha256"], current["child_sha256"])
    a, b = (subprocess.run(command, input=request, capture_output=True, timeout=120) for _ in range(2))
    require(a.returncode == b.returncode == 0 and a.stdout == b.stdout,
            (a.stderr + b.stderr).decode() or "fresh lightweight workers differ")
    files = (HERE, HERE.with_name("AssemblyLightweight.py"))
    proof = {"schema": "kit.sw2026.d01-assembly-lightweight.v1", "base": BASE, "prior_receipts": pins,
             "source_controls": source, "static": static_owners(args.native_dir, history),
             "generated": json.loads(a.stdout), "request_sha256": fingerprint(request), "guarded_workers": 2,
             "native_processes_started": 0, "heldout_inputs_read": 0,
             "source_sha256": {str(path.relative_to(HERE.parents[5])): fingerprint(path.read_bytes()) for path in files}}
    with args.output.open("xb") as output:
        output.write(wire(proof))


if __name__ == "__main__":
    main()
