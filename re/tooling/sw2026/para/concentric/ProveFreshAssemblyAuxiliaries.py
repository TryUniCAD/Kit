from argparse import ArgumentParser
from dataclasses import asdict
import codecs
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveAssemblyContentIndex import (
    ApplicationProperties,
    AssemblyPropertyIntent,
    CONTENT_INDEX,
    MEASUREMENTS,
    PROOF,
    PROOF_PIN,
    assemble,
    checked,
    disclose,
    disclose_properties,
    fingerprint,
    make_content_index,
    prepare_package,
    proof_guard,
    registry,
    require,
    selected_config,
    source_cases,
    stream_diff,
    wire,
)
from FreshAssemblyAuxiliaries import (
    MEMBERS,
    add_fresh_assembly_auxiliaries,
    fresh_assembly_auxiliaries,
)
from InspectPartEnvironmentSource import Image
from ProveConcentricCmgrHistory import refuse

from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

BASE = "2e3c2ab7c83ae5f6632dbc0bf64482f7546d8bab"
PRIOR = "AssemblyContentIndex01.json"
PRIOR_PIN = "dc937c1c3cfc373b334944500cc8a299e2afb7a6822b12535a8432e57d34a90c"
MFC_PIN = "af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735"
NATIVE_LABELS = {
    0x3CC6B0A0: "TotalFileOpenTime",
    0x3CC6B0F8: "LWTotalFileOpenTime",
    0x3CC6B190: "OpenTime.xml",
    0x3CC7F040: "OleItems",
    0x3CC806C8: "CM_MOTION_LOAD_1",
    0x3CC809D0: "SWA_Schedules",
    0x3CC80AF0: "CMMotionLoadMapU",
    0x3CC810EE: "-Attachment",
}


def native_rules(module):
    image = Image(module, MFC_PIN)
    for address, text in NATIVE_LABELS.items():
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        require(
            image.read(address, address + len(encoded)) == encoded,
            "native auxiliary storage vocabulary changed",
        )
    storage = image.read(0x3C7C940F, 0x3C7C9425)
    require(
        storage
        == bytes.fromhex(
            "33 c0 89 43 10 c7 43 14 ff ff ff ff 89 43 18 c7 43 1c ff ff ff ff"
        ),
        "native timing option defaults changed",
    )
    return {
        "build": "34.5.2.0604",
        "module_sha256": MFC_PIN,
        "time_constructor_initialization": {
            "va": "0x3c7c940f",
            "end_exclusive": "0x3c7c9425",
            "sha256": fingerprint(storage),
            "members": [0, -1, 0, -1],
        },
        "storage_label_addresses": {
            name: hex(address) for address, name in NATIVE_LABELS.items()
        },
    }


def inventory(streams):
    return {
        name: {"bytes": len(streams[name]), "sha256": fingerprint(streams[name])}
        for name in sorted(MEMBERS)
    }


def source_controls(location, property_receipt):
    composed = fresh_assembly_auxiliaries()
    measurements = {}
    for name, path, pin in source_cases(location, property_receipt):
        source = SldprtArchive.from_bytes(checked(path, pin))
        expected = {key: source.require(key) for key in MEMBERS}
        require(
            composed == expected,
            "fresh auxiliary scope differs in disclosed source " + name,
        )
        measurements[name] = {
            "source_sha256": pin,
            "matched_generated_streams": len(expected),
        }
    require(len(measurements) == 11, "disclosed auxiliary cohort changed")
    return measurements, inventory(composed)


