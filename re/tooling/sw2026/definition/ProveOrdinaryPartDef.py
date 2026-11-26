from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from struct import pack
from subprocess import check_output, run
import codecs
import json
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
BASE = "16493de95602b732a569923ec89cfee13a87d45d"
HISTORICAL = "81aff00e947ef3bb39fb479c265782d7ca7a0581"
ARCHIVE = Path("src/convert/adapters/solidworks/Archive")
NATIVE = {
    "L1": (
        BASE,
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "14d9b75edf4586f8e1db2b166e855e29a03d4c88256e26d24351edb5c43d8a87",
    ),
    "D19Annulus": (
        HISTORICAL,
        "curves-discovery/D19Annulus.SLDPRT",
        "2a9846fa9ddc882ef3b848dfc311a7859d102ab9fa7687769cdba88a7b510439",
        "b01c48a44afe1f63f9d7d08f548d3aac96860a4c69fd7365c7eeeaa85beb3aff",
    ),
}
AUTHORED = {
    "ordinary": {
        "standard": "moISO_c",
        "bits": [],
        "tessellation": [26, 4, 25, True],
        "compression": False,
        "journal": "Journal",
        "density": 1000.0,
    },
    "presentation": {
        "standard": "moDIN_c",
        "bits": [0, 5, 31, 58, 63],
        "tessellation": [36, 4, 32, False],
        "compression": True,
        "journal": "Geometric δ 🚲 " + "Archive " * 35,
        "density": 3167.25,
    },
}
ORDINARY_SHA256 = "2381c1a45d1554608019d81fd151ee7ee2fb9d43c1ef6ab2b988892cc5130dfd"


def require(valid, message):
    if not valid:
        raise ValueError(message)


def authored(values):
    from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
        MakePartDef,
    )
    from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
        ModelDefInput,
    )

    return MakePartDef(
        ModelDefInput(
            values["standard"],
            tuple(values["bits"]),
            tuple(values["tessellation"]),
            values["compression"],
            values["journal"],
            19000,
        ),
        values["density"],
    )


def emitted(raw):
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import (
        WriteModelDef,
    )

    output = WriteModelDef(authored(json.loads(raw)))
    require(
        output.UsageValue.IsComplete and output.MapValue.CounterValue == 7,
        "fresh part definition did not derive the ordinary archive map",
    )
    return output.OutputValue


def map_shape(snapshot):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

    result = []
    for entry in snapshot.EntriesValue:
        value = entry.EntryValue
        descriptor = value.ClassValue if isinstance(value, ArchiveNode) else value
        result.append(
            (
                entry.IndexValue,
                isinstance(value, ArchiveNode),
                descriptor.NameValue,
                descriptor.SchemaValue,
            )
        )
    return result


def readback(data):
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import (
        WriteModelDef,
    )

    typed = ReadModelDef(data, 19000)
    result = WriteModelDef(typed.GraphValue)
    require(
        result.OutputValue == data
        and typed.UsageValue.IsComplete
        and result.UsageValue.IsComplete
        and not typed.UsageValue.MissingNames
        and not result.UsageValue.MissingNames
        and result.MapValue.CounterValue == typed.MapValue.CounterValue
        and map_shape(result.MapValue) == map_shape(typed.MapValue),
        "typed part Definition did not reproduce its bytes and map",
    )
    fields = typed.GraphValue.DocumentValue.FieldsValue
    journal = fields["ffd8"]["f18"]
    render = fields.get("f1110")
    return {
        "size": len(data),
        "sha256": sha256(data).hexdigest(),
        "next_map_index": typed.MapValue.CounterValue,
        "typed_wire_equal": True,
        "root": [
            typed.GraphValue.DocumentValue.ClassValue.NameValue,
            typed.GraphValue.DocumentValue.ClassValue.SchemaValue,
        ],
        "drafting_standard": fields["fba8"].ClassValue.NameValue,
        "density_kg_m3": fields["f1688"],
        "display_words": [fields["fad8_0"], fields["fad8_1"]],
        "tessellation": [fields[name] for name in ("fa58", "fa5c", "fa60", "fa64")],
        "preference_7a": fields["fa90"],
        "journal": {
            "schema": journal.ClassValue.SchemaValue,
            "units": len(journal.FieldsValue["f08"].encode("utf-16-le")) // 2,
            "sha256": sha256(journal.FieldsValue["f08"].encode()).hexdigest(),
        },
        "line_style_count": len(fields["f878"]["styles"]),
        "font_count": len(fields["f870"].FieldsValue["f10"]),
        "splitter_grids": [
            [
                [row["o"].FieldsValue[key][item] for item in ("f08", "f0c")]
                for key in ("f10", "fe0")
            ]
            for row in fields["faf8"]
        ],
        "renderer_empty_wrapper": (
            [render["f08"], render["f0c"], render["list"]["n"]]
            if render is not None
            else None
        ),
    }


