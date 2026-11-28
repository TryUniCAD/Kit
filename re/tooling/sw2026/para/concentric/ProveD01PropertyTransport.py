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
from D01AssemblyPropertyIntent import CORE, CUSTOM, AssemblyPropertyIntent, add_property_streams
from D01AssemblyStampStreams import add_stamp_streams
from ProveConcentricCmgrHistory import disclosed_cases, refuse
from AssemblyUnitTable import add_unit_stream
from ObserveAssemblyUnitOwners import CASE_MANIFESTS
from AssemblyPropertyTransport import (
    APP, TRANSPORT, ApplicationProperties, add_property_transport, read_property_transport,
)

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakeCoreProps import MakeCoreProps
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakeCustomProps import MakeCustomProps
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KContentTypesStream, KRelationshipsStream
from interchange.serialization.Deserialize import FromData


BASE = "4f7ce7b398c7e2493f8fa4351190e30e41a7bc45"
PRIOR = "ConcentricD01UserUnitTable01.json"
PRIOR_SHA = "d28682ed658e02680583ae378181ee096d167edead5ebbf1568e954369587aa1"


def inventory(streams):
    return {key: {"bytes": len(streams[key]), "sha256": fingerprint(streams[key])} for key in TRANSPORT}


def inspect_source(source, pin):
    archive = SldprtArchive.from_bytes(checked(source, pin))
    app, roles = read_property_transport(archive.streams)
    independent = {key: value for key, value in archive.streams.items() if key not in TRANSPORT}
    regenerated = add_property_transport(independent, app)
    require(tuple(regenerated[key] for key in TRANSPORT) == tuple(archive.require(key) for key in TRANSPORT),
            "the typed native property transport cannot be re-emitted exactly")
    return {"source_sha256": pin, "targets": roles, "scope_streams": inventory(regenerated),
            "application_fields": {
                "application_characters": len(app.application),
                "template_characters": len(app.template),
                "company_characters": len(app.company),
                "edit_minutes": app.edit_minutes,
                "version": app.version,
            }}


def inspect_disclosures(disclosures, known):
    base = disclosures / "ConcentricMateSourcePacket02/Disclosed"
    results = {}
    for case in disclosed_cases():
        slot = case["id"]
        results[slot] = {}
        for phase in ("Source", "Edited"):
            pin = known[slot][phase]["source_sha256"]
            results[slot][phase] = inspect_source(base / slot / "Native" / phase / (case["name"] + ".SLDASM"), pin)
    return results


def inspect_controls():
    results = {}
    corpus = REPO / "re/solidworks/v2026/corpus"
    for folder, (pin, names) in CASE_MANIFESTS.items():
        archive_dir = corpus / folder
        manifest = json.loads(checked(archive_dir / "Manifest.json", pin))
        entries = {row.get("file", row["name"]): row for row in manifest["records"]}
        for name in names:
            results[name] = inspect_source(archive_dir / name, entries[name]["sha256"])
    return results


def contrast_app(properties, scope):
    first = ApplicationProperties("Kit research unit display", "1.0000", "", "", 0)
    second = ApplicationProperties("Kit research unit display", "2.0000", "Bespoke & 校核", "North & East", 37)
    reports = {}
    for label, authored, bag, expected in (
        ("application_only", first, {}, (APP,)),
        ("application_and_core", second, {CORE: MakeCoreProps({"title": "Independent property owner"})}, (APP, CORE)),
        ("all_three", second, {CORE: MakeCoreProps({"title": "Neutral fixture"}),
                              CUSTOM: MakeCustomProps((("Purpose", "Separately authored"),), False)}, (APP, CORE, CUSTOM)),
    ):
        generated = add_property_transport(bag, authored)
        require(read_property_transport(generated) == (authored, expected), "neutral package target selection changed")
        reports[label] = {"scope_streams": inventory(generated), "targets": expected}
    alternative = add_property_transport(properties, second)
    require(set(alternative) == set(scope)
            and {key for key in alternative if alternative[key] != scope[key]} == {APP},
            "an authored application-only change altered its actual relationship topology")
    reports["full_app_only_change"] = {"scope_streams": inventory(alternative)}
    return reports


def refusal_cases(base, emitted, intent):
    missing_core = {key: payload for key, payload in emitted.items() if key != CORE}
    mismatch = emitted | {KRelationshipsStream: emitted[KRelationshipsStream].replace(b'Id="rId3"', b'Id="rId2"')}
    foreign_type = emitted | {KContentTypesStream: emitted[KContentTypesStream].replace(
        b"/docProps/core.xml", b"/docProps/Another.xml")}
    active = emitted | {APP: emitted[APP].replace(b"<SharedDoc>false</SharedDoc>", b"<SharedDoc>true</SharedDoc>")}
    return {
        "missing_target": refuse(lambda: read_property_transport(missing_core), "differs from its actual typed targets"),
        "crossed_relation_id": refuse(lambda: read_property_transport(mismatch), "differs from its actual typed targets"),
        "foreign_type_decl": refuse(lambda: read_property_transport(foreign_type), "differs from its actual typed targets"),
        "unsupported_shared_state": refuse(lambda: read_property_transport(active), "unsupported extended property security"),
        "duplicate_transport": refuse(lambda: add_property_transport(emitted, intent), "already has an emitted stream"),
        "invalid_edit_minutes": refuse(lambda: add_property_transport(base, replace(intent, edit_minutes=-1)),
                                      "nonnegative whole minutes"),
    }


