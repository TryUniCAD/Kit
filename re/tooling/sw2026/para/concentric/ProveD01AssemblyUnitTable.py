from argparse import ArgumentParser
import codecs
from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01AssemblyChronology import (
    REPO, checked, compose_streams, disclose, fingerprint, mate_readback, observe,
    proof_guard, registry, require, stream_diff, verify_owned_edit, wire,
)
from ProveD01AssemblyProperties import bound_properties, disclose_properties
from D01AssemblyPropertyIntent import AssemblyPropertyIntent, add_property_streams
from D01AssemblyStampStreams import add_stamp_streams
from ProveConcentricCmgrHistory import disclosed_cases, refuse
from ProveD01ParentDisplay import build_arguments
from AssemblyUnitTable import UNIT_STREAM, add_unit_stream, verify_unit_table
from ObserveAssemblyUnitOwners import (
    CODE_KEYS, XML_CODES, assembly_controls, custom_preferences, format_differences, inspect_assembly, unit_codes,
)

from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Units.MakeDualLength import MakeDualLength
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "9dca0bd65a4762962b0d71b896cdd354eb405a98"
PRIOR = "ConcentricD01StampStreams01.json"
PRIOR_SHA = "d2f56661b35d6c019c3ed9b0aca9c9d241f4ba1b2631fb91eb3a9cfa5f080469"


def disclosed_assemblies(disclosures, manifest):
    folder = disclosures / "ConcentricMateSourcePacket02/Disclosed"
    results = {}
    for case in disclosed_cases():
        slot = case["id"]
        results[slot] = {}
        for phase in ("Source", "Edited"):
            source = manifest[slot][phase]["parent_sha256"]
            path = folder / slot / "Native" / phase / (case["name"] + ".SLDASM")
            archive = SldprtArchive.from_bytes(checked(path, source))
            root = ReadNativeLink(archive, 0).ConfigValue.RootValue
            results[slot][phase] = {"source_sha256": source, **inspect_assembly(archive),
                                    "differences_from_same_precision_minimal": format_differences(root)}
    return results


def table_result(units, counter, payload):
    return {"sha256": fingerprint(payload), "bytes": len(payload), "terminal_map": counter,
            "codes": unit_codes(units), "length_precision": units["length"].FieldsValue["f0c"],
            "has_dual": units["length"].FieldsValue["fb8"] is not None}


def authored_controls(recipe):
    results = {}
    for unit_input in (UnitInput("in", "degree", "ips", 3), UnitInput("m", "radian", "mks", 7)):
        state = MakeAsmBase(replace(recipe, DocumentUnits=unit_input))
        payload = add_unit_stream({}, state)[UNIT_STREAM]
        units, counter = verify_unit_table(state.RootValue, payload)
        result = table_result(units, counter, payload)
        require(result["length_precision"] == unit_input.DecimalPlaces, "unit table lost its authored display precision")
        units["length"].FieldsValue["fb8"] = MakeDualLength(unit_input.LengthUnit)
        alias = add_unit_stream({}, state)[UNIT_STREAM]
        expanded_units, expanded_counter = verify_unit_table(state.RootValue, alias)
        expanded = table_result(expanded_units, expanded_counter, alias)
        require(expanded["has_dual"] and expanded_counter == counter + 1 and len(alias) == len(payload) + 66
                and expanded["codes"] == result["codes"],
                "fresh dual formatter changed the primary role or did not allocate exactly one object")
        results[unit_input.UnitSystem] = {"primary_only": result, "with_dual": expanded,
                                        "dual_length_code": expanded_units["length"].FieldsValue["fb8"].FieldsValue["fb0"]}
    require(len({row["primary_only"]["sha256"] for row in results.values()}) == 2
            and len({row["primary_only"]["codes"] for row in results.values()}) == 2,
            "independent authored assembly unit sets do not distinguish their physical tables")
    return results


def refusal_cases(streams, state, recipe, payload):
    alien = MakeAsmBase(replace(recipe, DocumentUnits=UnitInput("in", "degree", "ips", 3)))
    custom = MakeAsmBase(replace(recipe, DocumentUnits=UnitInput("mm", "degree", "custom", 2, "kg")))
    root = state.RootValue
    wrong_analysis = ArchiveNode(root.ClassValue, root.FieldsValue | {"f9c0": root.FieldsValue["f9b8"]})
    return {
        "mirror_from_other_assembly": refuse(lambda: verify_unit_table(alien.RootValue, payload),
                                             "differ from their embedded"),
        "trailing_data": refuse(lambda: verify_unit_table(root, payload + b"\x00"), "trailing data"),
        "duplicate_stream": refuse(lambda: add_unit_stream(streams, state), "already have an emitted scope"),
        "analysis_alias": refuse(lambda: verify_unit_table(wrong_analysis, payload), "absent analysis table"),
        "unsupported_density_graph": refuse(lambda: add_unit_stream({}, custom), "unsupported density override"),
    }


