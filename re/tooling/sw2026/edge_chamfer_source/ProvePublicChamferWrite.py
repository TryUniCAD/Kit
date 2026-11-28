from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from pathlib import Path, PureWindowsPath
import json
import subprocess
from tempfile import TemporaryDirectory
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1]), str(HERE.parents[1] / "edge_fillet_source")]
from ChamferModel import values_si
from FilletModel import AXES, edge_role, stock
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import PlanChmfPart
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDim import ReadChmfDim
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import ChamferFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from VerifySdkCircleEndRegistration import OutputGuard
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

FORMAT = "solidworks.sldprt"
NATIVE = frozenset(("body_structure", "configurations", "editable_sketches",
                    "parameters", "parametric_history", "selections", "support_planes"))
EPOCH = 1795510277


def digest(data):
    return sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def authored(case, side):
    _, bounds = stock(case)
    _, axis, transverse, _, _ = edge_role(case)
    corner = {index: int(case["corner"][AXES[index]] == "max") for index in transverse}
    primary = transverse[side]
    edge = [sum(span) / 2 if index == axis else span[corner[index]] for index, span in enumerate(bounds)]
    face = [span[corner[index]] if index == primary else sum(span) / 2 for index, span in enumerate(bounds)]
    base = MakePlainDoc(case["name"], *case["size_mm"])
    sketch, = base.sketches
    boss, = base.feature_timeline
    body, = base.bodies
    cx, cy = case["center_mm"]

    def translate(point):
        return PlaneVector(point.x + cx, point.y + cy)

    entities = tuple(replace(entity, geometry=LineGeometry(translate(entity.geometry.start),
                                                            translate(entity.geometry.end))) for entity in sketch.entities)
    boss = replace(boss, name="ChamferStockBoss")
    sketch = replace(sketch, name="ChamferStockSketch", entities=entities)
    chamfer = "feature/bevel"
    distance = Parameter("parameter/bevel/distance", "D1",
                         ParameterValue(case["distance_mm"], ValueKind.KLength, "mm"),
                         ParameterRole.KDriving, owner_id=chamfer)
    angle = Parameter("parameter/bevel/angle", "D2", ParameterValue(case["angle_deg"], ValueKind.KAngle, "degree"),
                      ParameterRole.KDriving, owner_id=chamfer)
    selections = tuple(Selection(f"pick/{index}", boss.name + " " + kind, (SelectPathElem("feature", boss.id, kind),),
                                 point=SpaceVector(*(value * 1000.0 for value in point)))
                       for index, (kind, point) in enumerate((("edge", edge), ("distance face", face))))
    feature = FeatureStep(chamfer, "DistanceAngleEdgeChamfer", FeatureKind.KChamfer, 1, (boss.id,),
                          parameter_ids=(distance.id, angle.id),
                          definition=ChamferFeature(distance.value, "distance_angle", angle=angle.value),
                          selection_ids=tuple(item.id for item in selections))
    return replace(base, configurations=(replace(base.configurations[0], name="Default"),),
                   sketches=(sketch,), feature_timeline=(boss, feature), selections=selections,
                   parameters=(*base.parameters, distance, angle),
                   bodies=(replace(body, name=boss.name, final_feature_id=chamfer),))


def refuse(operation, message=None):
    try:
        operation()
    except (TypeError, ValueError, NotFoundError) as error:
        require(message is None or message in str(error), f"wrong refusal: {error}")
    else:
        raise ValueError("unsupported input was accepted")


def pair(document, locator):
    writer = SldprtAdapter()
    values = {"final_destination": locator, "allow_carrier": False, "require_native_transfers": True}
    first, second = BytesIO(), BytesIO()
    config, = document.configurations
    public = write_document(document, first, destination_format=FORMAT, configuration=config.id,
                            allow_carrier=False, values=values)
    direct = writer.write(document, second, WriteOptions(configuration=config.name, values=values))
    data = first.getvalue()
    require(data == second.getvalue() and all(result.vendor_loadable and result.application_usable and not result.dropped
                                               and not result.carrier_capabilities and result.roundtrip_safe
                                               and {item.value for item in result.native_capabilities} == NATIVE
                                               and result.bytes_written == len(data) for result in (direct, public)), "ordinary registry and direct writer differ")
    return data, writer, values


