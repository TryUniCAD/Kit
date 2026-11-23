from argparse import ArgumentParser
from codecs import lookup
from functools import partial
from hashlib import sha256
from pathlib import Path
from subprocess import run
from uuid import UUID
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.CheckConfigLink import CheckConfigLink
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.Link.ReadModelHead import ReadModelHead
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.Material.BindMatReadMut import BindMatReadMut
from convert.adapters.solidworks.Archive.Config.Members.CheckBlockOwner import CheckBlockOwner
from convert.adapters.solidworks.Archive.Config.ReadCfgBodyMut import ReadCfgBodyMut
from convert.adapters.solidworks.Archive.Config.RequireConfig import RequireConfig
from convert.adapters.solidworks.Archive.Config.WriteCfgBodyMut import WriteCfgBodyMut
from convert.adapters.solidworks.Archive.Header.ReadHeadItems import ReadHeadItems
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadNamedMat import ReadNamedMat

REVISION = "197a3283267e95167ac716efbe57d3449bab1b15"
VERSION = 19000
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
MODEL_LAYOUT = "moModel_c.FUN_4c22ec80"
BLOCK_LAYOUT = "moSketchBlockMgr_c"
NIL_FIELDS = ("f784", "f7a4")
CASES = {
    "assigned": ("named-material/AssignedDensityProbe.SLDPRT", "04ddbe3934185b0c484ca60579312aac6dc0d2412317cda58d8c518f8d214583"),
    "unassigned": ("ladder/L1_boss.SLDPRT", "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def git(*args):
    return run(("git", *args), cwd=ROOT, capture_output=True, check=True).stdout


def context(header, assigned):
    graph = MakeConfigCtx(VERSION, header, None, ReadHeadItems)
    if assigned:
        BindMatReadMut(graph)
    layouts = dict(graph.LayoutsValue)
    for owner, fields, member in ((MODEL_LAYOUT, NIL_FIELDS, "proof.NullMember"), (BLOCK_LAYOUT, ("f380",), "proof.WindowsGuid")):
        target = {rule.NameValue: rule for rule in layouts[owner] if rule.NameValue in fields}
        require(set(target) == set(fields) and all(rule == NativeField("Bytes", name, MaskValue=16) for name, rule in target.items()),
                "SDK fixed field declarations changed")
        layouts[owner] = tuple(NativeField("Embed", rule.NameValue, member) if rule.NameValue in fields else rule
                               for rule in layouts[owner])
    layouts["proof.NullMember"] = tuple(NativeField("Scalar", f"b{i}", "u8") for i in range(16))
    layouts["proof.WindowsGuid"] = (
        NativeField("Scalar", "data1", "u32"),
        NativeField("Scalar", "data2", "u16"),
        NativeField("Scalar", "data3", "u16"),
        *(NativeField("Scalar", f"data4_{i}", "u8") for i in range(8)),
    )
    graph.LayoutsValue = layouts
    return graph


def fixed_fields(root):
    fields = root.FieldsValue
    zeros = {f"b{i}": 0 for i in range(16)}
    require(all(fields[name] == zeros for name in NIL_FIELDS), "model members differ from the proved zero initializer")
    block = ArchiveNode.RequireNode(fields["fe80"])
    require(block.ClassValue == RuntimeClass(BLOCK_LAYOUT, 1), "block identity lacks its actual manager")
    CheckBlockOwner(block)
    numbers = block.FieldsValue["f380"]
    tail = bytes(numbers[f"data4_{i}"] for i in range(8))
    identity = UUID(fields=(numbers["data1"], numbers["data2"], numbers["data3"],
                            tail[0], tail[1], int.from_bytes(tail[2:], "big")))
    require(identity.version == 4, "block manager requires its ordinary Windows UUID4")
    return {"model_zero_members": list(NIL_FIELDS), "block_manager_uuid_version": identity.version,
            "block_manager_uuid_sha256": digest(identity.bytes_le), "block_manager_backlink": True}


def replay_config(archive, assigned):
    header = ReadModelHead(archive, VERSION)
    source = archive.require(CONFIG)
    read = context(header, assigned)
    reader = GraphReader(BinaryReader(source), ArchiveMaps(1), partial(ReadCfgBodyMut, read))
    root = RequireConfig(ReadNodeMut(reader))
    require(root.ClassValue == RuntimeClass("moPart_c", 1) and not reader.Cursor.GetRemaining(), "Config-0 did not exhaust its part root")
    CheckConfigLink(read)
    fields = fixed_fields(root)
    read.UsageValue.IsComplete = True
    write = context(header, assigned)
    write.PartRootValue = root
    writer = BodyWriter(ArchiveMaps(1), write, WriteCfgBodyMut)
    WriteNodeMut(writer, root)
    CheckConfigLink(write)
    write.UsageValue.IsComplete = True
    emitted = bytes(writer.OutputValue)
    snapshot = writer.MapValue.Snapshot()
    require(snapshot == reader.MapValue.Snapshot(), "Config-0 read/write map identity differs")
    report = tuple(GetBodyReport(item.UsageValue) for item in (read, write))
    require(all(not item["native_byte_fields"] for item in report), "Config-0 executed an opaque operation")
    config = ConfigGraph(root, header, snapshot, writer.MapValue.BaseValue, report[1], VERSION, dict(write.FlagsValue))
    return config, fields, summarize(source, emitted, report, snapshot.CounterValue)


def summarize(source, emitted, reports, count):
    require(emitted == source, "complete typed re-emission differs")
    require(all(row["completed"] and not row["missing_schemas"] and not row["provisional_schemas"] for row in reports),
            "a typed stream codec did not exhaust its grammar")
    require(all(field["length_rule"] == "count_times_native_binary64_width"
                and field["element_type"] == "f64" and field["completed"]
                and type(field["element_count"]) is int
                and len(field["typed_values"]) == field["element_count"]
                and field["declared_length"] == field["observed_length"] == 8 * field["element_count"]
                for report in reports for field in report["native_byte_fields"]),
            "resolved stream executed an opaque operation")
    counts = [len(row["native_byte_fields"]) for row in reports]
    require(counts[0] == counts[1], "packed scalar read/write incidence differs")
    return {"bytes": len(source), "sha256": digest(source), "exact": True, "opaque_operations": 0,
            "packed_binary64_fields_per_direction": counts[0], "map_count": count}


def worker(case):
    raw = sys.stdin.buffer.read()
    require(digest(raw) == CASES[case][1], "tracked input differs from its disclosed pin")
    for name in ("ascii", "latin-1", "utf-8", "utf-16", "utf-16-le"):
        lookup(name)
    attempted = []

    def deny(event, _):
        if event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen"} or event.startswith("socket."):
            attempted.append(event)
            raise RuntimeError("archive replay attempted outside input: " + event)

    sys.addaudithook(deny)
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION, "unsupported archive format")
    assigned = case == "assigned"
    config, fields, config_receipt = replay_config(archive, assigned)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), VERSION, ReadMaterial=assigned)
    source = archive.require(RESOLVED)
    decoded = ReadResolvedMut(source, VERSION, config.MapValue, MakeLinkContext(config, manager))
    encoded, result = WriteResolMut(decoded.RootsValue, decoded.ExtraFields, VERSION, config.MapValue, decoded.ContextValue)
    require(decoded.MapValue == result.MapValue and decoded.MapBase == config.MapValue.CounterValue,
            "resolved stream did not retain the recomputed Config-0 map")
    observations = None
    if assigned:
        material = ReadNamedMat(archive)
        observations = {"native_material_id": material.NativeId, "density_kg_m3": material.DensityValue,
                        "atom_id": material.AtomId, "feature_id": material.FeatureId}
        require(tuple(observations.values()) == (258, 2700.0, 101, 34), "assigned material owner changed")
    else:
        try:
            ReadNamedMat(archive)
        except BodyUnsupported as error:
            require("density is absent, overridden or inconsistent" in str(error), "unassigned source failed at another boundary")
        else:
            raise ValueError("unassigned control gained an assignment")
    resolved_receipt = summarize(source, encoded, (decoded.ReportValue, result.ReportValue), result.MapValue.CounterValue)
    require(not attempted, "a subordinate codec caught an outside input failure")
    return {"source_sha256": digest(raw), "streams": {CONFIG: config_receipt, RESOLVED: resolved_receipt},
            "resolved_seed_map": config.MapValue.CounterValue, "fixed_owners": fields, "material": observations,
            "runtime_file_or_process_accesses": 0}


