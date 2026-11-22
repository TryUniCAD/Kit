from argparse import ArgumentParser
from base64 import b64encode
from dataclasses import replace
from json import dumps, loads
from pathlib import Path, PureWindowsPath
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(path) for path in (ROOT, ROOT / "src", HERE.parent,
                                     HERE.parents[1], HERE.parents[2] / "edge_fillet_source",
                                     HERE.parents[2])]

from ObservePairArchives import guard, identity, require
from RunChamferPair import CASES
from FilletModel import AXES, edge_role, stock
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import ReadPrismParam
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
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
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc


def authored(case, side):
    _, bounds = stock(case)
    _, along, transverse, _, _ = edge_role(case)
    primary = transverse[side]
    corner = {index: int(case["corner"][AXES[index]] == "max") for index in transverse}
    edge = [sum(span) / 2 if index == along else span[corner[index]] for index, span in enumerate(bounds)]
    face = [span[corner[index]] if index == primary else sum(span) / 2 for index, span in enumerate(bounds)]
    base = MakePlainDoc(case["name"], *case["size_mm"])
    sketch, = base.sketches
    boss, = base.feature_timeline
    body, = base.bodies
    x, y = case["center_mm"]

    def translate(point):
        return PlaneVector(point.x + x, point.y + y)

    geometry = tuple(replace(entity, geometry=LineGeometry(translate(entity.geometry.start),
                                                            translate(entity.geometry.end)))
                     for entity in sketch.entities)
    boss = replace(boss, name="ChamferStockBoss")
    sketch = replace(sketch, name="ChamferStockSketch", entities=geometry)
    bevel_id = "feature/bevel"
    names = ("D1",) if case["equal"] else ("D1", "D3")
    drivers = tuple(Parameter("parameter/bevel/" + name, name,
                              ParameterValue(distance, ValueKind.KLength, "mm"),
                              ParameterRole.KDriving, owner_id=bevel_id)
                    for name, distance in zip(names, case["distances_mm"][:len(names)], strict=True))
    selections = tuple(Selection(f"pick/{index}", boss.name + " " + kind,
                                 (SelectPathElem("feature", boss.id, kind),),
                                 point=SpaceVector(*(value * 1000 for value in point)))
                       for index, (kind, point) in enumerate((("edge", edge), ("distance face", face))))
    second = None if case["equal"] else drivers[1].value
    kind = "equal_distance" if case["equal"] else "two_distances"
    feature = FeatureStep(bevel_id, "DistancePairEdgeChamfer", FeatureKind.KChamfer, 1, (boss.id,),
                          parameter_ids=tuple(driver.id for driver in drivers),
                          definition=ChamferFeature(drivers[0].value, kind, second_distance=second),
                          selection_ids=tuple(item.id for item in selections))
    return replace(base, configurations=(replace(base.configurations[0], name="Default"),),
                   sketches=(sketch,), feature_timeline=(boss, feature), selections=selections,
                   parameters=(*base.parameters, *drivers),
                   bodies=(replace(body, name=boss.name, final_feature_id=bevel_id),))


def compile_document(request):
    require(request.keys() == {"document", "epoch", "locator"} and type(request["epoch"]) is int,
            "distance-pair compiler expects a full authored neutral document, time and locator")
    from io import BytesIO

    doc = CadDocument.from_json(dumps(request["document"]))
    settings = WriteOptions(values={"final_destination": request["locator"]})
    denied = guard()
    candidate = PrepChmfPart(doc, BytesIO(), request["epoch"], settings, AllowDistancePair=True)
    raw = candidate.BytesValue
    archive = SldprtArchive.from_bytes(raw)
    linked = ReadNativeLink(archive, 0, ReadChamfers=True)
    config, resolved = linked.ConfigValue, linked.ResolvedValue
    feature = resolved.RootsValue[-1].FieldsValue
    fields = ("f810",) if feature["f8c0"] == 18 else ("f810", "f820")
    values = [ReadPrismParam(feature[field], False) for field in fields]
    driving = [(ReadNativeName(param), value, dim.FieldsValue["f50"]) for dim, param, value in values]
    source = doc.feature_timeline[-1]
    authored_values = [(p.name, p.value.value / 1000.0) for p in doc.parameters if p.id in source.parameter_ids]
    require([(name, value) for name, value, _ in driving] == authored_values
            and len({identity for _, _, identity in driving}) == len(driving)
            and feature["f818"] is None and len(archive.streams) == 10,
            "fresh pair lost a modeled driving owner")
    rebuilt, graph = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    wire, tail = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, graph.MapValue,
                              resolved.ContextValue, WriteChamfers=True)
    require(rebuilt == archive.require(linked.ConfigName) and wire == archive.require(linked.StreamName)
            and tail.MapValue.CounterValue == resolved.MapValue.CounterValue and not denied,
            "candidate failed exact guarded archive re-emission")
    return {"schema": "kit.sw2026.distance-pair-neutral-compiler.v1", "archive_sha256": identity(raw),
            "archive_bytes": len(raw), "mode_word": feature["f8c0"], "drivers": driving, "config_map": config.MapValue.CounterValue,
            "resolved_map": resolved.MapValue.CounterValue, "runtime_external_reads": len(denied),
            "streams": {lane: identity(archive.require(lane)) for lane in archive.streams},
            "archive": b64encode(raw).decode("ascii")}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", choices=("equal", "unequal"))
    parser.add_argument("--guest-root")
    parser.add_argument("--epoch", type=int)
    args = parser.parse_args()
    if args.disclosed is not None:
        require(args.guest_root and args.epoch is not None, "disclosed intent needs a native root and epoch")
        slot = int(args.disclosed == "unequal")
        case = CASES[slot]
        target = PureWindowsPath(args.guest_root) / (case["name"] + ".SLDPRT")
        document = authored(case, slot)
        print(dumps({"document": document.to_dict(), "epoch": args.epoch, "locator": str(target)},
                    sort_keys=True, allow_nan=False))
        return
    request = loads(sys.stdin.buffer.read(65537))
    print(dumps(compile_document(request), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
