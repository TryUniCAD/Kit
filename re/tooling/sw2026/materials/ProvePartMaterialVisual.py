from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASE = "d5a72e06a1402d7b9f64c1a4c35f84844f42416b"
ARCHIVE_READ = "c181cc057089eb1dbf6149f12158c5d846ce1c3a"
UPSTREAM_RECEIPTS = {
    "AssignedMaterialArchiveOwners01.json": "0d21e27c454c2b4619c3db3106e2f167d0a28d9eb91e9a1cca90b05d7625ea5c",
    "SdkAssignedMaterialRead01.json": "48d1a287e6137ac69f1156aa6cbba8fca590e114dbc3a9c33e16ac5ed2d9f1d7",
}
DIAGNOSTIC = "a23e44a29967ad84e2716f66363c2898025460bd5a9dddf266e575bdac3a88d2"
DISCLOSED = "cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1"
CONFIG = "Contents/Config-0"
MATERIAL = "uoMaterialProperties.restore"
VISUAL = "moVisualProperties_c"
TEX = "uoMaterialTextureProperties.restore"
PROPERTIES = "moUserProperty_c.restore"
CASENAMES = {"Author": "Original.SLDPRT", "Swap": "Swapped.SLDPRT", "Depth": "DepthEdit.SLDPRT"}
SOURCE_PREFIX = ROOT / "src/convert/adapters/solidworks/Archive"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def disk_input(root, relative, expected):
    target = root / relative
    require(target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root),
            "disclosed path escaped its known location")
    raw = target.read_bytes()
    require(digest(raw) == expected, "disclosed source commitment differs: " + relative)
    return raw


def upstream_receipts():
    result = {}
    for name, sha in UPSTREAM_RECEIPTS.items():
        relative = "re/solidworks/measurements/2026/" + name
        raw = check_output(("git", "-C", str(ROOT), "cat-file", "blob", ARCHIVE_READ + ":" + relative))
        require(digest(raw) == sha, "earlier archive evidence does not match its immutable aggregate receipt")
        result[name] = json.loads(raw)
    return result


def raw_inputs(source, receipts):
    require(source.name == "SdkNamedMaterial01" and not source.is_symlink(), "use the exact disclosed cohort directory")
    source = source.resolve(strict=True)
    cases = receipts["AssignedMaterialArchiveOwners01.json"]["cases"]
    native = json.loads(disk_input(source, "NativeSourcePacket03/Inspection/Result.json", DISCLOSED))
    diagnostic = json.loads(disk_input(source, "NativeDensityProbe01/Native/Result.json", DIAGNOSTIC))
    require(native["passed"] and native["controls_healthy"] and native["distinct_native_processes"] == 10
            and diagnostic["complete_observations"] and diagnostic["controls_healthy"],
            "only the disclosed completed observations qualify")
    for role, owner in cases.items():
        if role == "Control":
            relative = "NativeSourcePacket03/Control.SLDPRT"
        elif role == "Diagnostic":
            relative = "NativeDensityProbe01/Native/AssignedDensityProbe.SLDPRT"
        else:
            relative = "NativeSourcePacket03/Inspection/" + role + "/" + CASENAMES[role.split("/")[1]]
        raw = disk_input(source, relative, owner["file_sha256"])
        require(len(raw) == owner["file_bytes"], "source size differs")
        if role != "Control":
            observed = diagnostic["rows"]["Author"] if role == "Diagnostic" else native["phases"][role]
            label = "saved" if role == "Diagnostic" else "after_save"
            prepared = observed["file"]
            state = observed["states"][label]
            catalog, material, _ = owner["owners"]["active_config_material"].split("|")
            require(prepared["sha256"] == owner["file_sha256"] and prepared["diagnostics"] == [True, 0, 0]
                    and state["part_material"] == {"database": catalog, "material": material},
                    "disclosed native assignment and previous decoder disagree")
        yield role, raw, owner


def alter(archive, path, data):
    return replace(archive, records=tuple(
        replace(record, data=data) if record.name == path else record for record in archive.records
    ))


def refuse(action, expected):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), "unexpected archive refusal: " + str(error))
        return str(error)
    raise ValueError("malformed material prefix was accepted: " + expected)


