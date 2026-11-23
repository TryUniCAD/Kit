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
    REPO, archive_roles, checked, compose_streams, disclose, fingerprint, mate_readback, observe,
    proof_guard, registry, require, stream_diff, verify_owned_edit, wire,
)
from D01AssemblyPropertyIntent import AssemblyPropertyIntent, add_property_streams
from D01AssemblyStampStreams import STAMP_KEYS, add_stamp_streams, header_stamps, read_streams
from D01RevisionIntent import MODEL
from ProveD01AssemblyProperties import bound_properties, disclose_properties
from ProveConcentricCmgrHistory import CORPUS, disclosed_cases, refuse
from ReadConcentricCmgrInputs import config_owner

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Bookkeeping import EncodePartMeta, KConfigObjects, KDisplayUpdate, PartStamps
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from interchange.serialization.Deserialize import FromData


BASE = "5ccf707ad3e82eb409d33833ba013e79b93ca84a"
INTEGRATION = "9eb5a40b67406ea9b5a306e3cc5074d013096e66"
PRIOR = "ConcentricD01PropertyOwners01.json"
PRIOR_SHA = "39b0003fb2cf250afb85bc6efa26ec80e38bd92e47cfd49f909a789db13cf6d7"


def inspect(archive):
    headers, nodes = archive_roles(archive)
    config = config_owner(archive, "moConfiguration_c")
    root = nodes[MODEL]
    scope = {key: archive.require(key) for key in sorted(STAMP_KEYS)}
    stamps = read_streams(scope)
    require(stamps == header_stamps(root, config, headers) and EncodePartMeta(19000, stamps) == scope,
            "assembly stamp streams do not reconstruct from their actual paired headers")
    return {"stamps": asdict(stamps), "own_geometry_stamp": root.FieldsValue["f1300"],
            "streams": {key: {"bytes": len(data), "sha256": fingerprint(data)} for key, data in scope.items()}}


def disclosed_stamps(disclosures, known):
    base = disclosures / "ConcentricMateSourcePacket02/Disclosed"
    results = {}
    for case in disclosed_cases():
        slot = case["id"]
        results[slot] = {}
        for phase in ("Source", "Edited"):
            pins = known[slot][phase]
            path = base / slot / "Native" / phase / (case["name"] + ".SLDASM")
            archive = SldprtArchive.from_bytes(checked(path, pins["parent_sha256"]))
            results[slot][phase] = {"parent_sha256": pins["parent_sha256"], **inspect(archive)}
    stable = tuple(rows["Source"] for rows in results.values())
    require(len({row["own_geometry_stamp"] for row in stable}) == 1
            and len({row["stamps"]["update"] for row in stable}) > 1,
            "disclosed control no longer distinguishes header update from geometry allocation")
    return results


def altered_node(node, **overrides):
    return ArchiveNode(node.ClassValue, node.FieldsValue | overrides)


def refusal_cases(streams, state, headers, stamps):
    h1, h2 = headers
    other_time = replace(stamps, update=stamps.update + 1)
    stale_display = streams | {KDisplayUpdate: EncodePartMeta(19000, other_time)[KDisplayUpdate]}
    config = streams | {KConfigObjects: streams[KConfigObjects] + b"\x00"}
    detached = replace(state, CurrentConfig=altered_node(state.CurrentConfig))
    return {
        "missing_root_log": refuse(lambda: add_stamp_streams({}, state, (altered_node(h1, f20=None), h2)),
                                   "lacks an owned revision log"),
        "divergent_header_update": refuse(
            lambda: add_stamp_streams({}, state, (h1, altered_node(h2, f40=other_time.update))),
            "body ownership disagrees"),
        "stale_display_update": refuse(lambda: read_streams(stale_display), "disagrees with the model update counter"),
        "trailing_config_data": refuse(lambda: read_streams(config), "unqualified name or trailing data"),
        "missing_mirror": refuse(lambda: read_streams({key: data for key, data in streams.items() if key != KDisplayUpdate}),
                                 "scope is incomplete"),
        "detached_active_configuration": refuse(lambda: add_stamp_streams({}, detached, headers),
                                               "actual one selected assembly configuration"),
        "duplicate_output_scope": refuse(lambda: add_stamp_streams(streams, state, headers), "already emitted stream"),
    }


