from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from AuditColdSweep import EPOCH
from AuditSweepSketches import map_shape
from ProveSdkSweepPart import guard_runtime
from ProveSweepDocument import neutral_document
from SweepModel import dimensions, require, validate_spec
from convert import write_document
from convert.Geometry.Parasolid import EncodePartData
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSweepXmt import EncodeSweepXmt
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwFrame import ReadSwFrame
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KGhostPartition
from convert.adapters.solidworks.Core.Preparation.Sweeps.PrepSweepPart import PrepSweepPart
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import ReadSwGraph
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.serialization.JsonCodec import DumpJson, LoadJson


RECEIPT = ROOT / "re/solidworks/measurements/2026/OrdinarySweepColdNativeHeldout01.json"
RECEIPT_SHA = "d8d698670b21f432e0b6fc98a541d96acf706d9037ad871ec6251fe4be851f70"
FORMAT = "solidworks.sldprt"
MEASURE = "solidworks_native_measurement"
SLOTS = ("Slot01", "Slot02")


def checked(path, expected):
    require(path.resolve(strict=True) == path and not path.is_symlink(), "sweep input locator is indirect")
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, "sweep evidence fingerprint differs")
    return data


def inputs(root, slot):
    require(sys.platform == "win32" and root.is_absolute() and root.drive.casefold() == "c:"
            and root.resolve(strict=True) == root, "private sweep custody requires its original guest path")
    raw = checked(RECEIPT, RECEIPT_SHA)
    report = json.loads(raw)
    packet = root / "Packet"
    job = json.loads(checked(packet / "SweepJob.json", report["job_sha256"]))
    generation_raw = checked(root / "Generated" / "Generation.json", report["generation_sha256"])
    generation = json.loads(generation_raw)
    require(report["native_passed"] is True and report["blocked_writer_reads"] == 0
            and job["guest_packet"] == str(packet) and job["cohort"] == "heldout"
            and all(job[key] == report[key] for key in ("method_sha256", "prewriter_lock_sha256", "source_lock_sha256", "generation_sha256"))
            and all(generation[key] == report[key] for key in ("method_sha256", "sdk_tree", "writer_revision", "prewriter_lock_sha256"))
            and generation["native_processes_started"] == 0, "previous native lifecycle and source freeze do not join")
    spec = json.loads(checked(packet / "Spec.json", job["spec_sha256"]))
    density, cases = validate_spec(spec)
    index = SLOTS.index(slot)
    case, measured, proof = cases[index], report["cases"][index], generation["candidates"][index]
    expected = measured["candidate_sha256"]["original"]
    relative = f"Candidates/{slot}.SLDPRT"
    locator = str(packet / relative)
    require(case["name"] == measured["slot"] == proof["slot"] == slot and measured["passed"] is True
            and expected == proof["candidate_sha256"] == job["files"][relative]["sha256"]
            and proof["blocked_runtime_calls"] == 0 and job["candidates"][relative] == locator,
            "generated sweep candidate does not join the original model freeze")
    return case, density, locator, expected, raw.decode("utf-8")


def registry(document, sink, values):
    return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=values)


def direct(document, sink, values):
    return SldprtWriter().write(document, sink, WriteOptions(values=values))


def adapter(document, sink, values):
    return SldprtAdapter().write(document, sink, WriteOptions(values=values))


def authored_model(name, radii, density):
    document = neutral_document(name, *radii, density)
    return replace(document, metadata={"name": name, "solidworks_platform_view_math": True})


