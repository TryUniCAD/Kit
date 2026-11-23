from argparse import ArgumentParser
import codecs
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveAssemblyContentIndex import (
    CONTENT_INDEX,
    MEASUREMENTS,
    PROOF,
    PROOF_PIN,
    assemble,
    checked,
    fingerprint,
    make_content_index,
    prepare_package,
    proof_guard,
    registry,
    require,
    stream_diff,
    wire,
)
from ConfigHeaderExchangeModel import CONFIG_HEADER_STREAM, read_config_header
from ConfigHeaderExchangeStore import CMGR_HEADER, add_config_header_exchange
from ProveConfigHeaderExchange import source_cases
from ProveConcentricCmgrHistory import refuse
from ProveFreshAssemblyAuxiliaries import neutral_request
from FreshAssemblyAuxiliaries import add_fresh_assembly_auxiliaries

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Exchange.DatabaseClock import (
    DecodeUnqliteClock,
)
from convert.adapters.solidworks.Archive.Exchange.ReadUnqliteStore import (
    ReadUnqliteStore,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

BASE = "cefe11d61e121d5d3b5ab5403bae111092d668e1"
PRIOR = "FreshAssemblyAuxiliaries01.json"
PRIOR_PIN = "e3683d5e091adf854b75addb17057c2afdf6a9ffa24dd66f7a26a9cee107c2e4"
SEMANTIC = "ConfigHeaderExchange01.json"
SEMANTIC_PIN = "b567c3a30ec7c5ee28a0d40065e8a39fe7c073e3fc14e79ec974a32496ae1c94"
FRAMING = "UnqliteExchangeStore01.json"
FRAMING_PIN = "5057ed36d2792c6737bc05b262749340b944ef898e3a20572b88de695456130f"


def compare_sources(location, properties, projected):
    result = {}
    for name, path, pin in source_cases(location, properties):
        archive = SldprtArchive.from_bytes(checked(path, pin))
        stored = archive.require(CONFIG_HEADER_STREAM)
        require(
            fingerprint(stored) == projected[name]["header_store_sha256"],
            "configuration store differs from the pinned semantic comparison",
        )
        decoded = ReadUnqliteStore(stored)
        ((key, value),) = decoded.Records
        _, identity = read_config_header(key, value)
        owners = {CMGR_HEADER: archive.require(CMGR_HEADER)}
        manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
        created = DecodeUnqliteClock(decoded.ClockValue)
        recreated = add_config_header_exchange(owners, manager, created, identity)
        require(
            recreated[CONFIG_HEADER_STREAM] == stored, "projected source store differs"
        )
        result[name] = {"source_sha256": pin, "store_sha256": fingerprint(stored)}
    require(len(result) == 12, "configuration store comparison cohort changed")
    return result


def build(request_data, previous):
    require(
        set(request_data) == {"neutral", "create_events"}, "unexpected authoring inputs"
    )
    request, documents, models, properties, application = prepare_package(
        request_data["neutral"]
    )
    events = tuple(
        (datetime.fromisoformat(row["wall_clock"]), UUID(row["record_id"]))
        for row in request_data["create_events"]
    )
    require(
        len(events) == 2
        and len({x for x, _ in events}) == len({x for _, x in events}) == 2,
        "two distinct creation events are required",
    )
    reg = registry()
    for encoding in ("ascii", "utf-8-sig", "latin-1"):
        codecs.lookup(encoding)
    accessed = proof_guard()
    streams, bundle, headers = assemble(
        request, documents, models, properties, application, reg
    )
    state = bundle.StateValue
    index = make_content_index(
        state.RootValue, state.CurrentConfig, headers, bundle.MateValues, reg
    )
    baseline = add_fresh_assembly_auxiliaries(streams | {CONTENT_INDEX: index})
    before = BuildSldprt(baseline, FormatVersion=4)
    require(fingerprint(before) == previous, "previous complete parent changed")
    prior_archive = SldprtArchive.from_bytes(before)
    observed = []
    previous_map = None
    for created, identity in events:
        present = add_config_header_exchange(
            baseline, state.ManagerValue, created, identity
        )
        generated = BuildSldprt(present, FormatVersion=4)
        archive = SldprtArchive.from_bytes(generated)
        require(
            stream_diff(prior_archive, archive) == {CONFIG_HEADER_STREAM},
            "unrelated stream changed",
        )
        raw_store = archive.require(CONFIG_HEADER_STREAM)
        store = ReadUnqliteStore(raw_store)
        ((key, value),) = store.Records
        model, found_identity = read_config_header(key, value)
        require(
            found_identity == identity
            and DecodeUnqliteClock(store.ClockValue) == created
            and model.name == documents[1].configurations[0].name,
            "generated store changed a typed creation event or the active configuration",
        )
        require(
            previous_map in (None, value),
            "creation event changed the configuration model",
        )
        previous_map = value
        observed.append(
            {
                "parent_sha256": fingerprint(generated),
                "parent_bytes": len(generated),
                "store_sha256": fingerprint(raw_store),
                "store_bytes": len(raw_store),
                "map_sha256": fingerprint(value),
                "map_bytes": len(value),
                "prior_parent_streams_unchanged": len(prior_archive.streams),
                "parent_streams": sorted(archive.streams),
                "duplicate_refusal": refuse(
                    lambda: add_config_header_exchange(
                        present, state.ManagerValue, created, identity
                    ),
                    "already has an owner",
                ),
            }
        )
    require(
        observed[0]["parent_sha256"] != observed[1]["parent_sha256"] and not accessed,
        "independent creation events did not reach the output or runtime inputs were accessed",
    )
    return {
        "baseline_parent_sha256": previous,
        "child_sha256": fingerprint(bundle.ChildValue.BytesValue),
        "creation_events": request_data["create_events"],
        "builds": observed,
        "runtime_external_accesses": len(accessed),
    }


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker")
    mode.add_argument("--disclosures", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(build(json.load(sys.stdin), args.worker)))
        return
    require(args.output is not None, "specify the receipt destination")
    pins = {
        PRIOR: PRIOR_PIN,
        SEMANTIC: SEMANTIC_PIN,
        FRAMING: FRAMING_PIN,
        PROOF: PROOF_PIN,
    }
    receipts = {
        name: json.loads(checked(MEASUREMENTS / name, pin))
        for name, pin in pins.items()
    }
    prior = receipts[PRIOR]
    properties = receipts[PROOF]
    sources = compare_sources(
        args.disclosures, properties, receipts[SEMANTIC]["sources"]
    )
    neutral = neutral_request(args.disclosures, properties)
    request = wire(
        {
            "neutral": json.loads(neutral),
            "create_events": [
                {
                    "wall_clock": "2026-11-23T02:28:00",
                    "record_id": "a3c75998-e053-4576-90d9-7e03178febac",
                },
                {
                    "wall_clock": "2026-01-25T15:47:12",
                    "record_id": "6d28f706-2b21-4dd8-bf22-b0aee33dc464",
                },
            ],
        }
    )
    command = (
        sys.executable,
        "-I",
        "-B",
        str(HERE),
        "--worker",
        prior["generated"]["parent_sha256"],
    )
    first, second = (
        subprocess.run(command, input=request, capture_output=True, timeout=120)
        for _ in range(2)
    )
    require(
        first.returncode == second.returncode == 0 and first.stdout == second.stdout,
        (first.stderr + second.stderr).decode()
        or "guarded configuration store builds differ",
    )
    generated = json.loads(first.stdout)
    remaining = set(prior["unrepresented_source_streams"]) - {CONFIG_HEADER_STREAM}
    require(
        generated["child_sha256"] == prior["generated"]["child_sha256"]
        and len(remaining) == 10
        and all(len(row["parent_streams"]) == 33 for row in generated["builds"]),
        "configuration store changed the child or the intended assembly inventory",
    )
    out = wire(
        {
            "schema": "kit.sw2026.d01-config-header-store.v1",
            "base": BASE,
            "pinned_receipts": pins,
            "source_controls": sources,
            "guarded_generated_workers": 2,
            "neutral_request_sha256": fingerprint(neutral),
            "worker_input_sha256": fingerprint(request),
            "generated": generated,
            "unrepresented_source_streams": sorted(remaining),
            "whole_source_admitted": False,
            "native_processes_started": 0,
            "heldout_inputs_read": 0,
            "runner_sha256": fingerprint(HERE.read_bytes()),
            "composer_sha256": fingerprint(
                HERE.with_name("ConfigHeaderExchangeStore.py").read_bytes()
            ),
        }
    )
    with args.output.open("xb") as output:
        output.write(out)


if __name__ == "__main__":
    main()