def worker(request, expected_digest):
    require(set(request) == {"models", "chronology", "properties"}, "bookkeeping worker needs only the prior owned model")
    model = request["models"]
    docs = tuple(FromData(model[key]["document"]) for key in ("before", "after"))
    for doc in docs:
        doc.assert_valid()
    property_inputs = AssemblyPropertyIntent(**request["properties"])
    reg = registry()
    codecs.lookup("utf-8-sig")
    audit = proof_guard()
    models = verify_owned_edit(*docs)
    base, bundle = compose_streams(model, request["chronology"], docs, models, reg)
    state = bundle.StateValue
    headers = (bundle.HeaderValue, bundle.TopHeader)
    with_properties = add_property_streams(base, state.CurrentConfig, headers, property_inputs)
    prior = BuildSldprt(with_properties, FormatVersion=4)
    require(fingerprint(prior) == expected_digest, "the previous full property baseline changed")
    streams = add_stamp_streams(with_properties, state, headers)
    parent = BuildSldprt(streams, FormatVersion=4)
    archive = SldprtArchive.from_bytes(parent)
    before = SldprtArchive.from_bytes(prior)
    report = inspect(archive)
    read, property_report = bound_properties(archive)
    require(read == property_inputs and stream_diff(before, archive) == STAMP_KEYS,
            "bookkeeping changes affected existing geometry, chronology or property scope")
    life = observe(parent, bundle, request["chronology"]["after"], model["before"]["root_model_name"], reg)
    mate = mate_readback(parent, bundle, models[1], model["after"])
    refusals = refusal_cases(streams, state, headers, PartStamps(**report["stamps"]))
    require(not audit, "assembly bookkeeping attempted external access")
    return {
        "baseline_parent_sha256": fingerprint(prior), "parent_sha256": fingerprint(parent), "parent_bytes": len(parent),
        "child_sha256": life["child_sha256"], "actual_mate": mate, "properties": property_report,
        "ordinary_streams_unchanged": len(before.streams), "new_streams": report,
        "parent_streams": sorted(archive.streams), "runtime_external_accesses": len(audit), "refusals": refusals,
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
    prior_bytes = checked(REPO / "re/solidworks/measurements/2026" / PRIOR, PRIOR_SHA)
    prior = json.loads(prior_bytes)
    sources = disclose_properties(args.disclosures)
    stamp_receipts = disclosed_stamps(args.disclosures, sources)
    request, original, _ = disclose(args.disclosures, registry())
    source_properties = sources["D01"]["Edited"]
    require(original["after"]["file_sha256"] == source_properties["parent_sha256"],
            "bookkeeping and owned properties use different source custody")
    request["properties"] = asdict(AssemblyPropertyIntent(
        source_properties["configuration"], source_properties["created_at"], "Kit disclosed reconstruction"))
    neutral = wire(request)
    require(fingerprint(neutral) == prior["neutral_request_sha256"],
            "assembly bookkeeping must use the exact prior neutral request")
    expected = prior["generated"]
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", expected["parent_sha256"])
    first, second = (subprocess.run(command, input=neutral, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent guarded bookkeeping builds disagree")
    generated = json.loads(first.stdout)
    require(generated["child_sha256"] == expected["child_sha256"]
            and generated["actual_mate"] == expected["actual_mate"]
            and generated["properties"] == expected["added_streams"],
            "the previously verified child, actual mate or property scopes changed")
    generated["unrepresented_source_streams"] = sorted(
        set(original["after"]["original_streams"]) - set(generated["parent_streams"]))
    result = {
        "schema": "kit.sw2026.disclosed-d01-assembly-bookkeeping.v1", "base": BASE, "integration": INTEGRATION,
        "prior_receipt_sha256": PRIOR_SHA, "disclosed_corpus_sha256": CORPUS,
        "neutral_request_sha256": fingerprint(neutral), "native_probes": 0, "heldout_accesses": 0,
        "guarded_generated_workers": 2, "whole_source_admitted": False, "public_publication": False,
        "source_original_refusal": original["after"]["strict_source_refusal"],
        "disclosed_sources": stamp_receipts, "generated": generated,
        "source_sha256": {str(path.relative_to(REPO)): fingerprint(path.read_bytes()) for path in
                          (HERE, HERE.with_name("D01AssemblyStampStreams.py"))},
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
