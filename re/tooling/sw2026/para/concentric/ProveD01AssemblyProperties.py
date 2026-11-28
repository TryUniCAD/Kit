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
from ProveConcentricCmgrHistory import CORPUS, disclosed_cases, refuse
from ReadConcentricCmgrInputs import MANAGER_HEADER, config_owner
from D01AssemblyPropertyIntent import (
    CONFIG, CORE, CUSTOM, MANAGER, SCOPE_KEYS, AssemblyPropertyIntent, add_property_streams,
    configuration_and_save, make_core, make_property_manager, read_core, read_property_manager,
)
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakeCustomProps import MakeCustomProps
from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropManager
from convert.adapters.solidworks.Archive.Properties.WriteEmptyProps import WriteEmptyProps
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadRows, RequireNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps
from interchange.serialization.Deserialize import FromData


BASE = "3b5caa3b599b2184f32260e8b383d15044946d5f"
PRIOR = "ConcentricD01AssemblyChronology01.json"
PRIOR_SHA = "72aef4ea3efea4b499fc1cb878ce1b38bae985b627e8ace367189007b75bd800"


def stream_receipt(archive):
    return {key: {"sha256": fingerprint(archive.require(key)), "bytes": len(archive.require(key))}
            for key in sorted(SCOPE_KEYS)}


def bound_properties(archive, headers=None):
    if headers is None:
        headers, _ = archive_roles(archive)
    name, save_at = configuration_and_save(config_owner(archive, "moConfiguration_c"), headers)
    directory = ReadMgrHeader(archive.require(MANAGER_HEADER), 19000).RootValue
    entry, = ReadRows(directory.FieldsValue["f08"]["items"])
    fields = RequireNode(entry["o"], "dmConfigHeader_c").FieldsValue
    require((fields["f08"], fields["f10"], fields["f30"], fields["f34"]) == (1, name, 0, -1)
            and WriteMgrHeader(directory, 19000)[0] == archive.require(MANAGER_HEADER)
            and tuple(key for key in archive.streams if key.startswith("docProps/Config-")) == (CONFIG,),
            "assembly property lane is detached from the only active directory owner")
    manager = archive.require(MANAGER)
    end = read_property_manager(manager)
    require(manager == make_property_manager(), "generative assembly property manager differs from source")
    require(all(ReadCustomProps(archive.require(key), scoped) == {}
                and MakeCustomProps((), scoped) == archive.require(key)
                for key, scoped in ((CUSTOM, False), (CONFIG, True))),
            "assembly text has authored values requiring a separate input profile")
    actor, created, modified = read_core(archive.require(CORE))
    intent = AssemblyPropertyIntent(name, created, actor)
    require(modified == save_at and make_core(intent, save_at) == archive.require(CORE),
            "assembly summary has unaffiliated time or text")
    return intent, {"terminal_map": end, "configuration": name, "created_at": created,
                    "created_minus_header_creation_s": created - headers[0].FieldsValue["f70"],
                    "modified_at": modified, "modified_minus_header_save_s": modified - save_at,
                    "streams": stream_receipt(archive)}


def disclose_properties(disclosures):
    report = REPO / "re/solidworks/measurements/2026/ConcentricMateSourceArchive01.json"
    corpus = json.loads(checked(report, CORPUS))["cases"]
    base = disclosures / "ConcentricMateSourcePacket02/Disclosed"
    output = {}
    for case in disclosed_cases():
        slot = case["id"]
        case_evidence = corpus[slot]
        require(case_evidence["heldout_source_locked"] is False, "only the already disclosed cases may be read")
        output[slot] = {}
        for phase in ("Source", "Edited"):
            directory = base / slot / "Native" / phase
            pins = case_evidence["native_artifact_digests"][phase.lower()]
            original = SldprtArchive.from_bytes(checked(directory / (case["name"] + ".SLDASM"), pins["parent"]["sha256"]))
            child = SldprtArchive.from_bytes(checked(directory / (case["child_name"] + ".SLDPRT"), pins["child"]["sha256"]))
            _, properties = bound_properties(original)
            child_manager = child.require(MANAGER)
            ReadPropManager(child_manager, 19000)
            properties["part_owner_refusal"] = refuse(lambda: read_property_manager(child_manager), "unsupported concrete")
            properties["parent_sha256"] = pins["parent"]["sha256"]
            properties["child_sha256"] = pins["child"]["sha256"]
            output[slot][phase] = properties
        source, edited = (output[slot][phase] for phase in ("Source", "Edited"))
        require(source["created_at"] == edited["created_at"] and source["modified_at"] < edited["modified_at"],
                "archive property package creation and successive save ownership differ")
    return output


