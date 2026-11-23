from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import asdict, replace
import codecs
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01AssemblyChronology import (
    REPO,
    checked,
    compose_streams,
    disclose,
    fingerprint,
    mate_readback,
    observe,
    proof_guard,
    registry,
    require,
    stream_diff,
    verify_owned_edit,
    wire,
)
from ProveD01AssemblyProperties import disclose_properties
from ProveConcentricCmgrHistory import disclosed_cases, refuse
from AssemblyContentIndex import (
    CONTENT_INDEX,
    make_content_index,
    read_content_index,
    selected_config,
)
from AssemblyPropertyTransport import ApplicationProperties, add_property_transport
from AssemblyUnitTable import add_unit_stream
from D01AssemblyPropertyIntent import AssemblyPropertyIntent, add_property_streams
from D01AssemblyStampStreams import add_stamp_streams
from ObserveAssemblyUnitOwners import CASE_MANIFESTS
from PinAssemblyContentIndex import verify_native_content
from Streams import store_rooted

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import (
    BuildSldprt,
    SldprtArchive,
    StreamRecord,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData

BASE = "935d9848dab052aff0bc4495faa579e011cc7cba"
PROOF = "ConcentricD01PropertyTransport01.json"
PROOF_PIN = "676fb1e7e56e929d880a7de1471acf7cb456b70f9fec862f00961fc597736c51"
MEASUREMENTS = REPO / "re/solidworks/measurements/2026"
CONFIG = "Contents/Config-0"
HEADER = CONFIG + "-ModelHeader"
RESOLVED = CONFIG + "-ResolvedFeatures"
MATES = CONFIG + "-MatesList"
CMGR = "Contents/CMgr"
TOP = "Header2"
REQUIRED = frozenset({CONFIG, HEADER, RESOLVED, MATES, CMGR, TOP})


def source_cases(base, prior):
    location = base / "ConcentricMateSourcePacket02/Disclosed"
    for case in disclosed_cases():
        for phase in ("Source", "Edited"):
            path = location / case["id"] / "Native" / phase / (case["name"] + ".SLDASM")
            pin = prior["disclosed_sources"][case["id"]][phase]["source_sha256"]
            yield case["id"] + "/" + phase, path, pin
    corpus = REPO / "re/solidworks/v2026/corpus"
    for folder, (manifest_pin, names) in CASE_MANIFESTS.items():
        directory = corpus / folder
        manifest = json.loads(checked(directory / "Manifest.json", manifest_pin))
        entries = {row.get("file", row["name"]): row for row in manifest["records"]}
        if folder == "assembly-synchronized":
            names = (*names, "A12SyncedEmpty.SLDASM")
        for name in names:
            yield name, directory / name, entries[name]["sha256"]


def model_owners(archive):
    link = ReadNativeLink(archive, 0)
    manager = ReadCmgrMut(archive.require(CMGR), 19000).RootValue
    headers = link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require(TOP), 19000)
    mates = ReadMatesMut(archive.require(MATES), link.ResolvedValue).RootsValue
    return link.ConfigValue.RootValue, selected_config(manager), headers, mates


def narrow_input(archive):
    require(
        archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
        "content index requires an observed ordinary version-19000 container",
    )
    model_records = tuple(row for row in archive.records if row.name in REQUIRED)
    marker = StreamRecord("_MO_VERSION_19000", b"", 0, 0, 0, 0, 0, b"")
    result = replace(archive, records=(*model_records, marker))
    require(set(result.streams) == REQUIRED | {marker.name}, "incomplete binary owners")
    return result


def source_guard():
    for encoding in ("latin-1", "ascii", "utf-8", "utf-16-le", "utf-16-be", "cp1252"):
        codecs.lookup(encoding)
    audit = {"enabled": False, "external_accesses": 0}

    def check(event, args):
        if audit["enabled"] and event == "open":
            audit["external_accesses"] += 1
            raise RuntimeError(
                "binary owner projection attempted to open a runtime file"
            )

    sys.addaudithook(check)
    return audit


def summarize(data, reg):
    doc, count = read_content_index(data, reg)
    require(
        store_rooted(doc, reg, 19000) == data,
        "the new content index did not round-trip",
    )
    (mode,) = doc.roots
    (configuration,) = (row["o"] for row in mode["f38"]["items"])
    root, *rows = (row["o"] for row in configuration["f20"]["f08"]["items"])
    require(
        bool(mode["f30"]) == (not rows) and bool(root["fb0"]) == (not rows),
        "content index blank flags disagree with the actual inventory",
    )
    return {
        "bytes": len(data),
        "sha256": fingerprint(data),
        "map_next": count,
        "title_characters": len(mode["f28"]),
        "locator_characters": len(mode["f08"]),
        "occurrence_ids": [row["f08"] for row in rows],
        "mate_ids": [row["o"]["f3c"] for row in root["f50"]["items"]],
        "header_clocks": [mode["f10"], mode["f18"], mode["f20"]],
        "units": [mode["ff4"], mode["ff8"], mode["ffc"]],
    }