def native_readback(raw, label):
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    _, _, expected_file, expected_stream = NATIVE[label]
    require(
        sha256(raw).hexdigest() == expected_file,
        "received a different disclosed native file",
    )
    archive = SldprtArchive.from_bytes(raw)
    require(
        archive.format_version == 4 and ContainerMo(archive.streams) == 19000,
        "disclosed file did not have the measured native profile",
    )
    data = archive.require("Contents/Definition")
    require(
        sha256(data).hexdigest() == expected_stream and len(data) == 3816,
        "disclosed Definition differs from its prior fingerprint",
    )
    result = readback(data)
    require(
        result["next_map_index"] == 60
        and result["root"] == ["uiPartDoc_c", 1]
        and result["line_style_count"] == 7
        and result["font_count"] == 40
        and result["splitter_grids"] == [[[1, 1], [2, 1]]]
        and result["renderer_empty_wrapper"] == [6, 0, 0],
        "disclosed populated graph or renderer scope differs",
    )
    return {"file_sha256": expected_file, **result}


def refusal(call, expected):
    from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import (
        BodyUnsupported,
    )

    try:
        call()
    except (BodyUnsupported, ValueError) as error:
        require(expected in str(error), f"unexpected part Definition refusal: {error}")
        return str(error)
    raise ValueError(f"unsupported part Definition was accepted: {expected}")


def refusals():
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import (
        WriteModelDef,
    )
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Container.Definition import KAsmClsid

    fresh = authored(AUTHORED["ordinary"])
    stock = fresh.DocumentValue
    data = WriteModelDef(fresh).OutputValue

    def alternate(**changes):
        graph = replace(
            fresh,
            DocumentValue=ArchiveNode(
                stock.ClassValue, {**stock.FieldsValue, **changes}
            ),
        )
        return WriteModelDef(graph)

    def wrong_class(name, schema):
        return WriteModelDef(
            replace(
                fresh,
                DocumentValue=ArchiveNode(
                    RuntimeClass(name, schema), stock.FieldsValue
                ),
            )
        )

    return {
        "read_assembly": refusal(
            lambda: ReadModelDef(pack("<5i", 26, 4, 25, 1, 1) + KAsmClsid, 19000),
            "ordinary part CLSID",
        ),
        "write_assembly": refusal(
            lambda: wrong_class("uiAssemblyDoc_c", 1), "uiPartDoc_c schema 1"
        ),
        "write_root_schema": refusal(
            lambda: wrong_class("uiPartDoc_c", 2), "uiPartDoc_c schema 1"
        ),
        "read_old_version": refusal(
            lambda: ReadModelDef(data, 18000), "requires archive version 19000"
        ),
        "write_future_version": refusal(
            lambda: WriteModelDef(replace(fresh, VersionValue=19001)),
            "requires archive version 19000",
        ),
        "read_tail": refusal(
            lambda: ReadModelDef(data + b"\x00", 19000), "unconsumed tail"
        ),
        "write_renderer_marker": refusal(
            lambda: alternate(has_pwmaterial=2), "alternate renderer marker"
        ),
        "write_renderer_inactive": refusal(
            lambda: alternate(f1110={}), "inactive renderer owner"
        ),
        "write_renderer_objects": refusal(
            lambda: alternate(
                has_pwmaterial=1,
                f1110={
                    "f08": 6,
                    "f0c": 0,
                    "list": {"items": [{"o": stock.FieldsValue["fba8"]}]},
                },
            ),
            "renderer objects",
        ),
        "write_model_data_scene": refusal(
            lambda: alternate(fbf0={"f08": stock.FieldsValue["fba8"], "f10": 0}),
            "alternate scene or OLE owner",
        ),
        "write_unknown_density": refusal(
            lambda: authored({**AUTHORED["ordinary"], "density": 0}),
            "part density must be positive",
        ),
        "write_invalid_display_bits": refusal(
            lambda: authored({**AUTHORED["ordinary"], "bits": [64]}),
            "bit positions below 64",
        ),
    }