def typed(payload, case):
    archive = SldprtArchive.FromBytes(payload)
    linked = ReadNativeLink(archive, 0, ReadChamfers=True)
    cfg, history = linked.ConfigValue, linked.ResolvedValue
    feature = history.RootsValue[-1]
    drivers = tuple(ReadChmfDim(linked, feature.FieldsValue[owner], angular)
                    for owner, angular in (("f810", False), ("f818", True)))
    require(tuple((row.NameValue, row.ValueSi) for row in drivers) == tuple(zip(("D1", "D2"), values_si(case, False)))
            and len({row.DimensionNode.FieldsValue["f50"] for row in drivers}) == 2, "typed driver readback differs")
    stock = history.RootsValue[-2]
    atom = cfg.RootValue.FieldsValue["fd88"]["atoms"][0]["o"]
    require(stock.FieldsValue["f528"]["items"][0]["o"] is atom is feature.FieldsValue["f538"],
            "shared stock atom did not survive linked decoding")
    replay, graph = WriteResolMut(history.RootsValue, history.ExtraFields, 19000, cfg.MapValue,
                                  history.ContextValue, WriteChamfers=True)
    require(replay == archive.Require(linked.StreamName) and history.MapValue == graph.MapValue
            and WriteConfigMut(cfg.RootValue, 19000, cfg.HeaderValue)[0] == archive.Require(linked.ConfigName),
            "typed linked streams differ under replay")
    return {name: digest(archive.Require(name)) for name in archive.Streams}


def rejected(document, writer, values, case, side):
    boss, feature = document.feature_timeline
    edge, face = document.selections
    _, axis, transverse, _, _ = edge_role(case)
    primary = transverse[side]
    _, bounds = stock(case)
    original = [face.point.x, face.point.y, face.point.z]
    original[primary] = bounds[primary][int(case["corner"][AXES[primary]] == "min")] * 1000.0
    cases = {
        "distance_distance": replace(document, feature_timeline=(boss, replace(feature, definition=replace(feature.definition, mode="two_distances", angle=None, second_distance=feature.definition.distance)))),
        "equal_distance": replace(document, feature_timeline=(boss, replace(feature, definition=replace(feature.definition, mode="equal_distance", angle=None)))),
        "lost_side": replace(document, selections=(edge, replace(face, point=None))),
        "nonincident_face": replace(document, selections=(edge, replace(face, point=SpaceVector(*original)))),
        "crossed_picks": replace(document, feature_timeline=(boss, replace(feature, selection_ids=feature.selection_ids[::-1]))),
        "wrong_driver": replace(document, feature_timeline=(boss, replace(feature, parameter_ids=feature.parameter_ids[::-1]))),
    }
    target = BytesIO(b"unchanged")
    target.seek(2)
    for name, invalid in cases.items():
        refuse(lambda: PlanChmfPart(invalid))
        refuse(lambda: writer.write(invalid, target, WriteOptions(overwrite=True, values=values)))
        require(target.getvalue() == b"unchanged" and target.tell() == 2, f"refused {name} touched output")
    refuse(lambda: writer.write(document, target, WriteOptions(configuration="Other", values=values)),
           "requested chamfer write configuration is unavailable")
    refuse(lambda: writer.write(document, target, WriteOptions()), "explicit final destination")
    require(target.getvalue() == b"unchanged" and target.tell() == 2, "refused options mutated output")
    refuse(lambda: writer.write(document, target, WriteOptions(values=values | {
        "final_destination": str(PureWindowsPath("D:/wrong") / PureWindowsPath(values["final_destination"]).name)
    })), "local C drive")
    return [*cases, "unknown_configuration", "unnamed_stream", "wrong_drive"]