def build_case(payload, prior_parent):
    request, documents, models, properties, application = prepare_package(payload)
    reg = registry()
    for encoding in ("utf-8-sig", "latin-1"):
        codecs.lookup(encoding)
    accesses = proof_guard()
    streams, bundle, headers = assemble(
        request, documents, models, properties, application, reg
    )
    state = bundle.StateValue
    config = selected_config(state.ManagerValue)
    index = make_content_index(state.RootValue, config, headers, bundle.MateValues, reg)
    previous = streams | {CONTENT_INDEX: index}
    baseline = BuildSldprt(previous, FormatVersion=4)
    require(
        fingerprint(baseline) == prior_parent,
        "the prior complete indexed parent changed",
    )
    present = add_fresh_assembly_auxiliaries(previous)
    generated = BuildSldprt(present, FormatVersion=4)
    before, after = map(SldprtArchive.from_bytes, (baseline, generated))
    require(
        stream_diff(before, after) == MEMBERS
        and all(after.require(key) == present[key] for key in MEMBERS)
        and not accesses,
        "fresh auxiliaries changed prior streams or read external data",
    )
    return {
        "baseline_parent_sha256": prior_parent,
        "parent_sha256": fingerprint(generated),
        "parent_bytes": len(generated),
        "parent_streams": sorted(after.streams),
        "prior_streams_unchanged": len(before.streams),
        "child_sha256": fingerprint(bundle.ChildValue.BytesValue),
        "members": inventory(present),
        "runtime_external_accesses": len(accesses),
        "duplicate_refusal": refuse(
            lambda: add_fresh_assembly_auxiliaries(present), "already have an owner"
        ),
    }


def neutral_request(location, property_receipt):
    reg = registry()
    request, _, _ = disclose(location, reg)
    properties = disclose_properties(location)["D01"]["Edited"]
    request["properties"] = asdict(
        AssemblyPropertyIntent(
            properties["configuration"],
            properties["created_at"],
            "Kit disclosed reconstruction",
        )
    )
    application = ApplicationProperties(
        "Kit property transport research", "1.0000", "", "", 0
    )
    payload = wire({"model": request, "application": asdict(application)})
    require(
        fingerprint(payload) == property_receipt["neutral_request_sha256"],
        "fresh auxiliaries changed the established neutral input",
    )
    return payload


def main():
    parser = ArgumentParser()
    run = parser.add_mutually_exclusive_group(required=True)
    run.add_argument("--disclosures", type=Path)
    run.add_argument("--worker")
    parser.add_argument("--mfc-module", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(build_case(json.load(sys.stdin), args.worker)))
        return
    require(
        args.output is not None and args.mfc_module is not None,
        "pin the native module and output path",
    )
    prior = json.loads(checked(MEASUREMENTS / PRIOR, PRIOR_PIN))
    properties = json.loads(checked(MEASUREMENTS / PROOF, PROOF_PIN))
    native = native_rules(args.mfc_module)
    sources, chosen = source_controls(args.disclosures, properties)
    neutral = neutral_request(args.disclosures, properties)
    command = (
        sys.executable,
        "-I",
        "-B",
        str(HERE),
        "--worker",
        prior["generated"]["parent_sha256"],
    )
    first, second = (
        subprocess.run(command, input=neutral, capture_output=True, timeout=120)
        for _ in range(2)
    )
    require(
        first.returncode == second.returncode == 0 and first.stdout == second.stdout,
        (first.stderr + second.stderr).decode() or "guarded auxiliary builds differ",
    )
    built = json.loads(first.stdout)
    require(
        built["members"] == chosen
        and built["child_sha256"] == prior["generated"]["child_sha256"],
        "fresh default members or prior child differ",
    )
    remaining = set(prior["unrepresented_source_streams"]) - MEMBERS
    require(
        len(remaining) == 11 and len(built["parent_streams"]) == 32,
        "fresh auxiliary inventory did not advance the scoped parent",
    )
    out = wire(
        {
            "schema": "kit.sw2026.fresh-assembly-auxiliaries.v1",
            "base": BASE,
            "native_rules": native,
            "prior_receipt_sha256": PRIOR_PIN,
            "source_controls": sources,
            "whole_source_admitted": False,
            "unrepresented_source_streams": sorted(remaining),
            "guarded_generated_workers": 2,
            "generated": built,
            "native_processes_started": 0,
            "heldout_inputs_read": 0,
            "runner_sha256": fingerprint(HERE.read_bytes()),
            "emitter_sha256": fingerprint(
                HERE.with_name("FreshAssemblyAuxiliaries.py").read_bytes()
            ),
        }
    )
    with args.output.open("xb") as file:
        file.write(out)
    print(
        json.dumps(
            {
                "sha256": fingerprint(out),
                "disclosures": len(sources),
                "members": len(MEMBERS),
                "parent_streams": len(built["parent_streams"]),
            }
        )
    )


if __name__ == "__main__":
    main()