def contrasts(archive, read, graph, offsets):
    from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
    from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag

    config = archive.Require(CONFIG)
    prefix = graph.StartValue
    visual = graph.VisualValue

    def patch(offset, data):
        return alter(archive, CONFIG, config[:offset] + data + config[offset + len(data):])

    return {
        "wrong_concrete_visual_body": refuse(
            lambda: read(patch(visual.StartOffset, EncodeTag(ArchiveTag("ClassRef", prefix.RootValue.IndexValue - 1)))),
            "unsupported SOLIDWORKS part material visual body owner",
        ),
        "prefix_reuses_part": refuse(
            lambda: read(patch(visual.StartOffset, prefix.RootValue.IndexValue.to_bytes(2, "little"))),
            "requires moVisualProperties_c",
        ),
        "missing_visual_owner": refuse(lambda: read(patch(visual.StartOffset, b"\0\0")), "requires moVisualProperties_c"),
        "unknown_texture_selector": refuse(
            lambda: read(patch(offsets[(MATERIAL, "has80")], (2).to_bytes(4, "little", signed=True))),
            "unsupported SOLIDWORKS part material visual selectors",
        ),
        "unsupported_secondary_texture": refuse(
            lambda: read(patch(offsets[(MATERIAL, "has98")], (1).to_bytes(4, "little", signed=True))),
            "secondary material texture",
        ),
        "unqualified_user_properties": refuse(
            lambda: read(patch(offsets[(PROPERTIES, "n")], (1).to_bytes(4, "little", signed=True))),
            "populated material user properties",
        ),
        "truncated_lightweight_limit": refuse(
            lambda: read(patch(prefix.LightOffset - 4, (graph.NextOffset - prefix.LightOffset - 1).to_bytes(4, "little"))),
            "archive string has no complete length byte",
        ),
        "wrong_format": refuse(lambda: read(replace(archive, format_version=3)), "requires format 4"),
        "missing_physical_model_header": refuse(lambda: read(replace(
            archive, records=tuple(record for record in archive.records if record.name != CONFIG + "-ModelHeader"),
        )), "required stream is missing"),
    }


