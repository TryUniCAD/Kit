from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from subprocess import run
from zlib import ZLIB_RUNTIME_VERSION
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
FIXTURES = ROOT / "re/solidworks/v2026/corpus/saved-sweep/SavedSweepWide01"
MEASURES = ROOT / "re/solidworks/measurements/2026"
MANIFEST = "54461829abdc7501bcb3e5944adf9d569d345471e748c9e93b2ff77ec400cff4"
COLD_PROOF = "a021ac63e9dbbbcb5cdacfaa1c9e6e46339707459a6f0a3f6aaa1d69f13a876b"
PLAIN_SHA = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
RESOLVED = "Contents/Config-0-ResolvedFeatures"

sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]
from AuditSweepArchive import guard_runtime
from ProveSdkSweepPart import BuildSweepPart, SPEC, dimensions, make_intent, validate_spec
from SweepModel import require
from convert.Geometry.Parasolid import EncodePartData
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSavedSw import EncodeSavedSw
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def locked(path, expected):
    payload = path.read_bytes()
    require(sha256(payload).hexdigest() == expected, f"disclosed source changed: {path.name}")
    return payload


def reject(call, diagnostic):
    try:
        call()
    except ValueError as error:
        require(diagnostic in str(error), f"unexpected refusal: {error}")
    else:
        raise ValueError("unqualified graph reached typed emission")
    return diagnostic


def selected_section(graph):
    section, = (
        item.EntryValue.FieldsValue["fc8"]
        for item in graph.MapValue.EntriesValue
        if isinstance(item.EntryValue, ArchiveNode)
        and item.EntryValue.ClassValue.NameValue == "moGeneralCurveRef_w"
        and item.EntryValue.FieldsValue.get("has_fc8") == 1
    )
    return section


def saved_refusals(arguments, section):
    scopes = {
        "ordinary": reject(lambda: WriteResolMut(*arguments), "unsupported SOLIDWORKS body class moSweep_c"),
        "cold": reject(lambda: WriteResolMut(*arguments, WriteSweeps=True), "exclusive ordinary resolved context"),
        "mixed": reject(lambda: WriteResolMut(*arguments, ReplaySavedSweep=True, WriteSweeps=True),
                        "sweep requires its own archive scope"),
        "changed_body_map": reject(lambda: WriteResolMut(
            arguments[0], None, *arguments[2:], ReplaySavedSweep=True), "alternate configuration body mappings"),
    }
    nodes = section["NodesValue"]
    plane = next(item for item in nodes if item.KindValue == 50)
    for label, changed, diagnostic in (
        ("raw_section", b"synthetic opaque input", "requires typed resident cells"),
        ("foreign_resident_link", tuple(
            replace(item, FieldsValue={**item.FieldsValue, "geometric_owner": 2}) if item is plane else item
            for item in nodes), "foreign resident link"),
    ):
        section["NodesValue"] = changed
        try:
            scopes[label] = reject(lambda: WriteResolMut(*arguments, ReplaySavedSweep=True), diagnostic)
        finally:
            section["NodesValue"] = nodes
    return scopes


