from argparse import ArgumentParser
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01ModelExchange import (
    MEASUREMENTS,
    PRIOR,
    PRIOR_PIN,
    PROOF,
    PROOF_PIN,
    REPO,
    checked,
    fingerprint,
    generate,
    model_inputs,
    neutral_request,
    refuse,
    require,
    source_cases,
    stream_diff,
    wire,
)
from AssemblyInformation import KInfoXml, add_assembly_information, assembly_information

from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot

BASE = "d89dd5965880fda9b645336527b20fc02557d4e9"
MODEL = "D01ModelExchange01.json"
MODEL_PIN = "320d19067f29337c7fe572d17bf6b32f1293b63023c3139223b6a6ec748add32"


def system_rows(payload):
    (section,) = ReadPropRoot(payload)
    rows = tuple(
        (row.get("name"), row[0].tag, row[0].text or "")
        for row in section
        if row.tag == "property"
    )
    require(
        len(rows) == 49 and len({name for name, _, _ in rows}) == 49,
        "system information has a different property inventory",
    )
    return tuple((name, value) for name, _, value in rows)


def compare_sources(location, properties):
    result = {}
    for label, path, pin in source_cases(location, properties):
        archive = SldprtArchive.from_bytes(checked(path, pin))
        projected = assembly_information(archive, path.name, -480)
        require(
            projected == archive.require(KInfoXml),
            "assembly system information differs in " + label,
        )
        result[label] = {
            "source_sha256": pin,
            "stream_sha256": fingerprint(projected),
            "stream_bytes": len(projected),
            "property_rows": len(system_rows(projected)),
        }
    require(len(result) == 12, "ordinary assembly information control cohort changed")
    return result


def worker(inputs, expected_config, expected_model):
    payload = inputs["model"]
    earlier, child, previous, accesses = generate(payload, expected_config)
    require(
        previous["parent_sha256"] == expected_model,
        "previous full model exchange parent changed",
    )
    before = SldprtArchive.from_bytes(earlier)
    observations = {}
    for event in inputs["publication"]:
        name, clock = event["output"], event["offset_minutes"]
        streams = add_assembly_information(before.streams, before, name, clock)
        data = BuildSldprt(streams, FormatVersion=4)
        after = SldprtArchive.from_bytes(data)
        require(
            stream_diff(before, after) == {KInfoXml} and len(after.streams) == 35,
            "system information changed the assembly stream owners",
        )
        info = after.require(KInfoXml)
        rows = dict(system_rows(info))
        require(
            rows["SW-File Name"] == PureWindowsPath(name).stem,
            "system information loses the authored destination",
        )
        observations[event["name"]] = {
            "parent_sha256": fingerprint(data),
            "parent_bytes": len(data),
            "streams": len(after.streams),
            "prior_parent_streams_unchanged": len(before.streams),
            "information_sha256": fingerprint(info),
            "information_bytes": len(info),
            "native_filename": rows["SW-File Name"],
            "local_save_date": rows["SW-Short Date"],
            "property_rows": len(rows),
        }
    first, second = observations.values()
    require(
        first["information_sha256"] != second["information_sha256"]
        and first["local_save_date"] != second["local_save_date"],
        "independent calendar and filename did not vary the information stream",
    )
    rejections = {
        "duplicate_owner": refuse(
            lambda: add_assembly_information(streams, before, name, clock),
            "already has an owner",
        ),
        "unowned_clock": refuse(
            lambda: assembly_information(before, name, 1000), "explicit local clock"
        ),
        "foreign_type": refuse(
            lambda: assembly_information(before, "Foreign.sldprt", clock),
            "actual output filename",
        ),
    }
    require(not accesses, "system information accessed external runtime inputs")
    return {
        "baseline_sha256": expected_model,
        "child_sha256": fingerprint(child),
        "profiles": observations,
        "refusals": rejections,
        "runtime_external_accesses": len(accesses),
    }


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", nargs=2)
    mode.add_argument("--disclosures", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin), *args.worker)))
        return
    require(
        args.output is not None,
        "specify an unused assembly information receipt destination",
    )
    pins = {PRIOR: PRIOR_PIN, PROOF: PROOF_PIN, MODEL: MODEL_PIN}
    receipts = {
        name: json.loads(checked(MEASUREMENTS / name, pin))
        for name, pin in pins.items()
    }
    config, properties, model = (receipts[name] for name in (PRIOR, PROOF, MODEL))
    source = compare_sources(args.disclosures, properties)
    neutral = neutral_request(args.disclosures, properties)
    model_request = model_inputs(neutral, config)
    actual_destination = model_request["neutral"]["model"]["models"]["after"][
        "destination"
    ]
    request = wire(
        {
            "model": model_request,
            "publication": [
                {
                    "name": "working_destination",
                    "output": actual_destination,
                    "offset_minutes": -480,
                },
                {
                    "name": "authored_alternate",
                    "output": "C:\\KitInfo\\R&D \u2013 \u03bc assembly.SLDASM",
                    "offset_minutes": 780,
                },
            ],
        }
    )
    model_hash = model["generated"]["parent_sha256"]
    command = (
        sys.executable,
        "-I",
        "-B",
        str(HERE),
        "--worker",
        model["generated"]["prior_parent_sha256"],
        model_hash,
    )
    first, second = (
        subprocess.run(command, input=request, capture_output=True, timeout=120)
        for _ in range(2)
    )
    require(
        first.returncode == second.returncode == 0 and first.stdout == second.stdout,
        (first.stderr + second.stderr).decode()
        or "guarded assembly information builds differ",
    )
    generated = json.loads(first.stdout)
    require(
        generated["child_sha256"] == model["generated"]["child_sha256"],
        "assembly information changed the linked child",
    )
    missing = set(model["unrepresented_source_streams"]) - {KInfoXml}
    require(len(missing) == 8, "unrepresented source inventory differs")
    tools = (
        HERE,
        HERE.with_name("AssemblyInformation.py"),
        REPO / "re/solidworks/WriterResearch/PartInformation.py",
    )
    out = wire(
        {
            "schema": "kit.sw2026.d01-assembly-system-information.v1",
            "base": BASE,
            "pinned_receipts": pins,
            "source_controls": source,
            "guarded_generated_workers": 2,
            "generated": generated,
            "worker_input_sha256": fingerprint(request),
            "unrepresented_source_streams": sorted(missing),
            "native_processes_started": 0,
            "heldout_inputs_read": 0,
            "whole_source_admitted": False,
            "tool_sha256": {
                path.name: fingerprint(path.read_bytes()) for path in tools
            },
        }
    )
    with args.output.open("xb") as output:
        output.write(out)


if __name__ == "__main__":
    main()
