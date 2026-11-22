from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path
from subprocess import run
from zlib import ZLIB_RUNTIME_VERSION
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
GENERATED_RECEIPT = "294fe57fc50e8a4968eecf5b33bd9339df30b134857672033016e11b9cdd5c19"
FORMAT = "solidworks.sldprt"
MODEL = ("IndependentColdShell", 61.75, 47.5, 33.25, 3.1, (-12.25, 9.625))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def predicted(case):
    _, width, length, height, wall, (x, y) = case
    inner_width, inner_length, inner_height = width - 2 * wall, length - 2 * wall, height - wall
    stock = width * length * height
    removed = inner_width * inner_length * inner_height
    net = stock - removed
    area = (width * length + height * 2 * (width + length)
            + width * length - inner_width * inner_length
            + inner_width * inner_length + inner_height * 2 * (inner_width + inner_length))
    return (net, area, x, y, (stock * height - removed * (height + wall)) / (2 * net))


def check_document(doc, case, include):
    from convert import write_document
    from interchange.Features.FeatureExtrude import ExtrudeFeature
    from interchange.Features.FeatureKinds import ShellFeature

    features = tuple(step.attributes["native_object_id"] for step in doc.feature_timeline)
    require(features == (*range(1, 20), 26) and not doc.diagnostics,
            "strict read lost the actual twenty ordered feature roots")
    stock, shell = doc.feature_timeline[-2:]
    (pick,), (body,), (sketch,) = doc.selections, doc.bodies, doc.sketches
    require(isinstance(stock.definition, ExtrudeFeature) and stock.definition.end_condition.value == "blind"
            and stock.operation.value == "create" and stock.sketch_id == sketch.id
            and isinstance(shell.definition, ShellFeature) and shell.definition.outward is False
            and shell.input_feature_ids == (stock.id,) and shell.selection_ids == (pick.id,)
            and body.final_feature_id == shell.id and body.attributes["native_atom_id"] == 101,
            "neutral stock, shell or body lineage differs from the typed owners")
    require(len(sketch.entities) == 4 and not sketch.constraints
            and sketch.support_plane_id == "sldprt:plane:14"
            and doc.configurations[0].name == "Default", "free Front sketch or configuration changed")
    require(tuple((row.entity_kind, row.entity_id, row.subelement) for row in pick.path)
            == (("feature", stock.id, "face:1"),) and pick.provenance.spans[0].record_kind == "typed-archive-object",
            "selection is not the real earlier stock cap")
    depth, thickness = doc.parameters
    require((depth.id,) == stock.parameter_ids and (thickness.id,) == shell.parameter_ids
            and stock.definition.length == depth.value and shell.definition.thickness == thickness.value,
            "one of the two live dimension owners was lost")
    owners = []
    for param, feature, value, dimension_id, slot in zip(
        (depth, thickness), (stock, shell), case[3:5], (20, 25), ("f818.f18", "f818"), strict=True
    ):
        owner = param.attributes["typed_archive_owner"]
        require(param.name == "D1" and param.role.value == "driving" and param.owner_id == feature.id
                and param.value.unit == "mm" and isclose(param.value.value, value, rel_tol=1e-15)
                and param.attributes["native_value"] == value * 0.001
                and owner["dimension_id"] == dimension_id and owner["slot"] == slot,
                "wrong linked D1 identity or stored value")
        owners.append(owner)
    require(not ({owners[0][key] for key in ("object_index", "dimension_index", "handle_index", "display_index")}
                 & {owners[1][key] for key in ("object_index", "dimension_index", "handle_index", "display_index")}),
            "stock and shell drivers share an archive owner")
    topology = body.topology
    counts = [topology.solid_count, topology.shell_count, topology.face_count, topology.edge_count, topology.vertex_count]
    values = (topology.volume, topology.surface_area, *body.attributes["solidworks.body_centroid_mm"])
    require(counts == [1, 1, 11, 24, 16] and all(
        isclose(actual, expected, rel_tol=5e-7, abs_tol=1e-10)
        for actual, expected in zip(values, predicted(case), strict=True)
    ), "generated boundary differs from independent box subtraction")
    require((doc.brep is not None) == include and not doc.brep_payloads
            and "parasolid_active_payload_id" not in body.attributes,
            "invalid B-rep options or a fabricated native payload")
    if include:
        geom_body, = doc.brep.bodies
        require(geom_body.design_body_id == body.id and doc.brep.regions[0].solid and doc.brep.shells[0].closed
                and sorted(len(face.loop_ids) for face in doc.brep.faces) == [1] * 10 + [2],
                "the actual ring and cavity are not one closed design solid")
    doc.assert_valid()
    reread = type(doc).from_json(doc.to_json())
    require(reread.feature_timeline[-1].definition == shell.definition and reread.bodies[0].topology == topology
            and reread.selections[0].path == pick.path and reread.parameters[1].value == thickness.value
            and (reread.brep is not None) == include, "inspection JSON lost shell intent or geometry")
    sentinel = b"caller-owned JSON sink"
    destination = BytesIO(sentinel)
    try:
        write_document(doc, destination, destination_format="interchange.json", allow_carrier=False)
    except ValueError as error:
        require("native-only feature definitions cannot be exported" in str(error)
                and destination.getvalue() == sentinel and destination.tell() == 0,
                "public interchange export crossed its native history guard")
    else:
        raise ValueError("public interchange export admitted native-only system history")
    return {"brep": include, "counts": counts, "values": values, "root_count": len(features),
            "drivers": [depth.id, thickness.id], "native_metres": [depth.attributes["native_value"],
                                                                     thickness.attributes["native_value"]],
            "selection": [stock.id, "face:1"], "atom": 101, "inspection_json_roundtrip": True,
            "public_interchange_export_refused": True}