def worker(request):
    external = []
    guard = None

    def inspect(event, args):
        if guard is not None and guard.mode is not None and (event.startswith(("socket.", "ctypes.", "winreg.")) or event in ("os.startfile", "os.startfile/2")):
            external.append(event)
            raise PermissionError("unexpected external access")

    sys.addaudithook(inspect)
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut").ReadTime = lambda: request["epoch"]
    case = request["case"]
    document = authored(case, request["side"])
    wire = document.to_json()
    with TemporaryDirectory(prefix="KitPublicChamfer.") as temporary:
        folder = Path(temporary).resolve()
        filename = PureWindowsPath(request["locator"]).name
        guard = OutputGuard(folder, filename)
        sys.addaudithook(guard.audit)
        with guard.active("memory"):
            document = CadDocument.from_json(wire)
            payload, writer, values = pair(document, request["locator"])
            reordered = replace(document, selections=document.selections[::-1], parameters=document.parameters[::-1])
            require(pair(reordered, request["locator"])[0] == payload, "portable inventory order leaked into driver selection")
            streams = typed(payload, case)
            refusals = rejected(document, writer, values, case, request["side"])
            restored = open_document(BytesIO(payload), source_format=FORMAT, strict=True)
            (finish,) = [step for step in restored.feature_timeline if step.kind == FeatureKind.KChamfer]
            require(restored.brep is not None and len(restored.bodies) == 1
                    and restored.bodies[0].topology.solid_count == 1
                    and isinstance(finish.definition, ChamferFeature)
                    and finish.definition.mode == "distance_angle" and len(finish.parameter_ids) == 2,
                    "strict readback lost the live angle-distance chamfer or its solid")
            logical = str(PureWindowsPath("C:/KitSdkCandidates") / filename)
            local_bytes, _, _ = pair(document, logical)
            require(len(streams) == 10 and document.to_json() == wire, "writer modified the portable model or dropped streams")
        public_path = folder / "registry" / filename
        direct_path = folder / "adapter" / filename
        public_path.parent.mkdir()
        direct_path.parent.mkdir()
        with guard.active("path"):
            public = write_document(document, public_path, configuration="Default", allow_carrier=False)
            direct = writer.write(document, direct_path, WriteOptions(configuration="Default"))
            refuse(lambda: write_document(document, public_path, configuration="Missing", overwrite=True,
                                          allow_carrier=False), "requested chamfer write configuration is unavailable")
        require(public.path == public_path and direct.path == direct_path
                and public_path.read_bytes() == direct_path.read_bytes() == local_bytes
                and tuple(public_path.parent.iterdir()) == (public_path,) and tuple(direct_path.parent.iterdir()) == (direct_path,)
                and not guard.denied and not external,
                "ordinary path writes differ or refused writes touched the output")
        return {"archive_sha256": digest(payload), "bytes": len(payload), "streams": streams,
                "public_path_sha256": digest(local_bytes), "runtime_accesses": 0,
                "replayed_streams": 2, "refusals": refusals, "inventory_order_independent": True,
                "strict_readback": True}


def supervise(trial, native, output):
    raw = trial.read_bytes()
    require(digest(native.read_bytes()) == "d161909999b3ed8d72f0885dbb6dbc0dfa3866e712dc4dd390aef7406c236409",
            "exact successful native signed terminal is absent")
    require(digest(raw) == "8db08a479cd2b3e29dd4d5ad38eec3e96631e0aec15f71868a37aea51d423f49",
            "exact signed constructor trial is absent")
    frozen = json.loads(raw)
    results = []
    for index, (case, reference) in enumerate(zip(frozen["spec"]["cases"], frozen["cases"], strict=True)):
        request = {"case": case, "side": reference["branch"][0], "locator": reference["locator"], "epoch": EPOCH + index * 61}
        process = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                                 input=json.dumps(request).encode(), capture_output=True, check=False)
        require(process.returncode == 0 and not process.stderr, process.stderr.decode())
        result = json.loads(process.stdout)
        expected = reference["writer_proof"]["stream_sha256"]
        require(result["archive_sha256"] == reference["archive_sha256"] == digest((trial.parent / reference["path"]).read_bytes())
                and result["streams"] == expected,
                f"signed disclosed archive differs {result['archive_sha256']} vs {reference['archive_sha256']}: "
                + str({name: [value, expected.get(name)] for name, value in result["streams"].items() if value != expected.get(name)}))
        results.append(result | {"case": case["name"], "reciprocal": reference["reciprocal"]})
    source = ROOT / "src/convert/adapters/solidworks"
    owned = {*(source / "Archive/Construction/Chamfers").glob("*.py"),
             *(source / "Core/Preparation/Chamfers").glob("*.py"),
             *(source / name for name in ("Archive/Construction/Metadata/CheckRevKeys.py",
                "Archive/Construction/Part/EmitPartArchive.py", "Archive/Construction/Part/MakePartKeys.py",
                "Archive/Resolved/WriteResolMut.py", "Core/Preparation/PrepareNative.py", "Core/Writing/CanWritePart.py"))}
    report = {"construction_sources": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(owned)},
              "method_sha256": digest(HERE.read_bytes()), "comparison_manifest_sha256": digest(raw),
              "disclosed_native_receipt_sha256": digest(native.read_bytes()), "candidates": results,
              "guarded_processes": 2, "native_processes": 0, "heldout_inputs_read": 0}
    with output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"sha256": digest(output.read_bytes()), "cases": len(results)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--trial", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    else:
        supervise(args.trial, args.native, args.output)
