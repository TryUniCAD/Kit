from argparse import ArgumentParser
import codecs
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from struct import pack, pack_into
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASE = "794d0cb03a8dae8ad7af9fb8d397fc9114b9b267"
EVIDENCE = "ed0a90a0e8e913b4eb28f9c2dc6c92a814e32472"
INVENTORY = "re/solidworks/measurements/2026/SdkModelDefinitionCorpus01.json"
SOURCE = "7d9e15658f5e2d19db2d2f6afe5a995c26ebc54a"
EXPECTED_INVENTORY = "29c46bb51ff0ff883c939b9dfd10bf0ebdf83f17bca962557b9260516c7e0c21"
FRESH_DIGESTS = (
    "f18c7717493aad07d75f0d547fdfde5825fa980bd2d8a0673c5602ce6450877e",
    "233842a961645bd80f40e7754d7a1dcebc9ce2df1be203a135869573353646ac",
)
DEFINITION_PACKAGE = "src/convert/adapters/solidworks/Archive/Definition"
OWNED_MODULES = (
    "CheckAsmDef", "CheckDefRender", "CheckDefScope",
    "Construction/MakeAssemblyDef", "Construction/MakeSavePartSettings",
    "Construction/ReadSavePartValue", "Construction/SavePartSlots",
    "Fields/AsmDefLayouts", "Fields/AssemblyDefTail",
    "ModelDefClsid", "ModelDefContext", "ReadModelDef", "WriteModelDef",
)
RENDER_SAVED = {"f08": 1, "f0c": 0, "list": {"n": 0, "items": []}}
RENDER_FRAME = pack("<BiiH", 1, 1, 0, 0)
RENDER_OFFSET = 288
RENDER_DIGEST = "1f4252804c2bc9ea883ac3ee164df22aaece74b30a3a9be2c2998fd769bfb417"
REFERENCE_FILES = {
    "re/tooling/sw2026/serial/defs/Definition.py": "04dfa56204c742603a8a832ffd5146678d39cd12b6ffa6518137d2b4756a6702",
    "re/tooling/sw2026/builders/Definition.py": "b7fd7a3b226493623059a6cde7d5e464ae3e3ee8accd8101c7104be3bdec8a45",
}
PREF_SAVED = {
    "f08": 0, "f0c": 0, "f10": 0.75, "f18": 0, "f20": 0.000125,
    "f28": 0, "f30": 1, "f34": 1, "f2c": 1, "f38": 1, "f3c": 0,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def input_job(case):
    index = case + 2
    standard, journal = (("moDIN_c", "Assembly δ"), ("moGB_c", "上部 journal"))[case]
    return {
        "standard": standard,
        "bits": [index, 30 + index, 47, 63],
        "tessellation": [13 + index, 32 - index, 47 * index, bool(index % 2)],
        "journal": journal,
        "compression": bool(index % 2),
        "preferences": {
            "5fc": True, "5fd": (-0.4, 1.7)[case], "5fe": False, "5ff": 1.25,
            "600": True, "601": False, "602": True, "603": False, "604": True,
            "605": -9 - index,
        },
    }


def emitted(job):
    settings = ModelDefInput(
        job["standard"], tuple(job["bits"]), tuple(job["tessellation"]),
        job["compression"], job["journal"], 19000,
    )
    graph = MakeAssemblyDef(settings, job["preferences"])
    wire = WriteModelDef(graph, Assembly=True)
    require(wire.UsageValue.IsComplete, "assembly Definition construction did not complete")
    return wire.OutputValue


def map_shape(snapshot):
    result = []
    for slot in snapshot.EntriesValue:
        owner = slot.EntryValue
        descriptor = owner.ClassValue if isinstance(owner, ArchiveNode) else owner
        result.append([slot.IndexValue, type(owner).__name__, descriptor.NameValue, descriptor.SchemaValue])
    return sorted(result)


def readback(wire):
    read = ReadModelDef(wire, 19000, Assembly=True)
    write = WriteModelDef(read.GraphValue, Assembly=True)
    require(read.UsageValue.IsComplete and write.UsageValue.IsComplete, "typed Definition fields are incomplete")
    require(write.OutputValue == wire, "typed assembly Definition did not replay exactly")
    map_state = map_shape(read.MapValue)
    require(
        read.MapValue.CounterValue == write.MapValue.CounterValue
        and map_state == map_shape(write.MapValue)
        and (not map_state or map_state[0][0] == 1),
        "assembly Definition map counts or owners changed",
    )
    doc = read.GraphValue.DocumentValue
    fields = doc.FieldsValue
    journal = fields["ffd8"]["f18"]
    return {
        "sha256": sha256(wire).hexdigest(), "bytes": len(wire),
        "root": [doc.ClassValue.NameValue, doc.ClassValue.SchemaValue],
        "next_map_index": read.MapValue.CounterValue, "map": map_state,
        "renderer": fields.get("f1110"),
        "preferences": fields["f1b48"],
        "assembly_tail": {name: fields[name] for name in (
            "f1840", "f19c8", "f1a38", "f1a40", "f1a48", "f19b0", "f19b8", "f19c0", "f1afc",
        )},
        "journal": [journal.ClassValue.SchemaValue, journal.FieldsValue["f08"]],
        "standard": fields["fba8"].ClassValue.NameValue,
        "display_words": [fields["fad8_0"], fields["fad8_1"]],
        "tessellation": [fields[name] for name in ("fa58", "fa5c", "fa60", "fa64")],
        "compression": fields["fa90"],
        "style_count": len(fields["f878"]["styles"]),
        "font_count": len(fields["f870"].FieldsValue["f10"]),
        "view_environment_count": len(fields["faf8"]),
    }


def native_readback(raw):
    archive = SldprtArchive.FromBytes(raw)
    require(
        archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
        "expected a disclosed archive-version-19000 assembly",
    )
    return {"file_sha256": sha256(raw).hexdigest(), **readback(archive.require("Contents/Definition"))}


def reject(function, expected):
    try:
        function()
    except (ValueError, TypeError) as error:
        require(expected in str(error), f"unexpected refusal: {error}")
        return str(error)
    raise ValueError(f"unsupported assembly Definition accepted: {expected}")


def reject_cases(wire):
    part = MakePartDef(ModelDefInput("moANSI_c", (), (26, 4, 25, True), False, "Part", 19000), 1000.0)
    part_wire = WriteModelDef(part).OutputValue
    assembly = ReadModelDef(wire, 19000, Assembly=True).GraphValue
    option_start = len(wire) - 56
    invalid_bit = bytearray(wire)
    pack_into("<i", invalid_bit, option_start + 4, 2)
    invalid_fraction = bytearray(wire)
    pack_into("<d", invalid_fraction, option_start + 8, 1.0)
    invalid_null = wire[:36] + b"\xff\x7f\x00\x00\x00\x00" + wire[38:]
    require(wire[36:38] == b"\x00\x00", "generated first tag is not the proved null")

    def bad_input(slot, value):
        job = input_job(0)
        job["preferences"][slot] = value
        return emitted(job)

    def missing_slot():
        job = input_job(0)
        del job["preferences"]["5fc"]
        return emitted(job)

    return {
        "part_mode_read": reject(lambda: ReadModelDef(wire, 19000), "ordinary part CLSID"),
        "part_mode_write": reject(lambda: WriteModelDef(assembly), "uiPartDoc_c schema 1"),
        "assembly_mode_read": reject(lambda: ReadModelDef(part_wire, 19000, Assembly=True), "ordinary assembly CLSID"),
        "assembly_mode_write": reject(lambda: WriteModelDef(part, Assembly=True), "uiAssemblyDoc_c schema 1"),
        "version": reject(lambda: ReadModelDef(wire, 18900, Assembly=True), "archive version 19000"),
        "truncated_tail": reject(lambda: ReadModelDef(wire[:-1], 19000, Assembly=True), "truncated SOLIDWORKS archive field"),
        "trailing_bytes": reject(lambda: ReadModelDef(wire + b"\x00", 19000, Assembly=True), "unconsumed tail"),
        "escaped_small_null": reject(lambda: ReadModelDef(invalid_null, 19000, Assembly=True), "canonical"),
        "encoded_preference_bit": reject(lambda: ReadModelDef(bytes(invalid_bit), 19000, Assembly=True), "alternate boolean"),
        "encoded_preference_fraction": reject(lambda: ReadModelDef(bytes(invalid_fraction), 19000, Assembly=True), "fraction exceeds the native range"),
        "missing_preference": reject(missing_slot, "every slot from 5fc through 605"),
        "nonboolean_preference": reject(lambda: bad_input("5fc", 1), "must be boolean"),
        "nonfinite_preference": reject(lambda: bad_input("5ff", float("nan")), "finite authored domain"),
        "overflow_preference": reject(lambda: bad_input("605", 2**31), "must fit a signed long"),
    }


def renderer_wire(wire):
    require(
        sha256(wire).hexdigest() == FRESH_DIGESTS[0] and wire[RENDER_OFFSET] == 0,
        "fresh base differs from the reference renderer fixture",
    )
    result = wire[:RENDER_OFFSET] + RENDER_FRAME + wire[RENDER_OFFSET + 1:]
    require(sha256(result).hexdigest() == RENDER_DIGEST, "renderer frame differs from the resolved reference")
    return result


def author_renderer(wire):
    independent = renderer_wire(wire)
    model = ReadModelDef(wire, 19000, Assembly=True).GraphValue
    fields = model.DocumentValue.FieldsValue
    require(fields["has_pwmaterial"] == 0 and "f1110" not in fields, "authored case already has a renderer")
    fields["has_pwmaterial"] = 1
    fields["f1110"] = {"f08": 1, "f0c": 0, "list": {"n": 0, "items": []}}
    typed = WriteModelDef(model, Assembly=True).OutputValue
    require(typed == independent, "empty renderer differs from independently placed frame")
    return independent


def read_renderer(wire):
    offset = RENDER_OFFSET
    require(
        sha256(wire).hexdigest() == RENDER_DIGEST and wire[offset:offset + len(RENDER_FRAME)] == RENDER_FRAME,
        "invalid authored renderer fixture",
    )
    result = readback(wire)
    require(result["renderer"] == RENDER_SAVED, "stored empty assembly renderer was not retained")
    part_word = bytearray(wire)
    pack_into("<i", part_word, offset + 1, 6)
    reserved_word = bytearray(wire)
    pack_into("<i", reserved_word, offset + 5, 7)
    return {
        "definition": result, "offset": offset, "wrapper_frame": RENDER_FRAME.hex(),
        "part_word_rejection": reject(
            lambda: ReadModelDef(bytes(part_word), 19000, Assembly=True), "alternate renderer profile"
        ),
        "second_word_rejection": reject(
            lambda: ReadModelDef(bytes(reserved_word), 19000, Assembly=True), "alternate renderer profile"
        ),
    }


def guard_access():
    for encoding in ("ascii", "utf-8", "utf-16-le", "latin-1"):
        codecs.lookup(encoding)
    attempts = []

    def guard(event, _):
        if event in {
            "open", "os.listdir", "os.scandir", "os.system", "os.exec",
            "os.fork", "os.posix_spawn", "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError(f"assembly Definition worker attempted {event}")

    sys.addaudithook(guard)
    return attempts


def renderer_reference():
    return {
        "revision": EVIDENCE, "reference_files": REFERENCE_FILES,
        "absent_sha256": FRESH_DIGESTS[0], "present_sha256": RENDER_DIGEST,
        "offset": RENDER_OFFSET, "wrapper_frame": RENDER_FRAME.hex(),
    }


def replay_reference(reference):
    for path, digest in REFERENCE_FILES.items():
        require(sha256((reference / path).read_bytes()).hexdigest() == digest, f"unexpected reference source: {path}")
    for path in ("src", "re/tooling/sw2026", "re/tooling/sw2026/serial"):
        sys.path.insert(0, str(reference / path))
    from Classes import registry
    from builders.Definition import assembly_definition, definition_stream

    compiled = registry()
    job = input_job(0)
    attempts = guard_access()
    prior_profile = sys.getprofile()

    def check_calls(frame, event, _):
        if event != "call":
            return
        source = frame.f_code.co_filename.replace('\\', "/")
        if "/src/convert/" in source and ("/Archive/Definition/" in source or "/Archive/Bodies/" in source):
            raise ValueError("reference used the SDK Definition field executor")

    sys.setprofile(check_calls)
    try:
        document = assembly_definition(
            drafting_standard=job["standard"], detail_flags=job["bits"],
            tessellation=tuple(job["tessellation"]), system_preference_7a=job["compression"],
            journal_name=job["journal"], save_as_part_preferences=job["preferences"],
        )
        absent = definition_stream(registry=compiled, document=document)
        document.f["has_pwmaterial"] = 1
        document.f["f1110"] = {"f08": 1, "f0c": 0, "list": {"n": 0, "items": []}}
        present = definition_stream(registry=compiled, document=document)
    finally:
        sys.setprofile(prior_profile)
    require(present == renderer_wire(absent), "historical field order no longer corroborates renderer placement")
    require(not attempts, "reference author attempted runtime external access")
    return renderer_reference() | {
        "absent_bytes": len(absent), "present_bytes": len(present),
        "sdk_definition_field_calls": 0, "runtime_external_attempts": 0,
    }


def worker(mode):
    sys.path.insert(0, str(ROOT / "src"))

    global MakeAssemblyDef, MakePartDef, ModelDefInput, ReadModelDef, WriteModelDef
    global ArchiveNode, ContainerMo, SldprtArchive
    from convert.adapters.solidworks.Archive.Definition.Construction.MakeAssemblyDef import MakeAssemblyDef
    from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
    from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    attempts = guard_access()
    raw = sys.stdin.buffer.read()
    if mode == "author":
        output = emitted(json.loads(raw))
    elif mode == "readback":
        output = readback(raw)
    elif mode == "author_renderer":
        output = author_renderer(raw)
    elif mode == "read_renderer":
        output = read_renderer(raw)
    elif mode == "native":
        output = native_readback(raw)
    elif mode == "refusals":
        output = reject_cases(raw)
    else:
        raise ValueError("unknown assembly Definition phase")
    require(not attempts, "assembly Definition worker attempted external access")
    return output


def run_worker(mode, data):
    child = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode), input=data, capture_output=True,
                check=False, timeout=60)
    require(child.returncode == 0, f"{mode}: {child.stderr.decode()}")
    return child.stdout if mode in ("author", "author_renderer") else json.loads(child.stdout)


