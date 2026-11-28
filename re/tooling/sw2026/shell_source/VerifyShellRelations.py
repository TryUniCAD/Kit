from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent.parent), str(HERE.parent)]

from BuildOpenShellArchives import EPOCH
from BuildOpenShellPlan import document, require
from CheckColdShellRead import predicted
from CheckSavedShellRead import INPUTS, NATIVE_RECEIPT_SHA
from CheckScopedPlainWriter import WriterAudit
from ReplaySavedShell import replay_resolved
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Preparation.Shells.BuildShellPart import BuildShellPart
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfStock import ReadChmfStock
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import ReadPrismLoop
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.geometry.Models.Selection import SelectPathElem

FORMAT = "solidworks.sldprt"
BASE = "bd3ab078476c403e5615fc1f0eca6b29dd770747"
TEST = ("ShellAxisContrast", 46.125, 59.5, 27.75, 2.65, (6.25, -17.0))
SOURCE_NAMES = (
    "Archive/Construction/Shells/EmitShellPart.py",
    "Archive/Construction/Shells/MakeShellStock.py",
    "Archive/Construction/Shells/OpenShellPlan.py",
    "Core/Preparation/Shells/PlanOpenShell.py",
    "Core/Preparation/Shells/Readback/ReadShellInput.py",
    "Core/Preparation/Shells/ReadShellRect.py",
    "Core/TypedResolved/Chamfers/ReadChmfStock.py",
    "Core/TypedResolved/Shells/BindShellDoc.py",
    "Core/TypedResolved/Shells/Stock/BindShellSketch.py",
    "Core/TypedResolved/Shells/Stock/ReadShellStock.py",
)


def digest(raw):
    return sha256(raw).hexdigest()


def endpoint(geometry, term):
    value = {"start": geometry.start, "end": geometry.end}[term]
    return value.x, value.y


def relation_semantics(sketch):
    by_id = {line.id: line.geometry for line in sketch.entities}
    values = []
    for relation in sketch.constraints:
        refs = tuple((by_id[ref.entity_id], ref.point) for ref in relation.references)
        if relation.kind == "coincident":
            places = [endpoint(line, point) for line, point in refs]
            require(len(places) == 2 and places[0] == places[1], "coincidence changed its actual corner")
        members = [
            (tuple(sorted((endpoint(line, "start"), endpoint(line, "end")))),
             endpoint(line, point) if point else ())
            for line, point in refs
        ]
        require(relation.driving and not relation.suppressed and not relation.parameter_id,
                "selected solver role differs")
        values.append((relation.kind, tuple(sorted(members))))
    require(len(values) == len(set(values)) == 8, "the stock needs eight distinct geometric relations")
    return sorted(values)


def authored(case):
    result = document(*case)
    (sketch,) = result.sketches
    lines = sketch.entities
    axes = tuple(SketchRelation(f"axis:{index}", "horizontal" if index % 2 == 0 else "vertical",
                                (ConstraintRef(line.id),)) for index, line in enumerate(lines))
    corners = tuple(SketchRelation(f"corner:{index}", "coincident", (
        ConstraintRef(first.id, "end"), ConstraintRef(next_line.id, "start")))
        for index, (first, next_line) in enumerate(zip(lines, (*lines[1:], lines[0]), strict=True)))
    return replace(result, sketches=(replace(sketch, constraints=(*axes, *corners)),))


def project(source, name):
    (sketch,) = source.sketches
    stock, shell = source.feature_timeline[-2:]
    depth, wall = source.parameters
    require(sketch.name == "ShellStockSketch" and stock.name == "ShellStockBoss" and shell.name == "OpenShell"
            and stock.parameter_ids == (depth.id,) and shell.parameter_ids == (wall.id,)
            and stock.sketch_id == sketch.id and shell.input_feature_ids == (stock.id,)
            and shell.definition.outward is False and len(source.selections) == 1
            and source.selections[0].path == (SelectPathElem("feature", stock.id, "face:1"),),
            "disclosed warm stock selection or driver identities differ")
    source.assert_valid()
    lo, hi = source.bodies[0].topology.bounding_box.minimum, source.bodies[0].topology.bounding_box.maximum
    case = (name, hi.x - lo.x, hi.y - lo.y, depth.value.value, wall.value.value,
            ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2))
    value = document(*case)
    target = replace(value.sketches[0], closed_profile_entity_ids=sketch.closed_profile_entity_ids,
                     entities=tuple(replace(row, attributes={}, provenance=None) for row in sketch.entities),
                     constraints=tuple(replace(row, attributes={}, provenance=None) for row in sketch.constraints))
    return case, replace(value, sketches=(target,))


def preload():
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)


def reject(action, phrase):
    try:
        action()
    except (ValueError, RuntimeError) as error:
        require(phrase in str(error), f"unexpected refusal: {error}")
        return type(error).__name__
    raise ValueError("unqualified candidate was admitted")


