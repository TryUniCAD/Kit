from argparse import ArgumentParser
from codecs import lookup
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from math import isclose
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
FORMAT = "solidworks.sldprt"
INPUTS = {
    "OpenShell.SLDPRT": ("73a4330ef831d38273ef6128bcbff15e4a105421219293ae5454941a3c7301cd", 2.8, 18559.408, 13783.12, 10.810327743, 15),
    "OpenShellEdited.SLDPRT": ("c0be437a8c13a50c940b0d9cee51d369865abf3fa0a7ed62610fb9c76eb4b810", 3.53, 22690.287908, 13519.3272, 11.032153046, 20),
}
CONTROL = ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"
CONTROL_SHA = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
CONTROL_PROJECTION_SHA = "8529155cf5649b5ca574731ae2bb36a6f4717e1176fbd029f4a4d445ed13deab"
NATIVE_RECEIPT_SHA = "d469a4d75549f1c95948047264c118adadb3b843b3376218140baa61c752987b"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def guarded_worker(raw, name, edited_raw=None):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent.parent), str(HERE.parent)]
    from CheckScopedPlainWriter import WriterAudit
    from ReplaySavedShell import replay_manager, replay_resolved
    from convert import open_document
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.Features.FeatureKinds import NativeFeature, ShellFeature

    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)

    audit = WriterAudit(ROOT / "src", HERE.parent / "Unused.SLDPRT")
    layout = ROOT / "src/convert/adapters/solidworks/Config/RootLayout.json"
    resources = []

    def observe(event, args):
        if name == CONTROL.name and event == "open" and Path(args[0]) == layout:
            resources.append("RootLayout.json")
            return
        audit.observe(event, args)

    sys.addaudithook(observe)
    audit.phase = "cold"
    if name == CONTROL.name:
        require(sha256(raw).hexdigest() == CONTROL_SHA, "plain control changed")
        doc = open_document(raw, source_format=FORMAT, strict=True)
        require(doc.bodies and all(step.kind.value != "shell" for step in doc.feature_timeline), "plain control changed scope")
        encoded = doc.to_json(indent=None)
        digest = sha256(encoded.encode()).hexdigest()
        require(digest == CONTROL_PROJECTION_SHA, "control differs from the exact prerequisite revision")
        require(not audit.denied and not audit.target_opens, "control used unexpected files after import")
        audit.phase = "done"
        return {"source_sha256": CONTROL_SHA, "strict_document_sha256": digest,
                "diagnostics": [value.code for value in doc.diagnostics], "runtime_data_reads": 0,
                "packaged_layout_reads": len(resources)}

    expected, thickness, volume, area, centre_z, mark = INPUTS[name]
    require(sha256(raw).hexdigest() == expected, "disclosed shell source changed in transport")
    if edited_raw is not None:
        require(sha256(edited_raw).hexdigest() == INPUTS["OpenShellEdited.SLDPRT"][0], "edited partition contrast changed")
    archive = SldprtArchive.from_bytes(raw, name)
    loaded = ReadNativeLink(archive, 0, ReadShells=True)
    stock, feature = loaded.ResolvedValue.RootsValue[-2:]
    require(feature.FieldsValue["f3d0"].FieldsValue["f18"] == mark, "active mark differs")
    pair = []
    for include in (True, False):
        doc = open_document(raw, source_format=FORMAT, include_brep=include, strict=True)
        (shell,) = (step for step in doc.feature_timeline if isinstance(step.definition, ShellFeature))
        (param,) = (row for row in doc.parameters if row.owner_id == shell.id)
        (body,), (selection,), (sketch,) = doc.bodies, doc.selections, doc.sketches
        require(shell.definition.outward is False and shell.definition.thickness == param.value
                and isclose(param.value.value, thickness, rel_tol=1e-15) and param.name == "D1"
                and param.role.value == "driving" and shell.parameter_ids == (param.id,), "live D1 differs")
        owner = param.attributes["typed_archive_owner"]
        require(owner["dimension_id"] == 33 and owner["object_index"] == 295
                and owner["slot"] == "f818" and param.attributes["native_value"] == float(Decimal(str(thickness)) / 1000),
                "incorrect physical thickness owner")
        require(shell.selection_ids == (selection.id,) and len(selection.path) == 1
                and (selection.path[0].entity_kind, selection.path[0].entity_id, selection.path[0].subelement)
                == ("feature", shell.input_feature_ids[0], "face:1")
                and selection.provenance.spans[0].record_kind == "typed-archive-object",
                "shell removal is not the earlier stock cap")
        require(len(sketch.entities) == 4 and tuple(sorted(relation.kind for relation in sketch.constraints))
                == ("coincident",) * 4 + ("horizontal",) * 2 + ("vertical",) * 2
                and sketch.attributes["typed_line_loop"]
                and body.name == "OpenShell" and body.final_feature_id == shell.id and body.attributes["native_atom_id"] == 101,
                "modeled stock or body ownership changed")
        topology = body.topology
        require((topology.solid_count, topology.shell_count, topology.face_count,
                 topology.edge_count, topology.vertex_count) == (1, 1, 11, 24, 16), "wrong shell topology")
        require(isclose(topology.volume, volume, rel_tol=5e-7)
                and isclose(topology.surface_area, area, rel_tol=5e-7), "saved shape metrics differ from native authority")
        centroid = body.attributes["solidworks.body_centroid_mm"]
        require(abs(centroid[0]) < 1e-10 and abs(centroid[1]) < 1e-10 and isclose(centroid[2], centre_z, rel_tol=5e-7),
                "saved centroid differs from native authority")
        require((doc.brep is not None) == include
                and (not include or doc.brep.bodies[0].design_body_id == body.id)
                and (include or not doc.brep_payloads), "incorrect design or boundary mode")
        if include:
            doc.assert_valid()
        reread = type(doc).from_json(doc.to_json())
        require(reread.feature_timeline[-1].definition == shell.definition
                and reread.selections[0].path == selection.path
                and reread.parameters[-1].value == param.value
                and reread.bodies[0].topology == topology, "portable JSON loses shell intent or its topology summary")
        pair.append({"include_brep": include, "parameter_id": param.id, "native_metres": param.attributes["native_value"],
                     "bounds_mm": [[-26.5, -20.5, 0.0], [26.5, 20.5, 28.0]],
                     "volume_mm3": topology.volume, "area_mm2": topology.surface_area, "centroid_mm": centroid,
                     "selection_owner_offset": selection.provenance.spans[0].offset,
                     "topology": [1, 1, 11, 24, 16], "native_atom_id": 101, "configured_mark": mark,
                     "json": True, "shell_id": shell.id, "stock_id": shell.input_feature_ids[0]})

    def encode(changes):
        signatures, type_ids = TemplateFields(raw, archive)
        return EmitSldprt([(record.name, changes.get(record.name, record.data)) for record in archive.records],
                          archive.file_id, archive.format_version, signatures, type_ids)

    def contrast(kind):
        link = ReadNativeLink(archive, 0, ReadShells=True)
        if kind == "manager_owner":
            manager = link.ManagerValue.RootValue
            atom = manager.FieldsValue["f360"].FieldsValue["f450"][0]["o"]
            atom.FieldsValue["fd0"]["items"][0]["v"] += 1
            return encode({"Contents/CMgr": replay_manager(manager)})
        config, resolved = link.ConfigValue, link.ResolvedValue
        stock, shell = resolved.RootsValue[-2:]
        fields = shell.FieldsValue
        picks = fields["f828"].FieldsValue
        face = picks["items"][0]["o"]
        if kind == "two_caps":
            earlier = stock.FieldsValue["f4a8"]["f48"]["items"][0]["o"]
            bottom = earlier.FieldsValue["f08"]["items"][0]["o"]
            other = ArchiveNode(face.ClassValue, {**face.FieldsValue, "fe8": bottom})
            picks.update(n=2, items=[picks["items"][0], {"o": other}])
        elif kind == "owner":
            rep = face.FieldsValue["fe8"].FieldsValue["f10"][0]["f08"]
            fr = rep.FieldsValue["f10"]["f10"]
            fr.FieldsValue["f10"]["f00"] = shell.FieldsValue["f08"]
        elif kind == "outward":
            fields["f820"] = 1
        elif kind == "aux_atom":
            fields["f848"].FieldsValue["f1c"] += 1
        elif kind == "thickness":
            driver = fields["f818"].FieldsValue["f850"][0]["o"].FieldsValue["ff0"]
            driver.FieldsValue["f28"].FieldsValue["f58"] *= 2
        else:
            raise ValueError("unrecognized synthetic decoder contrast")
        changed = replay_resolved(config.MapValue, config.RootValue, resolved)
        return encode({link.StreamName: changed})

    refusals = {}
    if edited_raw is not None:
        edited = SldprtArchive.from_bytes(edited_raw, "OpenShellEdited.SLDPRT")
        name_value = "Contents/Config-0-Partition"
        cases = {
            "two_caps": "requires one selected cap",
            "outward": "requires one selected cap",
            "owner": "different producer or creation event",
            "aux_atom": "another component or atom owner",
            "thickness": "differs from its linked display value",
            "cache_owner": "partition does not own its active single body",
            "manager_owner": "linked manager row identifies another body",
        }
        for kind, reason in cases.items():
            data = encode({name_value: edited.require(name_value)}) if kind == "cache_owner" else contrast(kind)
            for include in (True, False):
                try:
                    open_document(data, source_format=FORMAT, include_brep=include, strict=True)
                except SldprtFormat as error:
                    require("SOLIDWORKS 2026 shell history" in str(error) and reason in str(error.__cause__),
                            f"{kind} refused for another reason: {error.__cause__}")
                else:
                    raise ValueError(f"{kind} crossed strict inspection")
            partial = open_document(data, source_format=FORMAT, strict=False, include_brep=False)
            (step,) = (row for row in partial.feature_timeline if row.kind.value == "shell")
            require(isinstance(step.definition, NativeFeature) and not step.selection_ids
                    and any(diag.code == "sldprt.shell_history_unresolved" for diag in partial.diagnostics),
                    "permissive fallback claimed an unsupported shell selection")
            refusals[kind] = {"strict_reads_refused": 2, "permissive_native_fallback": True}
    require(not audit.denied and not audit.target_opens, "shell reader used files after import")
    audit.phase = "done"
    return {"sha256": expected, "readback": pair, "refusals": refusals, "runtime_data_reads": 0}


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--disclosure", type=Path)
    mode.add_argument("--worker")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        transport = sys.stdin.buffer.read()
        size = int.from_bytes(transport[:8], "little")
        raw, contrast = transport[8 : 8 + size], transport[8 + size :]
        print(dumps(guarded_worker(raw, args.worker, contrast or None), sort_keys=True, allow_nan=False))
        return
    require(args.output is not None, "choose a fresh JSON output")
    directory = args.disclosure.resolve(strict=True)
    require(directory.name == "Disclosure", "expected the named disclosed shell directory")
    receipt = directory / "Receipt.json"
    require(receipt.is_file() and not receipt.is_symlink(), "native receipt must be the disclosed regular file")
    native = receipt.read_bytes()
    require(sha256(native).hexdigest() == NATIVE_RECEIPT_SHA, "native source receipt changed")
    paths = {name: directory / name for name in INPUTS} | {CONTROL.name: CONTROL}
    require(all(path.is_file() and not path.is_symlink() for path in paths.values()),
            "inputs must be the disclosed regular files")
    data = {name: path.read_bytes() for name, path in paths.items()}
    rows = {}
    for name, raw in data.items():
        contrast = data["OpenShellEdited.SLDPRT"] if name == "OpenShell.SLDPRT" else b""
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker", name),
                     input=len(raw).to_bytes(8, "little") + raw + contrast, capture_output=True, timeout=60, check=False)
        require(result.returncode == 0 and not result.stderr, result.stderr.decode())
        rows[name] = loads(result.stdout)
    require(all(paths[name].read_bytes() == raw for name, raw in data.items()), "original source changed")
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(dumps({"schema": "kit-sw2026-saved-open-shell-sdk-v1", "native_receipt_sha256": NATIVE_RECEIPT_SHA,
              "native_build": "34.5.2.0604", "fresh_guarded_workers": 3, "published_native_outputs": 0,
              "heldout_credit": 0, "cases": rows}, indent=2, sort_keys=True, allow_nan=False))
        stream.write("\n")


if __name__ == "__main__":
    main()