def check_author(case, job, wire, report):
    fraction = (0.0, 0.9)[case]
    signed_long = (-11, -12)[case]
    expected_options = pack("<iididiiiiii", 0, 1, fraction, 0, 1.25, 1, 0, 1, 0, 1, signed_long)
    require(len(expected_options) == 52 and wire[-56:-4] == expected_options and wire[-4:] == pack("<i", 10),
            "independently encoded inline preference order or final field differs")
    require(
        report["sha256"] == FRESH_DIGESTS[case] == sha256(wire).hexdigest()
        and report["bytes"] == len(wire)
        and report["next_map_index"] == 7
        and report["root"] == ["uiAssemblyDoc_c", 1]
        and report["renderer"] is None
        and report["journal"] == [0, job["journal"]]
        and report["standard"] == job["standard"]
        and report["tessellation"] == job["tessellation"]
        and report["compression"] == int(job["compression"])
        and report["display_words"] == ([4, -2147450879], [8, -2147450878])[case]
        and report["preferences"]["f10"] == fraction
        and report["preferences"]["f3c"] == signed_long,
        "explicit assembly design differs from the independent prior encoding",
    )


def git_bytes(revision, path):
    return check_output(("git", "-C", str(ROOT), "show", f"{revision}:{path}"))


def check_native():
    data = git_bytes(EVIDENCE, INVENTORY)
    require(sha256(data).hexdigest() == EXPECTED_INVENTORY, "historical Definition inventory digest differs")
    inventory = json.loads(data)
    require(inventory["corpus_revision"] == SOURCE, "historical source revision differs")
    rows = [row for row in inventory["records"] if row["file"].endswith(".SLDASM")]
    require(len(rows) == 8 and len({row["stream_sha256"] for row in rows}) == 3, "disclosed controls differ")
    receipts = []
    for row in rows:
        raw = git_bytes(SOURCE, row["file"])
        require(sha256(raw).hexdigest() == row["file_sha256"], "expected a pinned disclosed assembly")
        observed = run_worker("native", raw)
        require(
            observed["file_sha256"] == row["file_sha256"]
            and observed["sha256"] == row["stream_sha256"]
            and observed["bytes"] == row["bytes"] == 3900
            and observed["next_map_index"] == row["next_map_index"] == 60
            and observed["root"] == ["uiAssemblyDoc_c", 1]
            and observed["renderer"] == RENDER_SAVED
            and observed["preferences"] == PREF_SAVED
            and [observed[key] for key in ("style_count", "font_count", "view_environment_count")] == [7, 40, 1],
            f"observed Definition differs from the saved control: {row['file']}",
        )
        map_digest = sha256(json.dumps(observed["map"], separators=(",", ":")).encode()).hexdigest()
        receipts.append({
            "file": row["file"], "file_sha256": observed["file_sha256"],
            "sha256": observed["sha256"], "bytes": observed["bytes"],
            "next_map_index": observed["next_map_index"], "map_sha256": map_digest,
        })
    return receipts


