from argparse import ArgumentParser
from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))
from MeasuredPlanarPublicationProcess import (
    OPTION, ROOT, audit_io, changed_child, hashed, metrics, require, snapshot,
)

from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from interchange.serialization.Deserialize import FromData

FIXTURES = ROOT / "re/solidworks/measurements/2026/MeasuredPerpendicularPair"
HELDOUT = FIXTURES.parent / "SdkPerpendicularRegistryHeldout01.json"
POSITIVE = ("registry", "adapter")
NEGATIVE = {
    "no-receipt": "offline native measurement receipt",
    "forged-disclosed": "authenticated offline evidence",
    "wrong-body": "exact member",
    "wrong-location": "different native locator",
    "strict-location": "measured location or explicit deferred delivery",
    "foreign-heldout": "one exact held-out bundle",
    "tampered-heldout": "authenticated held-out evidence",
}


def payloads(directory, rows):
    computed = {}
    for row in rows:
        value = metrics((directory / row["name"]).read_bytes())
        require({key: value[key] for key in ("bytes", "sha256")} ==
                {key: row[key] for key in ("bytes", "sha256")}, "delivered member differs from its native authority")
        computed[row["name"]] = value
    return computed


def bind_reader(parent, child, files):
    document = open_document(parent, strict=True)
    graph = document.assembly
    require(graph is not None and len(graph.mates) == 1 and len(graph.mate_groups) == 1
            and len(graph.instances) == 2 and len(graph.mate_entities) == 2
            and len(graph.documents) == 1, "strict cold read lost part or mate ownership")
    (mate,) = graph.mates
    (linked,) = graph.documents
    require(str(mate.kind) == "perpendicular" and str(mate.alignment) == "unknown"
            and len(mate.entity_ids) == 2 and {row.id for row in graph.mate_entities} == set(mate.entity_ids)
            and {row.instance_path for row in graph.mate_entities} == {(row.id,) for row in graph.instances}
            and tuple(row.fixed for row in graph.instances) == (True, False)
            and {value.name for value in linked.document.parameters} == {"D1", "D2"}
            and len(linked.document.parameters) == 3,
            "cold perpendicular read did not preserve modeled planes and child drivers")
    require((document.source.sha256, linked.document.source.sha256)
            == (files[parent.name]["sha256"], files[child.name]["sha256"]),
            "cold read did not resolve the actual newly generated child")
    document.assert_valid()
    return {"mate_kind": str(mate.kind), "mate_endpoints": 2, "child_drivers": 3}


def call(mode, document, parent, options):
    if mode == "adapter":
        return SldprtAdapter().write(document, parent, WriteOptions(values=options))
    return write_document(document, parent, destination_format="solidworks.sldasm",
                          allow_carrier=True, values=options)


def verify(mode, directory):
    measured = json.loads((FIXTURES / "MeasuredOutput.json").read_bytes())["measurement"]
    request = hashed(FIXTURES / "NeutralRequest.json", measured["receipt"]["fixture_sha256"])
    doc = FromData(request["document"])
    doc.assert_valid()
    native = request["native_parent"]
    parent = directory / measured["receipt"]["root"]
    child = directory / measured["receipt"]["members"][0]["name"]
    options = {"allow_carrier": True, "native_destination": native, "defer_native_delivery": True,
               "require_native_transfers": True, OPTION: deepcopy(measured)}
    if mode == "no-receipt":
        del options[OPTION]
    elif mode == "forged-disclosed":
        options[OPTION]["receipt"]["members"][1]["sha256"] = "0" * 64
    elif mode == "wrong-body":
        doc = changed_child(doc, mode)
    elif mode == "wrong-location":
        options["native_destination"] = "C:\\UnmeasuredPerpendicular\\" + parent.name
    elif mode == "strict-location":
        del options["defer_native_delivery"]
    elif mode in ("foreign-heldout", "tampered-heldout"):
        options[OPTION]["receipt"] = json.loads(HELDOUT.read_bytes())
        if mode == "tampered-heldout":
            options[OPTION]["receipt"]["slots"][0]["generated_files"]["parent"]["sha256"] = "0" * 64
    notes = {"passed": True, "mode": mode, "native_processes_started": 0,
             "publications": 0, "refusals": 0, "runtime_input_file_reads": 0}
    with audit_io(parent, child, mode) as guarded:
        try:
            result = call(mode, doc, parent, options)
        except (ValueError, LookupError) as error:
            require(mode in NEGATIVE and NEGATIVE[mode] in str(error), "unexpected refusal: " + str(error))
            notes["refusals"] = 1
        else:
            require(mode in POSITIVE and result.path == parent and not result.vendor_loadable
                    and not result.application_usable
                    and result.metadata["required_native_destination"] == native,
                    "deferred pair reported native acceptance or reached the wrong destination")
            notes["publications"] = 1
    require(not guarded["input_reads"], "writer performed runtime reads")
    if notes["refusals"]:
        require(not snapshot(directory), "refusal changed the caller's directory")
    else:
        require(set(snapshot(directory)) == {parent.name, child.name}, "publication delivered unintended artifacts")
        rows = payloads(directory, measured["receipt"]["members"])
        notes["matching_streams"] = sum(len(row["streams"]) for row in rows.values())
        notes["members"] = {name: {"bytes": row["bytes"], "sha256": row["sha256"]} for name, row in rows.items()}
        notes["readback"] = bind_reader(parent, child, rows)
    return notes


if __name__ == "__main__":
    parser = ArgumentParser(description="Compare the measured perpendicular bundle through public SDK paths")
    parser.add_argument("mode", choices=(*POSITIVE, *NEGATIVE))
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitMeasuredPerpendicular-") as location:
        print(json.dumps(verify(args.mode, Path(location).resolve()), indent=2, sort_keys=True, allow_nan=False))