def compare_replay(archive, kind):
    link = ReadNativeLink(archive, 0, SavedSweep=kind == "saved", ColdSweep=kind == "cold")
    graph = link.ResolvedValue
    arguments = (graph.RootsValue, graph.ExtraFields, graph.VersionValue, link.ConfigValue.MapValue, graph.ContextValue)
    payload, emitted = WriteResolMut(*arguments, ReplaySavedSweep=kind == "saved", WriteSweeps=kind == "cold")
    require(payload == archive.require(RESOLVED), f"{kind} resolved stream differs")
    require(emitted.MapValue == graph.MapValue and emitted.MapBase == graph.MapBase
            and emitted.ReportValue["completed"] and not emitted.ReportValue["missing_schemas"],
            "the inherited map or resolved archive changed")
    report = {
        "resolved_sha256": sha256(payload).hexdigest(), "resolved_bytes": len(payload),
        "map_base": graph.MapBase, "map_final": graph.MapValue.CounterValue, "roots": len(graph.RootsValue),
    }
    if kind == "saved":
        require("Contents/Definition" not in archive.streams and graph.ExtraFields == {"n": 0, "fcd8": []},
                "the scrubbed input must preserve its scope without fabricated streams")
        byte_fields = emitted.ReportValue["native_byte_fields"]
        require(not emitted.ReportValue["field_calls"].get("Bytes") and len(byte_fields) == 2
                and all(row["element_type"] == "f64" and row["element_count"] == 1
                        and row["completed"] for row in byte_fields), "a saved sweep emitted opaque byte fields")
        section = selected_section(graph)
        nodes = section["NodesValue"]
        transmit = EncodeSavedSw(nodes, section["CircleValue"])
        wrapper = EncodePartData(transmit)
        report.update(
            packed_values=[item["typed_values"][0] for item in byte_fields], opaque_byte_fields=0,
            section_nodes=[(item.IndexValue, item.KindValue) for item in nodes],
            section_next_body=nodes[0].Integer("next"), section_transmit_bytes=len(transmit),
            section_wrapper_bytes=len(wrapper), section_wrapper_sha256=sha256(wrapper).hexdigest(),
            refusals=saved_refusals(arguments, section),
        )
    elif kind == "cold":
        require(set(selected_section(graph)) == {"CircleValue"}, "cold section retained saved wire state")
        report["saved_mode_refusal"] = reject(lambda: WriteResolMut(*arguments, ReplaySavedSweep=True),
                                              "alternate configuration body mappings")
    return report


def worker(job, raw):
    blocked = guard_runtime()
    kind = job["kind"]
    if kind == "cold":
        case, density = job["case"], job["density"]
        raw = BuildSweepPart(make_intent(case["name"], *dimensions(case, None), density)).BytesValue
    digest = sha256(raw).hexdigest()
    require(digest == job["sha256"], f"{job['name']} archive changed")
    report = compare_replay(SldprtArchive.from_bytes(raw), kind)
    if kind == "cold":
        require(report["resolved_sha256"] == job["stream_sha256"], "cold resolved bytes changed")
    require(not blocked, "resolved replay attempted external access")
    return {"kind": kind, "archive_sha256": digest, "runtime_reads": len(blocked), **report}


def tasks():
    fixtures = json.loads(locked(FIXTURES / "Fixtures.json", MANIFEST))
    for case in fixtures["cases"].values():
        name, digest = case["file"], case["archive_sha256"]
        yield {"kind": "saved", "name": name, "sha256": digest}, locked(FIXTURES / name, digest)
    density, cold_cases = validate_spec(json.loads(locked(HERE.parent / "DisclosedSweepInputs.json", SPEC)))
    prior = json.loads(locked(MEASURES / "SdkColdSweepPart01.json", COLD_PROOF))
    for case in cold_cases:
        anchor, = (row for row in prior["cases"] if row["state"] == "original" and row["name"] == case["name"])
        yield {"kind": "cold", "name": case["name"], "case": case, "density": density,
               "sha256": anchor["candidate_sha256"], "stream_sha256": anchor["stream_sha256"][RESOLVED]}, b""
    plain = ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"
    yield {"kind": "ordinary", "name": plain.name, "sha256": PLAIN_SHA}, locked(plain, PLAIN_SHA)


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.loads(sys.stdin.buffer.readline()), sys.stdin.buffer.read()), sort_keys=True))
        return
    cases = {}
    for job, raw in tasks():
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                     input=json.dumps(job).encode() + b"\n" + raw, capture_output=True, timeout=45, check=False)
        require(result.returncode == 0 and not result.stderr, result.stderr.decode())
        cases[job["name"]] = json.loads(result.stdout)
    print(json.dumps({"schema": "kit.sw2026.saved-sweep-resolved-replay.v1",
                      "base": "197a3283267e95167ac716efbe57d3449bab1b15",
                      "fixture_manifest_sha256": MANIFEST, "cold_proof_sha256": COLD_PROOF,
                      "zlib": ZLIB_RUNTIME_VERSION, "cases": cases, "fresh_workers": len(cases),
                      "native_processes": 0, "heldout_credit": 0}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
