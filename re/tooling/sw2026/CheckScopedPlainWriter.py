from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


FORMAT = "solidworks.sldprt"
EPOCH = 1794000130


class WriterAudit:
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.stem = "." + target.name + ".kit-"
        self.phase = "import"
        self.denied = []
        self.target_opens = 0

    def observe(self, event, arguments):
        if self.phase == "done":
            return
        watched = (
            event in ("open", "os.listdir", "os.scandir", "subprocess.Popen", "os.system",
                      "os.exec", "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.forkpty",
                      "ctypes.dlopen", "ctypes.dlsym", "ctypes.dlsym/handle")
            or event.startswith("socket.")
        )
        if not watched:
            return
        caller = sys._getframe(1)
        module = caller.f_globals.get("__name__")
        location = arguments[0] if arguments else None
        path = Path(os.fsdecode(location)) if isinstance(location, (str, bytes)) else None
        if self.phase == "import" and caller.f_code.co_filename == "<frozen importlib._bootstrap_external>":
            if event in ("os.listdir", "os.scandir"):
                return
            if (event == "open" and caller.f_code.co_name == "get_data"
                    and path is not None and path.suffix in (".py", ".pyc")):
                return
        if (self.phase == "import" and event in ("os.listdir", "os.scandir")
                and path is not None and path.is_relative_to(self.source)):
            return
        if self.phase == "write":
            if path is not None and self.is_staging(path):
                if event in ("os.scandir", "os.listdir"):
                    return
                if event == "open" and module == "shutil" and path.is_dir():
                    return
            if event == "os.scandir" and isinstance(location, int) and module == "shutil":
                return
            if event == "open" and path is not None and len(arguments) == 3:
                flags = arguments[2]
                access = flags & (os.O_WRONLY | os.O_RDWR)
                if (access == os.O_WRONLY and flags & os.O_CREAT and flags & os.O_EXCL
                        and path.name == self.target.name and self.is_staging(path.parent)):
                    self.target_opens += 1
                    return
        self.denied.append((event, str(location)))
        raise PermissionError(f"writer attempted runtime input access: {event} {location}")

    def is_staging(self, path):
        return path.parent == self.target.parent and path.name.startswith(self.stem)


def reject(action, error_type, reason):
    try:
        action()
    except error_type as error:
        if reason not in str(error):
            raise ValueError(f"unexpected refusal: {error}") from error
        return reason
    raise ValueError(f"unqualified write crossed publication: {reason}")


def inspect_refusals(write_document, doc, target, windows_path, audit, not_found):
    original_opens = audit.target_opens
    raw = b"caller-owned input"
    buffer = BytesIO(raw)
    buffer.seek(4)
    unknown = replace(doc, metadata={**doc.metadata, "unmodeled": True})
    sketch, = doc.sketches
    edge = sketch.entities[-1]
    point = replace(edge.geometry.end, x=edge.geometry.end.x + 0.5)
    broken_edge = replace(edge, geometry=replace(edge.geometry, end=point))
    broken = replace(doc, sketches=(replace(sketch, entities=(*sketch.entities[:-1], broken_edge)),))
    refusals = {
        "caller_stream_unnamed": reject(
            lambda: write_document(doc, buffer, destination_format=FORMAT),
            ValueError, "unnamed native streams require an explicit final destination",
        ),
        "unknown_model_data": reject(
            lambda: write_document(unknown, buffer, destination_format=FORMAT,
                                   values={"final_destination": windows_path}),
            not_found, "does not support the destination",
        ),
        "disconnected_loop": reject(
            lambda: write_document(broken, target, overwrite=True),
            not_found, "no writer supports the destination",
        ),
        "unmodeled_configuration": reject(
            lambda: write_document(doc, target, overwrite=True, configuration="missing"),
            ValueError, "requested write configuration is unavailable",
        ),
        "unsupported_extension": reject(
            lambda: write_document(doc, target.with_suffix(".SLDASM")),
            not_found, "no writer supports the destination",
        ),
        "overwrite_guard": reject(
            lambda: write_document(doc, target), FileExistsError, target.name,
        ),
    }
    if audit.target_opens != original_opens or buffer.getvalue() != raw or buffer.tell() != 4:
        raise ValueError("a refused write opened an output or changed the caller's destination")
    return refusals


