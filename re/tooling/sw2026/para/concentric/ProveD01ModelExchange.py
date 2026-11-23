from argparse import ArgumentParser
import codecs
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(REPO / "re/solidworks/WriterResearch")]

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
from AssemblyModelExchange import (
    ModelExchangeIds,
    add_model_exchange,
    model_owners,
    model_records,
    standard_records,
)
from ConcentricMateCell import concentric_mate_cell
from ConfigHeaderExchangeModel import (
    CONFIG_HEADER_STREAM,
    MODEL_EXCHANGE_STREAM,
    read_config_header,
    read_model_exchange_link,
)
from ConfigHeaderExchangeStore import add_config_header_exchange
from ExchangeMessagePack import read_exchange_map
from FreshAssemblyAuxiliaries import add_fresh_assembly_auxiliaries
from InspectPartEnvironmentSource import Image
from PrepareGeneratedConcentric import windows_path
from ProveConfigHeaderExchange import source_cases
from ProveConcentricCmgrHistory import disclosed_cases, refuse
from ProveFreshAssemblyAuxiliaries import neutral_request

from convert.adapters.solidworks.Archive.Exchange.ReadUnqlite import ReadUnqlite
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

BASE = "2acb0d00e36e584e16cdcf1bfc6f7c1bc1a11ee0"
PRIOR = "D01ConfigHeaderStore01.json"
PRIOR_PIN = "f4697b987acbc0d375c8ec4b874abd31453fc24b25f7a4c8c02b67ea893ac003"
MATE_SOURCES = "ConcentricMateSourceArchive01.json"
MATE_SOURCES_PIN = "3c67d10789bbd681bfb99da712e1c6a035d78713b326c3048373ed4972198997"
NAME_SOURCE = "ComponentInstanceNameWire01.json"
NAME_SOURCE_PIN = "3639fb9d7fd6c40e10782b8b43ce000a63269adcdcd8230ef911d24c38fe8d39"
MODEL_MODULE_PIN = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
NATIVE_WINDOWS = {
    "feature_visibility_dispatch": (
        0x4BB5369E,
        0x4BB536B0,
        "06bea04373c3e62eaff64fa047420a9c4ae0ee8327f24522a944b7b647f6ba23",
    ),
    "feature_visibility_key": (
        0x4BB536E4,
        0x4BB53702,
        "f93e777647f128a00411715016dc26b09613efe34c16753cf0bd6396f61e92d4",
    ),
    "datum_geometry_visibility": (
        0x4C2CECA0,
        0x4C2CED7C,
        "5556ebc8ab243185f075389c49dbb2b5558bfbd58afed975e448ae5b167efdf8",
    ),
    "datum_visibility_slot": (
        0x4D170B48,
        0x4D170B50,
        "4988c36e0f72c249fb7436568925268ecfcf8fbd60eeb6cbd812c03a9acbd453",
    ),
}