def contrast_streams(raw, change):
    from ReplaySavedShell import replay_manager, replay_resolved
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0, ReadShells=True)
    config, resolved = link.ConfigValue, link.ResolvedValue
    profile = resolved.RootsValue[-3]
    shell = resolved.RootsValue[-1].FieldsValue
    cap = shell["f828"].FieldsValue["items"][0]["o"].FieldsValue["fe8"].FieldsValue
    edge = shell["f848"].FieldsValue["fe8"].FieldsValue
    if change == "saved_atom_stamp":
        shell["f538"].FieldsValue["f1b0"] = 1
        changed = {link.ConfigName: WriteConfigMut(config.RootValue, 19000, config.HeaderValue)[0]}
    elif change == "swapped_manager":
        manager = link.ManagerValue.RootValue
        manager.FieldsValue["f368"] = None
        changed = {"Contents/CMgr": replay_manager(manager)}
    elif change == "foreign_partition":
        changed = {"Contents/Config-1-Partition": b"unqualified geometry stream"}
    elif change == "putative_saved_partition":
        changed = {"Contents/Config-0-Partition": b"unqualified geometry stream"}
    else:
        if change == "crossed_stock":
            points = profile.FieldsValue["pd_f80"].FieldsValue["points"]
            first, other = (row["point"] for row in points[2:])
            first["pos"], other["pos"] = other["pos"], first["pos"]
        elif change == "bottom_as_top":
            cap["f10"][0]["f08"].FieldsValue["f38"] = 0
        elif change == "reordered_auxiliary":
            rows = edge["f10"]
            rows[2], rows[3] = rows[3], rows[2]
        elif change == "different_history_file":
            for row in edge["f10"]:
                history = row["f08"].FieldsValue["f10"]["f10"].FieldsValue
                if row is edge["f10"][0]:
                    file = history["f08"]
                    different_file = ArchiveNode(file.ClassValue, dict(file.FieldsValue))
                history["f08"] = different_file
        elif change == "live_thickness":
            shell["f818"].FieldsValue["f850"][0]["o"].FieldsValue["ff0"].FieldsValue["f28"].FieldsValue["f58"] *= 2.0
        else:
            raise ValueError("unknown transient shell contrast")
        changed = {link.StreamName: replay_resolved(config.MapValue, config.RootValue, resolved)}
    return BuildSldprt(dict(archive.streams) | changed, FormatVersion=4)


def check_refusals(raw):
    from convert import open_document
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
    from interchange.Features.FeatureKinds import NativeFeature

    reasons = {
        "saved_atom_stamp": "body stamp contradicts its partition state",
        "swapped_manager": "alternate configuration or linked body state",
        "foreign_partition": "unqualified physical stream",
        "putative_saved_partition": "stock has unsupported blind end state",
        "bottom_as_top": "removed face is outside the actual stock cap",
        "crossed_stock": "stock contour does not follow the rectangle perimeter",
        "reordered_auxiliary": "ordered stock cap and edge roles",
        "different_history_file": "alternate clip, point or history ownership",
        "live_thickness": "differs from its linked display value",
    }
    for change, why in reasons.items():
        altered = contrast_streams(raw, change)
        for include in (True, False):
            try:
                open_document(altered, source_format=FORMAT, strict=True, include_brep=include)
            except SldprtFormat as error:
                require(why in str(error.__cause__), f"{change} refused for another reason: {error.__cause__}")
            else:
                raise ValueError(f"{change} entered strict shell projection")
        partial = open_document(altered, source_format=FORMAT, strict=False, include_brep=False)
        (step,) = (row for row in partial.feature_timeline if row.kind.value == "shell")
        require(isinstance(step.definition, NativeFeature) and not step.selection_ids
                and any(row.code == "sldprt.shell_history_unresolved" for row in partial.diagnostics),
                f"{change} permissive inspection invented shell intent")
    return reasons