def worker(run_contrasts):
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
    from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
    from convert.adapters.solidworks.Archive.Bodies.Reading.ReadLengthMut import ReadLengthMut
    from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut
    from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
    from convert.adapters.solidworks.Archive.Config.Material.MatVisualTypes import KMatVisualSchemas
    from convert.adapters.solidworks.Archive.Config.Material.PartVisLayouts import KPartVisLayouts
    from convert.adapters.solidworks.Archive.Config.Material.ReadPartVisual import ReadPartVisual
    from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    raw = sys.stdin.buffer.read()
    for name in ("ascii", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(name)
    denied = []

    def guard(event, _):
        if event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn", "os.fork", "ctypes.dlopen") or event.startswith(("socket.", "subprocess.")):
            denied.append(event)
            raise RuntimeError("part visual boundary attempted runtime input")

    sys.addaudithook(guard)
    archive = SldprtArchive.FromBytes(raw)
    offsets = {}

    def observe(frame, event, _):
        if event == "call" and frame.f_code in (ReadLengthMut.__code__, ReadValueMut.__code__):
            args = frame.f_locals
            state = args["FrameValue"]
            key = (state.ContextValue.UsageValue.SchemaPath[-1], args["RuleValue"].NameValue)
            offsets[key] = state.ReaderValue.Cursor.GetOffset()

    previous = sys.getprofile()
    if run_contrasts:
        sys.setprofile(observe)
    try:
        graph = ReadPartVisual(archive)
    finally:
        sys.setprofile(previous)
    root = graph.StartValue.RootValue
    seed = graph.StartValue.MapValue
    visual = graph.VisualValue
    config = archive.Require(CONFIG)
    originals = {entry.IndexValue: entry.EntryValue for entry in seed.EntriesValue}
    shared = {entry.IndexValue: entry.EntryValue for entry in graph.MapValue.EntriesValue}
    require(all(shared[slot] is item for slot, item in originals.items())
            and graph.NextOffset == visual.EndOffset and root.FieldsValue["f78"] is visual
            and shared[visual.IndexValue] is visual,
            "part visual lost the physical node or shared header map identity")
    before = graph.StartValue.LightOffset
    exact = config[before:graph.NextOffset]
    context = BodyContext(19000, KPartVisLayouts, {}, KMatVisualSchemas)
    writer = BodyWriter(ArchiveMaps(seed.CounterValue, seed), context, WriteBodyMut, NestingDepth=1)
    WriteBodyMut(writer, root)
    require(bytes(writer.OutputValue) == exact and writer.MapValue.CounterValue == graph.MapValue.CounterValue,
            "typed replay did not preserve every byte from the actual section start through the visual")
    fields = visual.FieldsValue
    select = fields["f20"]
    identity = select["f20"]
    if isinstance(identity, tuple):
        require(identity[0] == "A", "unknown identity CString mode")
        identity = identity[1]
    records = contrasts(archive, ReadPartVisual, graph, offsets) if run_contrasts else {}
    require(not denied and not graph.ReportValue["missing_schemas"] and not graph.ReportValue["provisional_schemas"]
            and not graph.ReportValue["native_byte_fields"],
            "part visual used external inputs or provisional/opaque fields")
    return {
        "file_sha256": digest(raw), "config_sha256": digest(config),
        "visual_span": [VISUAL, visual.IndexValue, visual.StartOffset, graph.NextOffset],
        "prefix_span": [before, graph.NextOffset], "prefix_sha256": digest(exact),
        "prefix_map": {"entry_counter": seed.CounterValue, "end_counter": graph.MapValue.CounterValue},
        "identity": identity, "selector": [select[name] for name in ("f70", "has80", "has90", "has98")] + [fields["has88"]],
        "texture_calls": graph.ReportValue["schema_calls"].get(TEX, 0), "exact_typed_replay": True,
        "refusals": records, "runtime_input_or_process_accesses": len(denied),
    }


def measure(source):
    records = upstream_receipts()
    earlier = records["SdkAssignedMaterialRead01.json"]["cases"]
    output = {}
    for role, raw, prior in raw_inputs(source, records):
        flags = ["--contrasts"] if role == "D01Corner/Author" else []
        process = run((sys.executable, "-I", "-B", str(HERE), "--worker", *flags), input=raw,
                      capture_output=True, timeout=50, check=False)
        require(process.returncode == 0 and not process.stderr, process.stderr.decode())
        row = json.loads(process.stdout)
        require(row["file_sha256"] == prior["file_sha256"] and row["config_sha256"] == prior["streams"][CONFIG]["sha256"]
                and row["identity"] == prior["owners"]["active_config_material"],
                "physical visual record differs from independently bound CMgr/part observations")
        if role != "Control":
            require(row["visual_span"] == earlier[role]["graph"]["nodes"]["part_visual"]
                    and row["texture_calls"] == earlier[role]["part_texture_visits"],
                    "main-compatible parse changed original ownership or branch extent")
        else:
            require(row["selector"] == [1, 0, 1, 0, 1] and row["texture_calls"] == 0
                    and prior["owners"]["active_config_density"] == -1.0,
                    "unassigned control differs from the stored label contrast")
        row["identity_sha256"] = digest(row.pop("identity").encode())
        output[role] = row
    modules = (*sorted((SOURCE_PREFIX / "Bodies/Layouts/Config/Visual").glob("*.py")),
               *(SOURCE_PREFIX / "Config/Material" / f"{name}.py" for name in (
                   "CfgVisualGraph", "CheckMatVisual", "MatVisualTypes", "PartVisLayouts", "ReadPartVisual",
                   "ReadVisBodyMut",
               )), HERE)
    return {"schema": "kit.sw2026.part-material-visual-prefix.v1", "base_commit": BASE,
            "native_build": "34.5.2.0604", "aggregate_read_commit": ARCHIVE_READ,
            "prior_receipt_sha256": UPSTREAM_RECEIPTS, "source_sha256": {
                path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in modules
            }, "cases": output, "fresh_guarded_processes": len(output), "assigned_visual_records": len(output) - 1,
            "native_processes": 0, "whole_config_admitted": False, "material_assignment_admitted": False,
            "public_writer_qualified": False, "heldout_credit": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--contrasts", action="store_true")
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(worker(args.contrasts)))
    else:
        if args.source is None or args.output is None:
            parser.error("--source and --output are required")
        receipt = measure(args.source)
        with args.output.open("xb") as output:
            output.write(encode(receipt))