def prove_sources(base, prior, reg):
    audit = source_guard()
    result = {}
    refused = []
    for label, path, pin in source_cases(base, prior):
        archive = SldprtArchive.from_bytes(checked(path, pin))
        model = narrow_input(archive)
        audit["enabled"] = True
        try:
            generated = make_content_index(*model_owners(model), reg)
            if not result:
                for name in sorted(REQUIRED):
                    incomplete = replace(
                        model,
                        records=tuple(row for row in model.records if row.name != name),
                    )
                    try:
                        _ = make_content_index(*model_owners(incomplete), reg)
                    except SldprtFormat as error:
                        require(
                            str(error) == "required stream is missing: " + name,
                            "binary owner refusal did not name its missing source",
                        )
                        refused.append(name)
                    else:
                        raise ValueError(
                            "content index accepted missing binary owner: " + name
                        )
        finally:
            audit["enabled"] = False
        require(
            generated == archive.require(CONTENT_INDEX),
            "source-derived content index differs: " + label,
        )
        result[label] = {"source_sha256": pin, **summarize(generated, reg)}
    require(
        len(result) == 11
        and len(refused) == len(REQUIRED)
        and not audit["external_accesses"],
        "disclosed cohort, missing-owner or file-access accounting changed",
    )
    return result, refused


def prepare_package(inputs):
    request = inputs["model"]
    model = request["models"]
    documents = tuple(FromData(model[key]["document"]) for key in ("before", "after"))
    for document in documents:
        document.assert_valid()
    properties = AssemblyPropertyIntent(**request["properties"])
    application = ApplicationProperties(**inputs["application"])
    models = verify_owned_edit(*documents)
    return request, documents, models, properties, application


def assemble(request, documents, models, properties, application, reg):
    streams, bundle = compose_streams(
        request["models"], request["chronology"], documents, models, reg
    )
    state = bundle.StateValue
    headers = bundle.HeaderValue, bundle.TopHeader
    streams = add_property_streams(streams, state.CurrentConfig, headers, properties)
    streams = add_unit_stream(add_stamp_streams(streams, state, headers), state)
    streams = add_property_transport(streams, application)
    return streams, bundle, headers


def controls(state, headers, mates, reg):
    root, config = state.RootValue, state.CurrentConfig
    top_fields = headers[1].FieldsValue
    stale = replace(headers[1], FieldsValue=top_fields | {"f40": top_fields["f40"] + 1})
    bad_config = replace(config, FieldsValue=config.FieldsValue | {"f08": 77})
    duplicate = replace(
        config,
        FieldsValue=config.FieldsValue
        | {
            "fce8": [*config.FieldsValue["fce8"], config.FieldsValue["fce8"][-1]],
        },
    )
    incomplete = replace(
        config,
        FieldsValue=config.FieldsValue
        | {
            "fce8": config.FieldsValue["fce8"][:-1],
        },
    )
    return {
        "stale_header": refuse(
            lambda: make_content_index(root, config, (headers[0], stale), mates, reg),
            "header time and locator owners disagree",
        ),
        "unselected_config": refuse(
            lambda: make_content_index(root, bad_config, headers, mates, reg),
            "ordinary assembly and named root configuration",
        ),
        "duplicate_occurrence": refuse(
            lambda: make_content_index(root, duplicate, headers, mates, reg),
            "foreign or repeated occurrence",
        ),
        "missing_occurrence": refuse(
            lambda: make_content_index(root, incomplete, headers, mates, reg),
            "omitted an actual occurrence",
        ),
    }


def generated_case(inputs, expected, variant):
    request, documents, models, properties, application = prepare_package(inputs)
    reg = registry()
    codecs.lookup("utf-8-sig")
    audit = proof_guard()
    streams, bundle, headers = assemble(
        request, documents, models, properties, application, reg
    )
    baseline = BuildSldprt(streams, FormatVersion=4)
    require(
        len(streams) == 24 and CONTENT_INDEX not in streams,
        "the prior assembled parent changed stream inventory",
    )
    if variant == "original":
        require(
            fingerprint(baseline) == expected,
            "the previous complete 24-stream parent changed",
        )
    state = bundle.StateValue
    config = selected_config(state.ManagerValue)
    require(
        config is state.CurrentConfig,
        "writer and manager selected different configurations",
    )
    index = make_content_index(state.RootValue, config, headers, bundle.MateValues, reg)
    parent = BuildSldprt(streams | {CONTENT_INDEX: index}, FormatVersion=4)
    earlier, archive = map(SldprtArchive.from_bytes, (baseline, parent))
    require(
        stream_diff(earlier, archive) == {CONTENT_INDEX}
        and archive.require(CONTENT_INDEX) == index
        and make_content_index(*model_owners(narrow_input(archive)), reg) == index,
        "content index changed prior publication or disagreed with the generated assembly model",
    )
    life = observe(
        parent,
        bundle,
        request["chronology"]["after"],
        request["models"]["before"]["root_model_name"],
        reg,
    )
    mate = mate_readback(parent, bundle, models[1], request["models"]["after"])
    invalid = controls(state, headers, bundle.MateValues, reg)
    require(
        not audit,
        "content index generation performed a runtime file, network or process access",
    )
    return {
        "variant": variant,
        "parent_bytes": len(parent),
        "parent_sha256": fingerprint(parent),
        "baseline_parent_sha256": fingerprint(baseline),
        "parent_streams": len(archive.streams),
        "unchanged_parent_streams": len(earlier.streams),
        "generated_stream_names": sorted(archive.streams),
        "child_sha256": life["child_sha256"],
        "actual_mate": mate,
        "index": summarize(index, reg),
        "runtime_external_accesses": len(audit),
        "refusals": invalid,
    }