def worker(request, baseline_digest):
    require(set(request) == {"models", "chronology", "properties"}, "unit mirror needs only the prior owned model")
    model = request["models"]
    docs = tuple(FromData(model[key]["document"]) for key in ("before", "after"))
    for document in docs:
        document.assert_valid()
    prop = AssemblyPropertyIntent(**request["properties"])
    reg = registry()
    codecs.lookup("utf-8-sig")
    audit = proof_guard()
    models = verify_owned_edit(*docs)
    base, bundle = compose_streams(model, request["chronology"], docs, models, reg)
    state = bundle.StateValue
    headers = (bundle.HeaderValue, bundle.TopHeader)
    properties = add_property_streams(base, state.CurrentConfig, headers, prop)
    with_stamps = add_stamp_streams(properties, state, headers)
    baseline = BuildSldprt(with_stamps, FormatVersion=4)
    require(fingerprint(baseline) == baseline_digest, "the previous complete bookkeeping parent changed")
    streams = add_unit_stream(with_stamps, state)
    parent = BuildSldprt(streams, FormatVersion=4)
    archive = SldprtArchive.from_bytes(parent)
    before = SldprtArchive.from_bytes(baseline)
    require(stream_diff(before, archive) == {UNIT_STREAM} and bound_properties(archive)[0] == prop,
            "unit publication changed previously verified owners")
    payload = archive.require(UNIT_STREAM)
    root = ReadNativeLink(archive, 0).ConfigValue.RootValue
    units, counter = verify_unit_table(root, payload)
    life = observe(parent, bundle, request["chronology"]["after"], model["before"]["root_model_name"], reg)
    mate = mate_readback(parent, bundle, models[1], model["after"])
    recipe = build_arguments(model["after"], docs[1], models[1])[1]
    authored = authored_controls(recipe)
    refusals = refusal_cases(streams, state, recipe, payload)
    require(not audit, "user table construction accessed an external file, process or network")
    return {
        "baseline_parent_sha256": fingerprint(baseline), "parent_sha256": fingerprint(parent),
        "parent_bytes": len(parent), "child_sha256": life["child_sha256"], "actual_mate": mate,
        "generated_units": table_result(units, counter, payload),
        "authored_unit_contrasts": authored, "refusals": refusals,
        "ordinary_streams_unchanged": len(before.streams), "parent_streams": sorted(archive.streams),
        "runtime_external_accesses": len(audit),
    }


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker")
    mode.add_argument("--disclosures", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin), args.worker)))
        return
    prior = json.loads(checked(REPO / "re/solidworks/measurements/2026" / PRIOR, PRIOR_SHA))
    sources = disclosed_assemblies(args.disclosures, prior["disclosed_sources"])
    controls = assembly_controls()
    preferences = custom_preferences(args.disclosures)
    owned = disclose_properties(args.disclosures)["D01"]["Edited"]
    request, original, _ = disclose(args.disclosures, registry())
    require(original["after"]["file_sha256"] == owned["parent_sha256"],
            "unit and property owners did not come from the same original source")
    request["properties"] = asdict(AssemblyPropertyIntent(
        owned["configuration"], owned["created_at"], "Kit disclosed reconstruction"))
    neutral = wire(request)
    require(fingerprint(neutral) == prior["neutral_request_sha256"], "unit mirror changed the prior neutral input")
    expected = prior["generated"]
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", expected["parent_sha256"])
    first, second = (subprocess.run(command, input=neutral, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent guarded table builds disagree")
    generated = json.loads(first.stdout)
    require(generated["child_sha256"] == expected["child_sha256"] and generated["actual_mate"] == expected["actual_mate"],
            "the earlier generated child or signed mate changed")
    generated["unrepresented_source_streams"] = sorted(
        set(original["after"]["original_streams"]) - set(generated["parent_streams"]))
    result = {
        "schema": "kit.sw2026.disclosed-d01-assembly-user-units.v1", "base": BASE, "prior_receipt_sha256": PRIOR_SHA,
        "neutral_request_sha256": fingerprint(neutral), "native_probes": 0, "heldout_accesses": 0,
        "guarded_generated_workers": 2, "whole_source_admitted": False, "public_publication": False,
        "source_original_refusal": original["after"]["strict_source_refusal"],
        "code_axes": {"archive": CODE_KEYS, "system_xml": XML_CODES},
        "disclosed_assembly_sources": sources, "independent_assembly_controls": controls,
        "disclosed_unit_preference_controls": preferences, "generated": generated,
        "source_sha256": {str(path.relative_to(REPO)): fingerprint(path.read_bytes()) for path in
                          (HERE, HERE.with_name("AssemblyUnitTable.py"), HERE.with_name("ObserveAssemblyUnitOwners.py"))},
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