def readback(payload, model, case, options):
    expected = relation_semantics(model.sketches[0])
    results = []
    for include_brep in (False, True):
        source = open_document(payload, source_format=FORMAT, include_brep=include_brep, strict=True)
        (sketch,), (body,), (cap,) = source.sketches, source.bodies, source.selections
        require(relation_semantics(sketch) == expected and len(source.feature_timeline) == 20,
                "strict readback changed an actual axis, join or feature owner")
        require(tuple(row.attributes.get("native_code") for row in sketch.constraints if row.kind != "coincident") == (4, 5, 4, 5),
                "strict readback did not retain the four typed relation records")
        stock, shell = source.feature_timeline[-2:]
        drivers = source.parameters
        require((stock.parameter_ids, shell.parameter_ids) == ((drivers[0].id,), (drivers[1].id,))
                and shell.input_feature_ids == (stock.id,) and body.final_feature_id == shell.id
                and tuple((row.entity_id, row.subelement) for row in cap.path) == ((stock.id, "face:1"),)
                and tuple((row.name, row.role.value) for row in drivers) == (("D1", "driving"),) * 2,
                "shell failed to retain actual stock or thickness drivers")
        require(all(isclose(param.value.value, target, rel_tol=1e-12)
                    for param, target in zip(drivers, case[3:5], strict=True)), "edited driver value differs")
        topology = body.topology
        require((topology.solid_count, topology.shell_count, topology.face_count, topology.edge_count, topology.vertex_count)
                == (1, 1, 11, 24, 16) and (source.brep is not None) is include_brep
                and not source.brep_payloads, "qualified shell boundary differs")
        geometry = (topology.volume, topology.surface_area, *body.attributes["solidworks.body_centroid_mm"])
        require(all(isclose(actual, target, rel_tol=5e-7, abs_tol=1e-10)
                    for actual, target in zip(geometry, predicted(case), strict=True)),
                "shell does not retain the independent shape prediction")
        if include_brep:
            require(source.brep.bodies[0].design_body_id == body.id and source.brep.shells[0].closed,
                    "physical shape lost its actual shell result")
        controls = (source, type(source).from_json(source.to_json()))
        for control in controls:
            require(BuildShellPart(control, BytesIO(), EPOCH, options).BytesValue == payload,
                    "strict shell readback did not regenerate all emitted bytes")
        results.append(digest(source.to_json().encode()))
    return results


def reject_archive(archive, link, stock):
    resolved = link.ResolvedValue
    prefix = replace(link, ResolvedValue=replace(resolved, RootsValue=resolved.RootsValue[:-1]))
    feature_index = IndexFeatures(prefix)
    checks = {"independent_chamfer_stock": reject(
        lambda: ReadChmfStock(link, resolved.RootsValue[-2], feature_index), "actual free rectangular Front stock")}
    first, second = (row["d"] for row in stock.FieldsValue["pd_f80"].FieldsValue["dims"]["log_g1"][:2])
    first["f80"], second["f80"] = second["f80"], first["f80"]
    changed = replay_resolved(link.ConfigValue.MapValue, link.ConfigValue.RootValue, resolved)
    candidate = BuildSldprt(dict(archive.streams) | {link.StreamName: changed}, FormatVersion=4)
    for include_brep in (False, True):
        try:
            open_document(candidate, source_format=FORMAT, include_brep=include_brep, strict=True)
        except SldprtFormat as error:
            require("axis disagrees with its selected line" in str(error.__cause__),
                    "invalid native axis was refused for the wrong cause")
        else:
            raise ValueError("misattached native axes crossed strict inspection")
    checks["swapped_axes_full_and_design"] = "typed axes disagree with the actual selected lines"
    return checks