def emit_references(wide=False):
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import (
        WriteModelDef,
    )
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

    model = authored(AUTHORED["ordinary"])
    style_class = RuntimeClass("moLineStyle_c", 1)
    if wide:
        nodes = [
            ArchiveNode(
                style_class,
                {"f08": f"Style {index:05d}", "f10": "", "f18": [], "f20": 0},
            )
            for index in range(0x7FFF - 3)
        ]
        nodes.append(nodes[-1])
    else:
        shared = ArchiveNode(
            style_class, {"f08": "Shared", "f10": "S01", "f18": [], "f20": 0}
        )
        separate = ArchiveNode(
            style_class, {"f08": "Distinct", "f10": "S02", "f18": [], "f20": 0}
        )
        nodes = [shared, shared, separate]
    model.DocumentValue.FieldsValue["f878"] = {
        "styles": [{"o": node} for node in nodes]
    }
    return WriteModelDef(model).OutputValue


def refuse_reference_widths(data):
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag

    typed = ReadModelDef(data, 19000)
    styles = typed.GraphValue.DocumentValue.FieldsValue["f878"]["styles"]
    first, repeated, separate = (row["o"] for row in styles)
    require(
        first is repeated and first is not separate
        and first.ClassValue is separate.ClassValue
        and first.IndexValue == 4 and separate.IndexValue == 5
        and typed.MapValue.CounterValue == 10
        and WriteModelDef(typed.GraphValue).OutputValue == data,
        "authored reference control did not preserve its two mapped style owners",
    )
    require(
        first.EndOffset is not None and separate.StartOffset == first.EndOffset + 2,
        "authored sibling tag boundaries do not match the shared style",
    )
    cases = (
        ("ObjectRef", first.EndOffset, 4, 4, 4),
        ("ClassRef", separate.StartOffset, 0x8003, 0x80000003, 3),
    )
    output = {}
    for kind, offset, short, wide, index in cases:
        require(data[offset:offset + 2] == pack("<H", short), "wrong short reference tag")
        altered = data[:offset] + pack("<HI", 0x7FFF, wide) + data[offset + 2:]
        permissive, end = ReadTag(altered, offset)
        require(
            (permissive.KindValue, permissive.IndexValue, end) == (kind, index, offset + 6),
            "wide contrast did not retain its valid structural tag meaning",
        )
        output[kind] = refusal(
            lambda: ReadModelDef(altered, 19000), "archive tag uses a noncanonical width"
        )
    return output


def replay_wide_reference(data):
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef

    typed = ReadModelDef(data, 19000)
    rows = typed.GraphValue.DocumentValue.FieldsValue["f878"]["styles"]
    owner = rows[-2]["o"]
    require(
        len(rows) == 0x7FFF - 2 and rows[-1]["o"] is owner
        and owner.IndexValue == 0x7FFF and owner.EndOffset is not None,
        "the threshold tag did not resolve to its actual mapped style",
    )
    offset = owner.EndOffset
    tag = data[offset:offset + 6]
    require(tag == pack("<HI", 0x7FFF, 0x7FFF), "wrong canonical wide tag bytes")
    written = WriteModelDef(typed.GraphValue)
    require(
        written.OutputValue == data
        and written.MapValue.CounterValue == typed.MapValue.CounterValue,
        "the canonical wide reference did not replay exactly",
    )
    return {
        "object_index": owner.IndexValue,
        "next_map_index": typed.MapValue.CounterValue,
        "tag_width": len(tag),
        "typed_wire_equal": True,
    }


def refuse_repeated_class(data):
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag

    typed = ReadModelDef(data, 19000)
    rows = typed.GraphValue.DocumentValue.FieldsValue["f878"]["styles"]
    first, repeated, separate = (row["o"] for row in rows)
    offset = separate.StartOffset
    tag, end = ReadTag(data, offset)
    require(
        first is repeated and first is not separate
        and first.ClassValue == separate.ClassValue and tag.KindValue == "ClassRef"
        and tag.IndexValue == 3 and end == offset + 2
        and WriteModelDef(typed.GraphValue).OutputValue == data,
        "the canonical contrast requires an exact reference to its mapped class",
    )
    name = separate.ClassValue.NameValue.encode("ascii")
    descriptor = pack("<HHH", 0xFFFF, separate.ClassValue.SchemaValue, len(name)) + name
    alternate = data[:offset] + descriptor + data[end:]
    return {
        "class_name": name.decode("ascii"),
        "canonical_class_slot": tag.IndexValue,
        "canonical_replays": True,
        "diagnostic": refusal(
            lambda: ReadModelDef(alternate, 19000),
            "archive repeats a canonical class declaration",
        ),
    }