def worker(request, baseline_digest):
    require(set(request) == {"models", "chronology", "properties"}, "unknown assembly property worker input")
    model = request["models"]
    docs = tuple(FromData(model[key]["document"]) for key in ("before", "after"))
    for document in docs:
        document.assert_valid()
    intent = AssemblyPropertyIntent(**request["properties"])
    reg = registry()
    codecs.lookup("utf-8-sig")
    audit = proof_guard()
    models = verify_owned_edit(*docs)
    base, bundle = compose_streams(model, request["chronology"], docs, models, reg)
    base_bytes = BuildSldprt(base, FormatVersion=4)
    require(fingerprint(base_bytes) == baseline_digest, "prior exact chronology output changed")
    config = bundle.StateValue.CurrentConfig
    headers = (bundle.HeaderValue, bundle.TopHeader)
    parent = BuildSldprt(add_property_streams(base, config, headers, intent), FormatVersion=4)
    archive = SldprtArchive.from_bytes(parent)
    read, properties = bound_properties(archive)
    prior_title = model["before"]["root_model_name"]
    proof = observe(parent, bundle, request["chronology"]["after"], prior_title, reg)
    mate = mate_readback(parent, bundle, models[1], model["after"])
    before = SldprtArchive.from_bytes(base_bytes)
    fresh = replace(intent, created_at=intent.created_at + 173, save_actor="Kit & model author")
    contrast = SldprtArchive.from_bytes(BuildSldprt(add_property_streams(base, config, headers, fresh), FormatVersion=4))
    varied, _ = bound_properties(contrast)
    require(read == intent and varied == fresh and stream_diff(before, archive) == SCOPE_KEYS
            and stream_diff(archive, contrast) == {CORE}
            and not audit, "property scopes or their chronology affected unrelated generated archive data")
    negatives = {
        "part_owner_class": refuse(lambda: read_property_manager(WriteEmptyProps(19000)), "unsupported concrete"),
        "independent_config": refuse(lambda: add_property_streams(base, config, headers, replace(intent, configuration="elsewhere")),
                                     "different configuration"),
        "competing_property_stream": refuse(lambda: add_property_streams(base | {CONFIG: b""}, config, headers, intent),
                                            "already emitted scope"),
        "future_creation_event": refuse(lambda: make_core(replace(intent, created_at=0xFFFFFFFF), properties["modified_at"]),
                                        "follows its final save"),
        "unrepresented_core_field": refuse(lambda: read_core(archive.require(CORE).replace(b"</cp:coreProperties>",
                                                                                         b"<dc:title>owned</dc:title></cp:coreProperties>")),
                                           "unprojected fields"),
    }
    require(not audit, "refusal path performed external access")
    return {"parent_sha256": fingerprint(parent), "parent_bytes": len(parent),
            "child_sha256": proof["child_sha256"], "base_parent_sha256": fingerprint(base_bytes),
            "ordinary_streams_unchanged": len(before.streams), "added_streams": properties,
            "parent_streams": sorted(archive.streams),
            "changed_creation_actor_core_only": True, "actual_mate": mate,
            "runtime_external_accesses": len(audit), "refusals": negatives}


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
    prior = json.loads(prior_bytes)["generated"]["original_chronology"]
    baseline = prior["parent_sha256"]
    sources = disclose_properties(args.disclosures)
    request, original, _ = disclose(args.disclosures, registry())
    source_properties = sources["D01"]["Edited"]
    require(original["after"]["file_sha256"] == source_properties["parent_sha256"],
            "root owner and projected property scopes differ in source custody")
    request["properties"] = asdict(AssemblyPropertyIntent(
        source_properties["configuration"], source_properties["created_at"], "Kit disclosed reconstruction"))
    neutral = wire(request)
    command = (sys.executable, "-I", "-B", str(HERE), "--worker", baseline)
    first, second = (subprocess.run(command, input=neutral, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent guarded property builds disagree")
    generated = json.loads(first.stdout)
    require(generated["child_sha256"] == prior["child_sha256"]
            and generated["added_streams"]["streams"][MANAGER] == source_properties["streams"][MANAGER]
            and all(generated["added_streams"]["streams"][key] == source_properties["streams"][key]
                    for key in (CUSTOM, CONFIG)),
            "concentric property graph changed the generated child or an empty source-owned bag")
    generated["unrepresented_source_streams"] = sorted(
        set(original["after"]["original_streams"]) - set(generated["parent_streams"]))
    result = {
        "schema": "kit.sw2026.disclosed-d01-assembly-properties.v1", "base": BASE,
        "prior_receipt_sha256": fingerprint(prior_bytes), "disclosed_corpus_sha256": CORPUS,
        "neutral_request_sha256": fingerprint(neutral), "native_probes": 0, "heldout_accesses": 0,
        "guarded_generated_workers": 2, "whole_source_admitted": False, "public_publication": False,
        "source_original_refusal": original["after"]["strict_source_refusal"],
        "disclosed_sources": sources, "generated": generated,
        "source_sha256": {str(path.relative_to(REPO)): fingerprint(path.read_bytes()) for path in
                          (HERE, HERE.with_name("D01AssemblyPropertyIntent.py"),
                           HERE.with_name("ProveD01AssemblyChronology.py"))},
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