def worker(name, raw):
    preload()
    audit = WriterAudit(ROOT / "src", HERE.parent / "Unused.SLDPRT")
    sys.addaudithook(audit.observe)
    audit.phase = "cold"
    try:
        warm = None
        if name == "independent":
            case, model = TEST, authored(TEST)
        else:
            require(digest(raw) == INPUTS[name][0], "disclosed native source changed")
            warm = open_document(raw, source_format=FORMAT, include_brep=False, strict=True)
            case, model = project(warm, "ShellRetained" + ("Edited" if "Edited" in name else "Original"))
        locator = rf"C:\KitOpenShellRelations01\Working\{case[0]}.SLDPRT"
        options = WriteOptions(values={"final_destination": locator})
        part = BuildShellPart(model, BytesIO(), EPOCH, options)
        source = SldprtArchive.from_bytes(part.BytesValue)
        require(len(source.streams) == 10 and source.streams == part.StreamsValue,
                "complete shell archive lost a logical stream")
        link = ReadNativeLink(source, 0, ReadShells=True)
        stock = link.ResolvedValue.RootsValue[-3]
        loop = ReadPrismLoop(stock, link)
        require(loop.DimsValue is not None and not loop.DimsValue.DriverValues
                and loop.DimsValue.OriginValue is None and len(loop.DimsValue.AxisValues) == 4,
                "native axis rows were not emitted by the actual sketch owner")
        reads = readback(part.BytesValue, model, case, options)
        checks = reject_archive(source, link, stock) if warm is None else {}
        if warm is not None:
            checks["original_native_source"] = reject(lambda: BuildShellPart(warm, BytesIO(), EPOCH, options),
                                                      "requires its cache-free source")
        else:
            (sketch,) = model.sketches
            axes, joins = sketch.constraints[:4], sketch.constraints[4:]
            wrong = replace(joins[0], references=(joins[0].references[0], joins[1].references[1]))
            invalid = (("missing", (*axes, *joins[1:]), "four axes and four corner coincidences"),
                       ("wrong_join_owner", (*axes, wrong, *joins[1:]), "join all four contour corners"),
                       ("wrong_axis", (replace(axes[0], kind="vertical"), *axes[1:], *joins), "axis relations must match"),
                       ("non_driving_corner", (*axes, replace(joins[0], driving=False), *joins[1:]), "local driving corner"),
                       ("duplicate_corner", (*axes, replace(joins[0], references=joins[1].references), *joins[1:]), " join all four"))
            for label, relations, message in invalid:
                invalid_model = replace(model, sketches=(replace(sketch, constraints=relations),))
                checks[label] = reject(lambda: BuildShellPart(invalid_model, BytesIO(), EPOCH, options), message)
        for route, publish, reason in (
            ("registry", lambda sink: write_document(model, sink, destination_format=FORMAT, allow_carrier=False, values=options.values),
             "solidworks.sldprt does not support the destination"),
            ("direct", lambda sink: SldprtWriter().write(model, sink, options), "requires an offline native measurement receipt"),
        ):
            sink = BytesIO(b"owned sink")
            checks[route] = reject(lambda: publish(sink), reason)
            require(sink.getvalue() == b"owned sink" and sink.tell() == 0, "public refusal wrote output")
        require(not audit.denied and not audit.target_opens, "guarded runtime read data or opened a destination")
    finally:
        audit.phase = "done"
    return part.BytesValue, {"source_sha256": digest(raw) if raw else None, "candidate_sha256": digest(part.BytesValue),
                            "bytes": len(part.BytesValue), "logical_locator": locator, "publications": 0,
                            "reads": reads, "exact_regenerations": 4, "native_launches": 0, "runtime_file_reads": 0,
                            "axis_rows": 4, "selected_corner_pairs": 4, "refusals": checks,
                            "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in source.streams.items()}}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosure", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", choices=(*INPUTS, "independent"))
    args = parser.parse_args()
    if args.worker:
        raw, report = worker(args.worker, sys.stdin.buffer.read())
        print(dumps(report | {"candidate_hex": raw.hex()}, sort_keys=True))
        return
    require(args.disclosure and args.output and not args.output.exists()
            and not args.output.resolve().is_relative_to(ROOT), "choose the disclosure and a new result directory outside Kit")
    root = args.disclosure.resolve(strict=True)
    receipt = root / "Receipt.json"
    require(root.name == "Disclosure" and not receipt.is_symlink() and digest(receipt.read_bytes()) == NATIVE_RECEIPT_SHA,
            "native disclosure does not match its exact public receipt")
    sources = {name: root / name for name in INPUTS}
    require(all(not path.is_symlink() for path in sources.values()), "disclosed native inputs must be regular files")
    rows = tuple((name, path.read_bytes()) for name, path in sources.items()) + (("independent", b""),)
    observed = {}
    payloads = {}
    for name, raw in rows:
        outcome = run((sys.executable, "-I", "-B", str(HERE), "--worker", name), input=raw,
                      capture_output=True, check=False, timeout=60)
        require(outcome.returncode == 0 and not outcome.stderr, outcome.stderr.decode())
        result = loads(outcome.stdout)
        payloads[name] = bytes.fromhex(result.pop("candidate_hex"))
        require(digest(payloads[name]) == result["candidate_sha256"], "worker result transport differs")
        observed[name] = result
    require(all(digest(path.read_bytes()) == INPUTS[name][0] for name, path in sources.items()),
            "native disclosed source changed during proof")
    require(len({row["candidate_sha256"] for row in observed.values()}) == len(observed), "different input geometry retained one output")
    args.output.mkdir(exist_ok=False)
    for name, result in observed.items():
        target = args.output / (result["logical_locator"].rsplit("\\", 1)[-1])
        with target.open("xb") as stream:
            stream.write(payloads[name])
    with (args.output / "Receipt.json").open("x", encoding="utf-8") as stream:
        source_root = ROOT / "src/convert/adapters/solidworks"
        stream.write(dumps({"schema": "kit.sw2026.open-shell-relations.v1", "base": BASE,
                            "scoped_source_sha256": {name: digest((source_root / name).read_bytes()) for name in SOURCE_NAMES},
                            "guard_tool_sha256": digest(HERE.read_bytes()), "source_lock_sha256": NATIVE_RECEIPT_SHA,
                            "heldout_source_reads": 0, "native_publications": 0, "workers": len(observed),
                            "native_launches": 0, "cases": observed}, sort_keys=True, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
