from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from pathlib import Path
from subprocess import run
from types import MappingProxyType
from xml.etree.ElementTree import fromstring
import importlib
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TEXTURE = "uoMaterialTextureProperties.restore"
HATCH = "gcXhatch_c"
BUILD = "34.5.2.0604"
MF_HASH = "af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735"
NATIVE = {
    "restore": (0x3c8d66a0, 0x3c8d689b, "e858c077b7f4b3020c44002e50a00ed869a898db7a1f4e0ce6780a4b00aedcef"),
    "save": (0x3c8d68a0, 0x3c8d69c8, "8eeb6c081fc85fc6b44ff9af756f98d305b6734b42d1ab1e86ce49743c2afacc"),
    "hatch": (0x3c834c80, 0x3c8350e6, "d4ad43031fa8e91e1f716ff4ec6adc022c23d69ed10c3884a2c201776b7a3f98"),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def pin_module(path):
    sys.path.insert(0, str(HERE.parent))
    from MaterialPe import PeImage

    module = PeImage(path)
    require(module.sha256 == MF_HASH, "SOLIDWORKS 2026 sldmfcu bytes differ")
    checks = []
    for label, (start, end, digest) in NATIVE.items():
        require(module.range(start) == (start, end), "native range changed: " + label)
        row = module.pin(label, start, end)
        require(row["sha256"] == digest, "native procedure changed: " + label)
        checks.append(row)
    return checks


def exploratory_profile():
    from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ModelFields import KModelFields
    from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

    cmgr = importlib.import_module("convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext")
    config = importlib.import_module("convert.adapters.solidworks.Archive.Config.MakeConfigCtx")
    fields = (
        *(NativeField("Scalar", f"f{offset:02x}", "f64") for offset in range(8, 0x70, 8)),
        NativeField("Text", "f70"),
        NativeField("Scalar", "f78", "i16"),
        NativeField("Scalar", "f7c", "i32"),
        NativeField("Scalar", "f80", "f64"),
        NativeField("Scalar", "f88", "f64"),
        NativeField("Scalar", "f9c", "i32"),
    )
    cmgr.KBodyLayouts = MappingProxyType({**cmgr.KBodyLayouts, TEXTURE: fields, HATCH: KModelFields[HATCH]})
    cmgr.KBodySchemas = MappingProxyType({**cmgr.KBodySchemas, HATCH: (1,)})
    config.KConfigLayouts = MappingProxyType({**config.KConfigLayouts, TEXTURE: fields})


def tree_shape(blob):
    if blob is None:
        return None
    require(blob.startswith(b"\xff\xfe"), "material tree changed UTF-16 wire encoding")
    value = blob.decode("utf-16")
    require("<!DOCTYPE" not in value and "<!ENTITY" not in value, "unexpected material tree declaration")
    root = fromstring(value)
    uri = "{http://www.solidworks.com/sldmaterials}"
    require(root.tag == uri + "materials", "unexpected material tree root")
    return {
        "bytes": len(blob), "sha256": sha256(blob).hexdigest(), "root": root.tag,
        "branches": [{"tag": child.tag, "children": len(child), "attributes": sorted(child.attrib)} for child in root],
        "element_names": sorted({entry.tag for entry in root.iter()}),
    }


def material_owners(manager, linked):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue

    manager_fields = manager.RootValue.FieldsValue
    current = ArchiveNode.RequireNode(manager_fields["f368"]).FieldsValue
    presentation = current.get("f78")
    visual = presentation.FieldsValue if isinstance(presentation, ArchiveNode) else presentation
    material = visual.get("f20") if isinstance(visual, dict) else None
    part = ArchiveNode.RequireNode(linked.ConfigValue.RootValue.FieldsValue["f1420"])
    parameter = ArchiveNode.RequireNode(part.FieldsValue["f08"]).FieldsValue
    identity = material.get("f20") if isinstance(material, dict) else None
    return {
        "part_density": {key: parameter.get(key) for key in ("f58", "f60", "f68")},
        "active_config_density": current.get("fc50"), "custom_material_rows": manager_fields.get("n600"),
        "active_config_material": identity.TextValue if isinstance(identity, CStringValue) else identity,
        "active_color_texture": sorted(key for key in ("f80", "f90", "f98") if isinstance(material, dict) and key in material),
        "manager_texture_calls": manager.ReportValue["schema_calls"].get(TEXTURE, 0),
        "manager_hatch_calls": manager.ReportValue["schema_calls"].get(HATCH, 0),
    }


def read_worker():
    sys.path.insert(0, str(ROOT / "src"))
    from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    raw = sys.stdin.buffer.read()
    file = SldprtArchive.from_bytes(raw)
    manager_bytes = file.require("Contents/CMgr")
    xml = tree_shape(file.streams.get("swXmlContents/MATERIALTREE"))
    for name in ("ascii", "latin-1", "utf-16-le", "utf-8"):
        lookup(name)

    def audit(name, args):
        require(name not in ("open", "os.listdir", "os.scandir", "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"),
                "research archive worker attempted external input: " + name)

    for name in (
        "Bodies.Layouts.Config.ModelFields", "Bodies.NativeField", "Cmgr.MakeCmgrContext", "Config.MakeConfigCtx",
    ):
        importlib.import_module("convert.adapters.solidworks.Archive." + name)
    sys.addaudithook(audit)
    missing = None
    try:
        ReadCmgrMut(manager_bytes, 19000)
    except BodyUnsupported as error:
        missing = str(error)
        require(missing in ("unsupported SOLIDWORKS body schema " + TEXTURE,
                            "unsupported SOLIDWORKS body class " + HATCH + " schema 1"),
                "unexpected baseline schema boundary: " + missing)
    exploratory_profile()
    manager = ReadCmgrMut(manager_bytes, 19000)
    linked = ReadNativeLink(file, 0)
    config = linked.ConfigValue
    resolved = linked.ResolvedValue
    rewritten_config, decoded_config = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    rewritten_resolved, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, decoded_config.MapValue, resolved.ContextValue)
    streams = {
        "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
        linked.ConfigName: rewritten_config,
        linked.StreamName: rewritten_resolved,
    }
    report = {}
    for name, emitted in streams.items():
        original = file.require(name)
        report[name] = {"bytes": len(original), "sha256": sha256(original).hexdigest(),
                        "typed_replay_sha256": sha256(emitted).hexdigest(), "exact": emitted == original}
    return {"file_sha256": sha256(raw).hexdigest(), "file_bytes": len(raw), "baseline_refusal": missing,
            "owners": material_owners(manager, linked), "material_tree": xml, "streams": report,
            "map_counters": {"manager": manager.MapValue.CounterValue, "configuration": config.MapValue.CounterValue,
                             "resolved_features": resolved.MapValue.CounterValue}, "runtime_file_reads": 0}