def run_worker(arguments, request, expected, variant):
    command = (
        sys.executable,
        "-I",
        "-B",
        str(HERE),
        "--worker",
        expected,
        "--variant",
        variant,
    )
    completed = subprocess.run(
        command, input=wire(request), capture_output=True, timeout=arguments.timeout
    )
    require(completed.returncode == 0, completed.stderr.decode(errors="replace"))
    return json.loads(completed.stdout)


def model_cases(args, prior, reg):
    owned = disclose_properties(args.disclosures)["D01"]["Edited"]
    request, source, _ = disclose(args.disclosures, reg)
    require(
        source["after"]["file_sha256"] == owned["parent_sha256"],
        "property and assembly model source custody differ",
    )
    request["properties"] = asdict(
        AssemblyPropertyIntent(
            owned["configuration"], owned["created_at"], "Kit disclosed reconstruction"
        )
    )
    preferred = ApplicationProperties(
        "Kit property transport research", "1.0000", "", "", 0
    )
    base = {"model": request, "application": asdict(preferred)}
    require(
        fingerprint(wire(base)) == prior["neutral_request_sha256"],
        "content index changed the earlier neutral assembly",
    )
    alternate = deepcopy(base)
    alternate["model"]["models"]["after"][
        "destination"
    ] = "C:/IndependentPublication/Model placement and archive content contrast/ConcentricD01AlignedFree.SLDASM"
    expected = prior["generated"]["parent_sha256"]
    first = run_worker(args, base, expected, "original")
    second = run_worker(args, base, expected, "original")
    other = run_worker(args, alternate, expected, "relocated")
    require(
        first == second
        and first["child_sha256"] == prior["generated"]["child_sha256"]
        and other["index"]["bytes"] != first["index"]["bytes"]
        and other["index"]["occurrence_ids"] == first["index"]["occurrence_ids"]
        and other["index"]["mate_ids"] == first["index"]["mate_ids"],
        "neutral locator contrast altered topology, or first generation changed",
    )
    remaining = set(source["after"]["original_streams"]) - set(
        first["generated_stream_names"]
    )
    require(
        remaining
        == set(prior["generated"]["unrepresented_source_streams"]) - {CONTENT_INDEX},
        "assembly model source coverage changed outside the content index",
    )
    return first, other, sorted(remaining)


def main():
    parser = ArgumentParser()
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--disclosures", type=Path)
    selector.add_argument("--worker")
    parser.add_argument("--variant", choices=("original", "relocated"))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model-module", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(
            wire(generated_case(json.load(sys.stdin), args.worker, args.variant))
        )
        return
    require(
        args.disclosures.is_absolute()
        and args.output is not None
        and args.model_module is not None,
        "provide disclosures, a pinned model module and a new receipt path",
    )
    prior = json.loads(checked(MEASUREMENTS / PROOF, PROOF_PIN))
    reg = registry()
    native = verify_native_content(args.model_module)
    sources, refusals = prove_sources(args.disclosures, prior, reg)
    generated, relocation, remaining = model_cases(args, prior, reg)
    report = {
        "schema": "kit.sw2026.assembly-content-index.v1",
        "base": BASE,
        "native_format": native,
        "prior_receipt_sha256": PROOF_PIN,
        "source_owner_streams": sorted(REQUIRED),
        "source_index_supplied_to_writer": False,
        "disclosed_sources": sources,
        "missing_owner_refusals": refusals,
        "source_runtime_file_reads": 0,
        "guarded_generated_workers": 3,
        "generated": generated,
        "relocation": relocation,
        "unrepresented_source_streams": remaining,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
        "public_writer_qualified": False,
        "emitter_sha256": fingerprint(
            (HERE.parent / "AssemblyContentIndex.py").read_bytes()
        ),
        "mate_descriptor_sha256": fingerprint(
            (HERE.parent / "AssemblyMateDescriptor.py").read_bytes()
        ),
        "runner_sha256": fingerprint(HERE.read_bytes()),
        "native_verifier_sha256": fingerprint(
            (HERE.parent / "PinAssemblyContentIndex.py").read_bytes()
        ),
    }
    data = wire(report)
    with args.output.open("xb") as target:
        target.write(data)
    print(
        json.dumps(
            {
                "sha256": fingerprint(data),
                "sources": len(sources),
                "generated_workers": 3,
                "generated_bytes": generated["parent_bytes"],
            }
        )
    )


if __name__ == "__main__":
    main()