def native_visibility(path):
    image = Image(path, MODEL_MODULE_PIN)
    require(
        image.read(0x4CDE00F4, 0x4CDE00FB) == b"hidden\0",
        "native feature visibility key changed",
    )
    windows = {}
    for name, (start, end, pin) in NATIVE_WINDOWS.items():
        require(
            fingerprint(image.read(start, end)) == pin,
            "native datum visibility rule changed",
        )
        windows[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": pin}
    return {"module_sha256": MODEL_MODULE_PIN, "matched_windows": windows}


def observed_ids(records):
    keys = tuple(UUID(key.decode("ascii")) for key, _ in records if key != b"TOC")
    manager, selection, *planes, mates, document = keys
    model = read_exchange_map(dict(records)[b"TOC"]).field("model")
    folder_group, mate_group, plane_group = model.values("object")
    require(
        folder_group.field("class") == "moSelectionSetFolder_c"
        and mate_group.field("class") == "moMateGroup_c"
        and plane_group.field("class") == "moRefPlane_c",
        "source exchange TOC ownership changed",
    )
    order = tuple(
        planes.index(UUID(row.field("guid"))) for row in plane_group.values("object")
    )
    return ModelExchangeIds(manager, selection, tuple(planes), mates, document, order)


def compare_sources(location, properties, corpus, rename):
    cases = {row["id"]: row for row in disclosed_cases()}
    result = {}
    for label, path, pin in source_cases(location, properties):
        archive = SldprtArchive.from_bytes(checked(path, pin))
        records = ReadUnqlite(archive.require(MODEL_EXCHANGE_STREAM)).Records
        ids = observed_ids(records)
        owners = model_owners(archive)
        root, _, _, _, mates = owners
        source = dict(records)
        known = standard_records(owners, ids)
        require(
            all(source[key] == value for key, value in known),
            "ordinary system exchange records differ",
        )
        paired = None
        if "/" in label:
            case, phase = label.split("/")
            pins = corpus["cases"][case]["native_artifact_digests"][phase.lower()]
            name = cases[case]["child_name"] + ".SLDPRT"
            paired = pins, name, path.parents[2] / "Working" / name
        elif label == "renamed_native":
            name = "IndependentNameCylinder.SLDPRT"
            paired = (
                rename["native"]["synchronized_saved_pair"],
                name,
                path.parents[2] / "Owned" / "Working" / name,
            )
        mate_pin = None
        if paired is not None:
            pins, name, prior_location = paired
            require(pins["parent"]["sha256"] == pin, "mate source parent changed")
            mate_pin = pins["child"]["sha256"]
            child = checked(path.with_name(name), mate_pin)
            projected = tuple(
                concentric_mate_cell(
                    root,
                    mate,
                    child,
                    historical_keeper_locator=windows_path(prior_location),
                )
                for mate in mates
            )
            require(
                model_records(owners, ids, projected) == records,
                "same-child concentric model exchange differs",
            )
        elif not mates:
            require(
                model_records(owners, ids, ()) == records,
                "empty mate model exchange differs",
            )
        packed = not mates or mate_pin is not None
        result[label] = {
            "parent_sha256": pin,
            "child_sha256": mate_pin,
            "matching_records": 8 if packed else len(known),
            "actual_mates": len(mates),
            "exact_live_store": packed,
            "toc_plane_order": ids.plane_order,
        }
    require(
        len(result) == 12
        and sum(row["exact_live_store"] for row in result.values()) == 11,
        "the complete scoped native model exchange comparison changed",
    )
    return result


def next_ids(request, created, config_id):
    event = wire(
        {
            "document": request,
            "clock": created.isoformat(),
            "scope": "assembly-model-exchange",
        }
    )
    roles = ("manager", "selection", "front", "top", "right", "mates", "document")
    identities = tuple(
        UUID(
            bytes=sha256(role.encode("ascii") + b"\0" + event).digest()[:16], version=4
        )
        for role in roles
    )
    require(
        config_id not in identities,
        "model exchange shares a configuration header identity",
    )
    manager, selection, *planes, mates, document = identities
    return ModelExchangeIds(manager, selection, tuple(planes), mates, document)


def generate(inputs, expected):
    require(
        set(inputs) == {"neutral", "header_event", "model_clock"},
        "unexpected model exchange inputs",
    )
    request, documents, models, properties, application = prepare_package(
        inputs["neutral"]
    )
    header_event = inputs["header_event"]
    config_id = UUID(header_event["record_id"])
    config_clock = datetime.fromisoformat(header_event["wall_clock"])
    model_clock = datetime.fromisoformat(inputs["model_clock"])
    ids = next_ids(inputs["neutral"], model_clock, config_id)
    for encoding in ("ascii", "utf-8-sig", "latin-1"):
        codecs.lookup(encoding)
    reg = registry()
    accessed = proof_guard()
    streams, bundle, headers = assemble(
        request, documents, models, properties, application, reg
    )
    state = bundle.StateValue
    index = make_content_index(
        state.RootValue, state.CurrentConfig, headers, bundle.MateValues, reg
    )
    base = add_fresh_assembly_auxiliaries(streams | {CONTENT_INDEX: index})
    baseline = add_config_header_exchange(
        base, state.ManagerValue, config_clock, config_id
    )
    prior = BuildSldprt(baseline, FormatVersion=4)
    require(
        fingerprint(prior) == expected, "complete previous configuration parent changed"
    )
    before = SldprtArchive.from_bytes(prior)
    owners = model_owners(before)
    root, _, manager, _, mates = owners
    child = bundle.ChildValue.BytesValue
    projected = tuple(concentric_mate_cell(root, mate, child) for mate in mates)
    present = add_model_exchange(baseline, owners, ids, model_clock, projected)
    output = BuildSldprt(present, FormatVersion=4)
    after = SldprtArchive.from_bytes(output)
    require(
        stream_diff(before, after) == {MODEL_EXCHANGE_STREAM},
        "model exchange changed prior streams",
    )
    raw_store = after.require(MODEL_EXCHANGE_STREAM)
    data = ReadUnqlite(raw_store)
    (header_cell,) = ReadUnqlite(after.require(CONFIG_HEADER_STREAM)).Records
    config, found = read_config_header(*header_cell)
    require(
        found == config_id
        and read_model_exchange_link(data.Records, manager, config)
        == (ids.manager, ()),
        "constructed exchange databases disagree on their active configuration",
    )
    require(
        data.Records == model_records(owners, ids, projected),
        "model exchange readback changes records",
    )
    refusal = refuse(
        lambda: add_model_exchange(present, owners, ids, model_clock, projected),
        "already has an owner",
    )
    require(
        not accessed and len(data.Records) == 8 and len(after.streams) == 34,
        "model exchange scope changed",
    )
    return {
        "prior_parent_sha256": expected,
        "parent_sha256": fingerprint(output),
        "parent_bytes": len(output),
        "child_sha256": fingerprint(child),
        "store_sha256": fingerprint(raw_store),
        "store_bytes": len(raw_store),
        "live_record_sizes": [len(value) for _, value in data.Records],
        "unchanged_parent_streams": len(before.streams),
        "parent_streams": sorted(after.streams),
        "runtime_external_accesses": len(accessed),
        "duplicate_refusal": refusal,
    }


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker")
    mode.add_argument("--disclosures", type=Path)
    parser.add_argument("--model-module", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(generate(json.load(sys.stdin), args.worker)))
        return
    require(
        args.output is not None and args.model_module is not None,
        "supply the native model module and receipt destination",
    )
    pins = {
        PRIOR: PRIOR_PIN,
        PROOF: PROOF_PIN,
        MATE_SOURCES: MATE_SOURCES_PIN,
        NAME_SOURCE: NAME_SOURCE_PIN,
    }
    receipts = {
        name: json.loads(checked(MEASUREMENTS / name, pin))
        for name, pin in pins.items()
    }
    prior = receipts[PRIOR]
    properties = receipts[PROOF]
    sources = compare_sources(
        args.disclosures, properties, receipts[MATE_SOURCES], receipts[NAME_SOURCE]
    )
    visibility = native_visibility(args.model_module)
    neutral = neutral_request(args.disclosures, properties)
    request = wire(
        {
            "neutral": json.loads(neutral),
            "header_event": prior["generated"]["creation_events"][0],
            "model_clock": "2026-11-23T02:28:02",
        }
    )
    command = (
        sys.executable,
        "-I",
        "-B",
        str(HERE),
        "--worker",
        prior["generated"]["builds"][0]["parent_sha256"],
    )
    one, two = (
        subprocess.run(command, input=request, capture_output=True, timeout=120)
        for _ in range(2)
    )
    require(
        one.returncode == two.returncode == 0 and one.stdout == two.stdout,
        (one.stderr + two.stderr).decode() or "guarded model exchange builds differ",
    )
    result = json.loads(one.stdout)
    require(
        result["child_sha256"] == prior["generated"]["child_sha256"],
        "linked child changed",
    )
    remaining = set(prior["unrepresented_source_streams"]) - {MODEL_EXCHANGE_STREAM}
    tools = (
        HERE,
        HERE.with_name("AssemblyModelExchange.py"),
        HERE.with_name("ConcentricMateCell.py"),
        HERE.with_name("ExchangeMateEndpoints.py"),
        REPO / "re/solidworks/WriterResearch/PartObjectExchange.py",
    )
    report = wire(
        {
            "schema": "kit.sw2026.d01-model-exchange.v1",
            "base": BASE,
            "pinned_receipts": pins,
            "native_visibility": visibility,
            "source_controls": sources,
            "guarded_generated_workers": 2,
            "neutral_request_sha256": fingerprint(neutral),
            "worker_input_sha256": fingerprint(request),
            "generated": result,
            "whole_source_admitted": False,
            "unrepresented_source_streams": sorted(remaining),
            "native_processes_started": 0,
            "heldout_inputs_read": 0,
            "tool_sha256": {
                path.name: fingerprint(path.read_bytes()) for path in tools
            },
        }
    )
    with args.output.open("xb") as output:
        output.write(report)


if __name__ == "__main__":
    main()