def prove(include_native):
    fresh = []
    refusals = {}
    renderer = None
    for case in range(2):
        job = input_job(case)
        wire = run_worker("author", json.dumps(job, ensure_ascii=False).encode("utf-8"))
        result = run_worker("readback", wire)
        check_author(case, job, wire, result)
        if case == 0:
            refusals = run_worker("refusals", wire)
            renderer = run_worker("read_renderer", run_worker("author_renderer", wire))
            value = renderer["definition"]
            require(
                value["bytes"] == result["bytes"] + len(RENDER_FRAME) - 1
                and value["map"] == result["map"]
                and value["preferences"] == result["preferences"]
                and value["journal"] == result["journal"],
                "renderer authoring changed other typed values or map slots",
            )
        fresh.append(result)
    require(renderer is not None, "missing renderer process control")
    recorded = check_native() if include_native else []
    sources = {
        f"{DEFINITION_PACKAGE}/{name}.py": sha256((ROOT / f"{DEFINITION_PACKAGE}/{name}.py").read_bytes()).hexdigest()
        for name in OWNED_MODULES
    }
    return {
        "schema": "kit.sw2026.ordinary-assembly-definition.v1",
        "base_revision": BASE, "historical_inventory_sha256": EXPECTED_INVENTORY,
        "historical_corpus_revision": SOURCE, "sources": sources,
        "proof_sha256": sha256(HERE.read_bytes()).hexdigest(),
        "generated": fresh, "saved": recorded, "refusals": refusals,
        "authored_renderer": renderer, "renderer_placement_reference": renderer_reference(),
        "saved_renderer": RENDER_SAVED if recorded else None,
        "saved_preferences": PREF_SAVED if recorded else None,
        "saved_stream_counts": dict(Counter(row["sha256"] for row in recorded)),
        "guarded_processes": 7 + len(recorded), "runtime_external_attempts": 0,
        "native_launches": 0, "heldout_inputs_read": 0, "public_writer_enabled": False,
        "fcstd_conversion_credit": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("author", "readback", "native", "refusals", "author_renderer", "read_renderer"))
    parser.add_argument("--generated", action="store_true")
    parser.add_argument("--reference-root", type=Path)
    arguments = parser.parse_args()
    if arguments.reference_root is not None:
        output = replay_reference(arguments.reference_root.resolve())
    elif arguments.worker:
        output = worker(arguments.worker)
    else:
        output = prove(not arguments.generated)
    if isinstance(output, bytes):
        sys.stdout.buffer.write(output)
    else:
        print(json.dumps(output, ensure_ascii=True, allow_nan=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