def readback(source, native_bytes, original, expected_path):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.Enums.EnumValues import ParameterRole

    document = open_document(
        source, source_format=FORMAT, strict=True,
        include_brep=False, include_tessellation=False,
    )
    config, = document.configurations
    original_config, = original.configurations
    config_id = config.attributes["native_configuration_id"]
    sketch, = document.sketches
    author_sketch, = original.sketches
    authored_boss, = original.feature_timeline
    boss, = [feature for feature in document.feature_timeline if feature.name == authored_boss.name]
    driving, = [value for value in document.parameters if value.id in boss.parameter_ids]
    expected_depth = original.parameters[0].value.value
    if (document.brep is not None or document.brep_payloads
            or len(document.feature_timeline) != 19
            or boss.sketch_id != sketch.id
            or not config.active or config_id != 0 or config.name != original_config.name
            or sketch.closed_profile_entity_ids != (tuple(edge.id for edge in sketch.entities),)
            or len(sketch.entities) != len(author_sketch.entities)
            or driving.name != "D1" or driving.owner_id != boss.id
            or driving.role != ParameterRole.DRIVING or driving.value.unit != "mm"
            or not isclose(driving.value.value, expected_depth, rel_tol=1e-12)):
        raise ValueError("strict public read lost the authored topology or driving depth")
    for actual, authored in zip(sketch.entities, author_sketch.entities, strict=True):
        if actual.kind != "line" or any(
            not isclose(getattr(actual_point, axis), getattr(author_point, axis),
                        rel_tol=0.0, abs_tol=1e-10)
            for actual_point, author_point in (
                (actual.geometry.start, authored.geometry.start),
                (actual.geometry.end, authored.geometry.end),
            )
            for axis in ("x", "y")
        ):
            raise ValueError("strict public read changed ordered model geometry")
    archive = SldprtArchive.from_bytes(native_bytes)
    link = ReadNativeLink(archive, config_id)
    linked = IndexFeatures(link)
    native = GetFileRef(link.ConfigValue.HeaderValue.FieldsValue["f38"])
    native_boss, = [node for node in linked.values() if node.ClassValue.NameValue == "moExtrusion_c"]
    extrusion = ReadExtrude(link, native_boss, linked)
    if (len(linked) != len(document.feature_timeline) or native.PathValue != expected_path
            or boss.id != f"sldprt:feature:{NativeNodeId(native_boss)}"
            or sketch.id != f"sldprt:sketch:{NativeNodeId(extrusion.ProfileValue)}"
            or not isclose(extrusion.DepthValue.DepthValue.value_mm, expected_depth, rel_tol=1e-12)):
        raise ValueError("native link changed the resolved owners, depth or final path")
    return {
        "tree_rows": len(document.feature_timeline),
        "linked_root_rows": len(linked),
        "line_count": len(sketch.entities),
        "driving_dimension": [driving.name, driving.value.unit, driving.value.value,
                              driving.owner_id == boss.id],
    }


def read_cold_geometry(source, original):
    from convert import open_document

    document = open_document(source, source_format=FORMAT)
    model = document.brep
    if model is None or document.brep_payloads:
        raise ValueError("default strict read must derive the cold body from its editable model")
    body, = document.bodies
    solid, = model.bodies
    region, = model.regions
    shell, = model.shells
    sketch, = original.sketches
    original_boss, = original.feature_timeline
    boss, = [feature for feature in document.feature_timeline if feature.name == original_boss.name]
    sides = len(sketch.entities)
    expected_topology = (1, 1, sides + 2, 3 * sides, 2 * sides)
    expected_volume = abs(sum(
        edge.geometry.start.x * edge.geometry.end.y - edge.geometry.end.x * edge.geometry.start.y
        for edge in sketch.entities
    )) * original.parameters[0].value.value / 2
    summary = body.topology
    topology = (
        summary.solid_count, summary.shell_count, summary.face_count,
        summary.edge_count, summary.vertex_count,
    )
    if (body.final_feature_id != boss.id or solid.design_body_id != body.id
            or model.validate(frozenset({body.id})) or not region.solid or not shell.closed
            or topology != expected_topology
            or (len(model.faces), len(model.edges), len(model.vertices)) != expected_topology[2:]
            or summary.volume is None or not isclose(summary.volume, expected_volume, rel_tol=1e-12)):
        raise ValueError("default strict read changed the authored body ownership, topology or volume")
    return {"topology": topology, "volume_mm3": summary.volume, "body_feature_linked": True}