def measure(cases, module):
    records = {}
    for item in cases:
        role, expected, loc = item.split("=", 2)
        require(role and role not in records and len(expected) == 64, "invalid duplicate research case")
        raw = Path(loc).read_bytes()
        require(sha256(raw).hexdigest() == expected, "disclosed source custody differs: " + role)
        outcome = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=raw, capture_output=True, timeout=50)
        require(outcome.returncode == 0 and not outcome.stderr, outcome.stderr.decode())
        row = json.loads(outcome.stdout)
        require(row["file_sha256"] == expected, "data changed during transport")
        records[role] = row
    require(len(records) >= 2, "assigned source and unassigned control are required")
    return {"schema": "kit.sw2026.assigned-material-archive-exploration.v1", "native_build": BUILD,
            "module_sha256": MF_HASH, "native_ranges": pin_module(module),
            "proof_sha256": sha256(HERE.read_bytes()).hexdigest(), "native_processes_started": 0,
            "production_grammar_enabled": False, "writer_qualified": False, "cases": records}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--module", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", action="append", metavar="ROLE=SHA256=PATH")
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(read_worker()))
    else:
        if args.module is None or args.output is None or not args.case:
            parser.error("--module, --output and --case are required")
        report = measure(args.case, args.module)
        with args.output.open("xb") as output:
            output.write(encode(report))


if __name__ == "__main__":
    main()