def worker(mode):
    sys.path.insert(0, str(REPO / "src"))
    from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
        MakePartDef,
    )
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import (
        WriteModelDef,
    )
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    for encoding in ("ascii", "utf-8", "utf-16-le", "latin-1"):
        codecs.lookup(encoding)
    attempts = []

    def guard(event, _):
        if event in {
            "open",
            "os.listdir",
            "os.scandir",
            "os.system",
            "os.exec",
            "os.fork",
            "os.posix_spawn",
            "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError(f"Definition worker attempted {event}")

    sys.addaudithook(guard)
    raw = sys.stdin.buffer.read()
    if mode == "author":
        output = emitted(raw)
    elif mode == "readback":
        output = readback(raw)
    elif mode == "refusals":
        output = refusals()
    elif mode == "author_refs":
        output = emit_references()
    elif mode == "wide_refs":
        output = refuse_reference_widths(raw)
    elif mode == "author_wide_tag":
        output = emit_references(wide=True)
    elif mode == "replay_wide_tag":
        output = replay_wide_reference(raw)
    elif mode == "repeat_type_declaration":
        output = refuse_repeated_class(raw)
    elif mode in NATIVE:
        output = native_readback(raw, mode)
    else:
        raise ValueError("unknown Definition worker phase")
    require(not attempts, "Definition worker attempted external access")
    return output


def run_worker(mode, data):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode),
        input=data,
        capture_output=True,
    )
    require(child.returncode == 0, f"{mode}: {child.stderr.decode()}")
    return child.stdout if mode == "author" else json.loads(child.stdout)


def verify_authored(value, settings):
    mask = sum(1 << bit for bit in set(settings["bits"]))
    words = unpack_words(mask)
    require(
        value["drafting_standard"] == settings["standard"]
        and value["density_kg_m3"] == settings["density"]
        and value["display_words"] == words
        and value["tessellation"] == settings["tessellation"]
        and value["preference_7a"] == settings["compression"]
        and value["journal"]["sha256"]
        == sha256(settings["journal"].encode()).hexdigest()
        and value["journal"]["schema"] == 0
        and not value["font_count"]
        and not value["line_style_count"]
        and not value["splitter_grids"]
        and value["renderer_empty_wrapper"] is None
        and value["next_map_index"] == 7,
        "fresh typed result differs from its independently authored Definition intent",
    )


def unpack_words(mask):
    from struct import unpack

    return list(unpack("<ii", pack("<Q", mask)))


def prove():
    head = check_output(("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip()
    require(head == BASE, "use the exact selected Definition base")
    generated = {}
    requests = {
        name: json.dumps(value, sort_keys=True).encode()
        for name, value in AUTHORED.items()
    }
    for name, request in requests.items():
        wire = run_worker("author", request)
        generated[name] = run_worker("readback", wire)
        verify_authored(generated[name], AUTHORED[name])
    require(
        generated["ordinary"]["sha256"] == ORDINARY_SHA256
        and generated["ordinary"]["size"] == 459
        and generated["presentation"]["size"] > generated["ordinary"]["size"],
        "historical ordinary Definition bytes or model-dependent length differs",
    )
    repeat = run_worker("author", requests["presentation"])
    require(
        sha256(repeat).hexdigest() == generated["presentation"]["sha256"],
        "independent generation changed Definition bytes",
    )
    negative = run_worker("refusals", b"")
    saved = {}
    for label, (revision, path, _, _) in NATIVE.items():
        data = check_output(
            ("git", "show", f"{revision}:re/solidworks/v2026/corpus/{path}"), cwd=REPO
        )
        saved[label] = native_readback_receipt(label, data, revision, path)
    hashes = (REPO / ARCHIVE / "Definition").rglob("*.py")
    files = (
        *sorted(hashes),
        REPO / ARCHIVE / "Construction/Geometry/IdentityXform.py",
        REPO / ARCHIVE / "Bodies/Layouts/ContainerFields.py",
        HERE,
    )
    return {
        "schema": "kit.sw2026.ordinary-part-definition.v1",
        "baseline": head,
        "historical_author_source": HISTORICAL,
        "authored": generated,
        "deterministic_fresh_repeat": True,
        "saved": saved,
        "native_sources_read_after_author_and_refusals": True,
        "guarded_processes": 2 * len(AUTHORED) + len(NATIVE) + 2,
        "guarded_external_access_attempts": 0,
        "private_input_reads": 0,
        "refusals": negative,
        "native_open_runs": 0,
        "complete_part_outputs": 0,
        "tool_sha256": {
            str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }


def native_readback_receipt(label, data, revision, path):
    return {
        "source_revision": revision,
        "source_path": f"re/solidworks/v2026/corpus/{path}",
        **run_worker(label, data),
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker")
    args = parser.parse_args()
    result = worker(args.worker) if args.worker else prove()
    if isinstance(result, bytes):
        sys.stdout.buffer.write(result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