def worker(payload, baseline_digest):
    require(set(payload) == {"model", "application"}, "transport worker accepts only model and application intent")
    request = payload["model"]
    require(set(request) == {"models", "chronology", "properties"}, "unrecognized parent model")
    model = request["models"]
    docs = tuple(FromData(model[key]["document"]) for key in ("before", "after"))
    for document in docs:
        document.assert_valid()
    prop = AssemblyPropertyIntent(**request["properties"])
    app = ApplicationProperties(**payload["application"])
    reg = registry()
    codecs.lookup("utf-8-sig")
    audit = proof_guard()
    models = verify_owned_edit(*docs)
    original, bundle = compose_streams(model, request["chronology"], docs, models, reg)
    state = bundle.StateValue
    headers = (bundle.HeaderValue, bundle.TopHeader)
    properties = add_property_streams(original, state.CurrentConfig, headers, prop)
    with_stamps = add_stamp_streams(properties, state, headers)
    base = add_unit_stream(with_stamps, state)
    baseline = BuildSldprt(base, FormatVersion=4)
    require(fingerprint(baseline) == baseline_digest, "the previous complete 21-stream parent changed")
    composed = add_property_transport(base, app)
    parent = BuildSldprt(composed, FormatVersion=4)
    before, archive = map(SldprtArchive.from_bytes, (baseline, parent))
    roles = (APP, CORE, CUSTOM)
    require(read_property_transport(archive.streams) == (app, roles)
            and stream_diff(before, archive) == set(TRANSPORT) and bound_properties(archive)[0] == prop,
            "property transport changed the scoped model or its existing streamed owners")
    life = observe(parent, bundle, request["chronology"]["after"], model["before"]["root_model_name"], reg)
    mate = mate_readback(parent, bundle, models[1], model["after"])
    contrasts = contrast_app(base, composed)
    refusals = refusal_cases(base, composed, app)
    require(not audit, "property transport construction accessed an external file, process or network")
    return {"baseline_parent_sha256": fingerprint(baseline), "parent_sha256": fingerprint(parent),
            "parent_bytes": len(parent), "child_sha256": life["child_sha256"], "actual_mate": mate,
            "ordinary_streams_unchanged": len(before.streams), "parent_streams": sorted(archive.streams),
            "transport_streams": inventory(archive.streams), "targets": roles, "authored_contrasts": contrasts,
            "runtime_external_accesses": len(audit), "refusals": refusals}


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
    sources = inspect_disclosures(args.disclosures, prior["disclosed_assembly_sources"])
    controls = inspect_controls()
    owned = disclose_properties(args.disclosures)["D01"]["Edited"]
    request, original, _ = disclose(args.disclosures, registry())
    require(original["after"]["file_sha256"] == owned["parent_sha256"] == sources["D01"]["Edited"]["source_sha256"],
            "property package and model use different source custody")
    request["properties"] = asdict(AssemblyPropertyIntent(
        owned["configuration"], owned["created_at"], "Kit disclosed reconstruction"))
    require(fingerprint(wire(request)) == prior["neutral_request_sha256"], "transport changed the prior neutral model")
    app = ApplicationProperties("Kit property transport research", "1.0000", "", "", 0)
    neutral = wire({"model": request, "application": asdict(app)})
    expected = prior["generated"]
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", expected["parent_sha256"])
    first, second = (subprocess.run(command, input=neutral, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent guarded transport builds disagree")
    generated = json.loads(first.stdout)
    native_d01 = sources["D01"]["Edited"]["scope_streams"]
    require(generated["child_sha256"] == expected["child_sha256"] and generated["actual_mate"] == expected["actual_mate"]
            and all(generated["transport_streams"][key] == native_d01[key] for key in (KContentTypesStream, KRelationshipsStream))
            and generated["transport_streams"][APP] != native_d01[APP],
            "the generated property index or existing owned geometry changed, or native app provenance was reused")
    generated["unrepresented_source_streams"] = sorted(
        set(original["after"]["original_streams"]) - set(generated["parent_streams"]))
    result = {"schema": "kit.sw2026.disclosed-d01-property-transport.v1", "base": BASE,
              "prior_receipt_sha256": PRIOR_SHA, "neutral_request_sha256": fingerprint(neutral),
              "native_probes": 0, "heldout_accesses": 0, "guarded_generated_workers": 2,
              "whole_source_admitted": False, "public_publication": False,
              "source_original_refusal": original["after"]["strict_source_refusal"],
              "disclosed_sources": sources, "independent_assembly_controls": controls, "generated": generated,
              "source_sha256": {str(path.relative_to(REPO)): fingerprint(path.read_bytes())
                                for path in (HERE, HERE.with_name("AssemblyPropertyTransport.py"))}}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