def main():
    require(not git("diff", "--name-only", REVISION, "--", "src"), "SDK closure differs from the exact revision")
    require(not git("ls-files", "--others", "--exclude-standard", "--", "src"), "untracked SDK files change the closure")
    inputs = "re/solidworks/v2026/corpus/"
    cases = {}
    for role, (path, pin) in CASES.items():
        raw = git("show", f"{REVISION}:{inputs}{path}")
        require(digest(raw) == pin, "tracked file custody differs")
        reports = []
        for _ in range(2):
            child = run((sys.executable, "-I", "-B", str(HERE), "--worker", role),
                        input=raw, capture_output=True, timeout=45)
            require(child.returncode == 0 and not child.stderr, child.stderr.decode())
            reports.append(json.loads(child.stdout))
        require(reports[0] == reports[1], "fresh workers disagree")
        cases[role] = {"source_path": inputs + path, **reports[0]}
    return {"schema": "kit.sw2026.assigned-stream-replay.v1", "sdk_revision": REVISION,
            "sdk_src_tree": git("rev-parse", REVISION + ":src").decode().strip(),
            "tool_sha256": digest(HERE.read_bytes()), "fresh_processes": 4,
            "native_processes": 0, "product_writer_outputs": 0, "heldout_inputs": 0, "cases": cases}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=tuple(CASES))
    args = parser.parse_args()
    print(json.dumps(worker(args.worker) if args.worker else main(), indent=2, sort_keys=True))