def inspect_part(part, radii):
    archive = SldprtArchive.from_bytes(part.BytesValue)
    require(archive.streams == part.StreamsValue and len(archive.streams) == 11,
            "sweep container or logical streams differ")
    graph = ReadSwGraph(archive, ColdSweep=True)
    require((graph.SectionValue.DriverValue.MetresValue / 2, graph.PathValue.DriverValue.MetresValue) == radii,
            "the cold sweep lost its actual editable drivers")
    link = graph.LinkValue
    config = link.ConfigValue
    resolved = link.ResolvedValue
    config_bytes, cfg = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    resolved_bytes, same = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, 19000, cfg.MapValue, resolved.ContextValue, WriteSweeps=True
    )
    require(config_bytes == archive.require(link.ConfigName) and resolved_bytes == archive.require(link.StreamName)
            and same.MapValue == resolved.MapValue and cfg.MapValue == config.MapValue
            and map_shape(resolved.MapValue) == map_shape(part.ResolvedValue.MapValue)
            and map_shape(config.MapValue) == map_shape(part.ConfigValue.MapValue),
            "sweep archive or object map does not replay exactly")
    ghost = archive.require(KGhostPartition)
    nodes = ReadActiveNodes(ReadSwFrame(ghost))
    require(EncodePartData(EncodeSweepXmt(tuple(nodes.values()), True)) == ghost,
            "sweep ghost partition does not replay exactly")
    return (link.ConfigName, link.StreamName, KGhostPartition)


def verify_public(document, restored, part, locator, receipt, case, density):
    options = {"final_destination": locator, MEASURE: {"written_at": EPOCH, "receipt": {"native_report": receipt}}}
    changed_model = authored_model(case["name"], dimensions(case, "section"), density)
    target = Path(locator)
    variants = (
        (changed_model, options),
        (document, {"final_destination": locator}),
        (document, {**options, "final_destination": str(target.parent / "Unmeasured" / target.name)}),
        (document, {**options, MEASURE: {"written_at": EPOCH + 1, "receipt": {"native_report": receipt}}}),
        (document, {**options, MEASURE: {"written_at": EPOCH, "receipt": {"native_report": receipt + " "}}}),
    )
    routes = {}
    for write in (registry, direct, adapter):
        for model in (document, restored):
            output = BytesIO()
            evidence = write(model, output, options)
            require(output.getvalue() == part.BytesValue and evidence.vendor_loadable and evidence.application_usable
                    and evidence.metadata[MEASURE]["generated_sha256"] == sha256(part.BytesValue).hexdigest(),
                    "public sweep publication differs from the native-tested artifact")
        for invalid, configuration in variants:
            sink = BytesIO()
            try:
                write(invalid, sink, configuration)
            except ValueError:
                require(sink.tell() == 0 and not sink.getvalue(), "refused sweep changed the destination")
            else:
                raise ValueError("unmeasured sweep was published")
        routes[write.__name__] = {"whole_archives": 2, "refusals": len(variants)}
    return routes


def replay(root, slot, publish):
    case, density, locator, expected, receipt = inputs(root, slot)
    radii = dimensions(case)
    document = authored_model(slot, radii, density)
    document.assert_valid()
    restored = LoadJson(DumpJson(document))
    require(restored == document, "neutral sweep changed during JSON round trip")
    blocked = guard_runtime()
    settings = WriteOptions(values={"final_destination": locator})
    result = PrepSweepPart(document, BytesIO(), EPOCH, settings)
    repeated = PrepSweepPart(restored, BytesIO(), EPOCH, settings)
    require(result.BytesValue == repeated.BytesValue, "repeated model-only sweep differs")
    actual = sha256(result.BytesValue).hexdigest()
    exact_streams = inspect_part(result, radii)
    require(not blocked, "model-only sweep accessed an external runtime source")
    routes = verify_public(document, restored, result, locator, receipt, case, density) if publish and actual == expected else {}
    require(not blocked, "public sweep writer accessed an external runtime source")
    return {
        "slot": slot, "expected_sha256": expected, "generated_sha256": actual, "passed": actual == expected,
        "stream_count": len(result.StreamsValue), "typed_stream_replays": exact_streams,
        "normal_publication": routes, "runtime_input_reads": len(blocked),
        "native_processes_started": 0, "native_source_files_opened": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--slot", required=True, choices=SLOTS)
    parser.add_argument("--publication", action="store_true")
    args = parser.parse_args()
    try:
        report = replay(args.root, args.slot, args.publication)
    except Exception as exc:
        raise SystemExit(f"sweep proof refused ({type(exc).__name__})") from None
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    raise SystemExit(0 if report["passed"] else 2)