def worker(case, original, expected_hash, probe):
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent.parent), str(HERE.parent)]
    from BuildOpenShellArchives import EPOCH, verify_part
    from BuildOpenShellPlan import document
    from CheckScopedPlainWriter import WriterAudit
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Shells.BuildShellPart import BuildShellPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    for module in ("ReplaySavedShell", "interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)
    name = case[0]
    settings = WriteOptions(values={"final_destination": rf"C:\KitOpenShellGenerated01\Working\{name}.SLDPRT"})
    audit = WriterAudit(ROOT / "src", HERE.parent / "Unused.SLDPRT")
    sys.addaudithook(audit.observe)
    audit.phase = "cold"
    model = document(*case)
    product = BuildShellPart(model, BytesIO(), EPOCH, settings)
    result = verify_part(product, case)
    raw = product.BytesValue
    if original:
        require(sha256(original).hexdigest() == expected_hash and raw == original,
                "the measured reader did not receive exact generated source bytes")
    else:
        require(raw == BuildShellPart(model, BytesIO(), EPOCH, settings).BytesValue,
                "independently varied neutral shell did not regenerate deterministically")
    cases = [
        check_document(open_document(raw, source_format=FORMAT, strict=True, include_brep=include), case, include)
        for include in (True, False)
    ]
    rejections = check_refusals(raw) if probe else {}
    publication = {}
    buffers = {name: BytesIO() for name in ("registry", "direct")}
    for route, publish in (
        ("registry", lambda: write_document(model, buffers["registry"], destination_format=FORMAT,
                                            allow_carrier=False, values=settings.values)),
        ("direct", lambda: SldprtWriter().write(model, buffers["direct"], settings)),
    ):
        try:
            publish()
        except (ValueError, RuntimeError) as error:
            reason = type(error).__name__
            require((route == "registry" and reason == "AdapterNotFoundError")
                    or (route == "direct" and "requires an offline native measurement receipt" in str(error)),
                    f"{route} failed outside the publication guard: {error}")
            publication[route] = reason
        else:
            raise ValueError("unqualified shell reached public writing")
    require(all(not value.getvalue() for value in buffers.values()) and not audit.denied and not audit.target_opens,
            "public refusal wrote to a stream or the guarded worker accessed external data")
    audit.phase = "done"
    return {"source_sha256": result["hash"], "bytes": result["bytes"], "streams": len(result["stream_hashes"]),
            "readback": cases, "refusals": rejections, "strict_refusal_runs": 2 * len(rejections),
            "permissive_refusal_runs": len(rejections), "writer_refusals": publication, "runtime_data_reads": 0,
            "native_process_launches": 0}


def supervise(args):
    if args.model:
        inputs = [(MODEL, b"", None)]
    else:
        sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]
        from BuildOpenShellArchives import CASES

        receipt = (args.generated / "Receipt.json").read_bytes()
        require(sha256(receipt).hexdigest() == GENERATED_RECEIPT, "generated owner receipt differs")
        expected = loads(receipt)["cases"]
        inputs = []
        for case in CASES:
            raw = (args.generated / (case[0] + ".SLDPRT")).read_bytes()
            observed = expected[case[0]]
            require(len(raw) == observed["bytes"] and sha256(raw).hexdigest() == observed["hash"],
                    "generated owner file differs")
            inputs.append((case, raw, observed["hash"]))
    rows = {}
    for index, (case, raw, digest) in enumerate(inputs):
        header = dumps({"case": case, "digest": digest, "probe": index == 0}).encode("utf-8")
        process = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                      input=header + b"\n" + raw, capture_output=True, timeout=60, check=False)
        require(process.returncode == 0 and not process.stderr, process.stderr.decode())
        rows[case[0]] = loads(process.stdout)
    return {"schema": "kit-sw2026-cold-open-shell-sdk-v1", "fresh_guarded_workers": len(rows),
            "format_codec": ZLIB_RUNTIME_VERSION, "generated_authority_sha256": None if args.model else GENERATED_RECEIPT,
            "heldout_credit": 0, "published_native_outputs": 0, "cases": rows}


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generated", type=Path)
    mode.add_argument("--model", action="store_true")
    mode.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        request = loads(sys.stdin.buffer.readline())
        result = worker(request["case"], sys.stdin.buffer.read(), request["digest"], request["probe"])
    else:
        result = supervise(args)
    output = dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