def publish(target, source_text, audit):
    from convert import write_document
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from interchange.document.Models.DocumentModel import CadDocument

    for module_name in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module_name)
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    emitter.ReadTime = lambda: EPOCH
    for name in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(name)
    explicit_path = rf"C:\KitPlainWriter\{target.name}"
    path_expected = str(target) if os.name == "nt" else rf"C:\KitSdkCandidates\{target.name}"
    strict = {"require_native_transfers": True}
    audit.phase = "write"
    doc = CadDocument.from_json(source_text)
    if doc.metadata != {"name": target.stem}:
        raise ValueError("authored neutral model and test target differ")
    disk = write_document(doc, target, allow_carrier=False, values=strict)
    memory = BytesIO()
    stream = write_document(doc, memory, destination_format=FORMAT, allow_carrier=False,
                            values={**strict, "final_destination": str(target)})
    windows = BytesIO()
    write_document(doc, windows, destination_format=FORMAT, allow_carrier=False,
                   values={**strict, "final_destination": explicit_path})
    refusals = inspect_refusals(write_document, doc, target, explicit_path, audit, NotFoundError)
    return doc, disk, stream, memory.getvalue(), windows.getvalue(), path_expected, explicit_path, refusals


def measure(root, target, source_text):
    sys.path.insert(0, str(root / "src"))
    audit = WriterAudit(root / "src", target)
    sys.addaudithook(audit.observe)
    try:
        doc, disk, stream, report, windows, path_expected, explicit_path, refusals = publish(
            target, source_text, audit)
    finally:
        audit.phase = "done"
    from convert import extract_brep
    from convert.adapters.solidworks.Container.Container import SldprtArchive, SldprtFormatError

    if audit.denied or audit.target_opens != 1:
        raise ValueError(f"unexpected writer input or output access {audit.denied}")
    if (tuple(target.parent.iterdir()) != (target,) or target.read_bytes() != report
            or disk.path != target or stream.path is not None
            or disk.bytes_written != len(report) or stream.bytes_written != len(report)
            or disk.native_capabilities != stream.native_capabilities
            or len(stream.native_capabilities) != 6
            or not (disk.vendor_loadable and stream.vendor_loadable
                    and disk.application_usable and stream.application_usable)):
        raise ValueError("file staging and caller-owned stream disagree")
    path_read = readback(target, report, doc, path_expected)
    stream_read = readback(report, report, doc, path_expected)
    if readback(windows, windows, doc, explicit_path) != path_read:
        raise ValueError("explicit Windows locator changed the part model")
    cold_read = read_cold_geometry(target, doc)
    if read_cold_geometry(report, doc) != cold_read:
        raise ValueError("file and memory disagree on default strict geometry")
    raw_target = target.parent.parent / "raw"
    raw_refusal = reject(
        lambda: extract_brep(report, raw_target, source_format=FORMAT),
        SldprtFormatError, "SLDPRT contains no readable Parasolid payload",
    )
    if raw_target.exists():
        raise ValueError("declined raw extraction created a destination")
    archive = SldprtArchive.from_bytes(report)
    names = (
        "Contents/Config-0", "Contents/Config-0-ResolvedFeatures",
        "Contents/Config-0-ModelHeader", "Contents/CMgr",
        "Contents/Definition", "swXmlContents/KeyWords",
    )
    if any(name.startswith("Kit/") for name in archive.streams):
        raise ValueError("public part unexpectedly relies on a neutral carrier")
    research_modules = [
        module.__name__ for name, module in tuple(sys.modules.items()) if name != "__main__"
        and getattr(module, "__file__", None)
        and Path(module.__file__).is_relative_to(root / "re")
    ]
    if research_modules or any(name.startswith(("pythoncom", "win32com")) for name in sys.modules):
        raise ValueError("writer escaped the standalone SDK boundary")
    return {
        "file_stream_equal": True,
        "physical_destinations_intact": True,
        "target_file_opens": audit.target_opens,
        "path_readback": path_read,
        "stream_readback": stream_read,
        "default_geometry": cold_read,
        "raw_extraction_refusal": raw_refusal,
        "explicit_windows_locator": True,
        "native_capabilities": sorted(value.value for value in stream.native_capabilities),
        "logical_stream_lengths": {name: len(archive.require(name)) for name in names},
        "sha256": sha256(report).hexdigest(),
        "bytes": len(report),
        "refusals": refusals,
        "writer_input_file_reads": len(audit.denied),
        "sdk_runtime_research_imports": len(research_modules),
    }


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    source_text = sys.stdin.buffer.read().decode("utf-8")
    with TemporaryDirectory(prefix="KitPlainWriter-") as directory:
        target = Path(directory).resolve() / "native" / "QueuePlain.SLDPRT"
        print(json.dumps(measure(root, target, source_text), sort_keys=True, allow_nan=False))
