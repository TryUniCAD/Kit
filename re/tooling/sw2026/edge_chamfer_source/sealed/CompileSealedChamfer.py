from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from math import isfinite
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
FAMILY = HERE.parent.parent
RESEARCH = FAMILY.parent
ROOT = RESEARCH.parents[2]
sys.path[:0] = [str(path) for path in (ROOT, ROOT / "src", RESEARCH, RESEARCH / "serial", FAMILY)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(RESEARCH / "serial/defs")
sys.addaudithook(audit.InspectEvent)
external = []


def inspect_external(event, args):
    if event.startswith(("socket.", "ctypes.", "winreg.")) or event in ("os.startfile", "os.startfile/2"):
        external.append(event)
        raise PermissionError("compiler requested external access: " + event)


sys.addaudithook(inspect_external)

from LinkChamferGraph import build_graph, emit_cold, write_roots
from ProveChamferEdgeOwners import check_owners, digest, require
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream, KResolvedFeaturesStream
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDim import ReadChmfDim
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc


def neutral_part(request, center):
    require(type(center) is list and len(center) == 2
            and all(type(value) in (int, float) and isfinite(value) and abs(value) < 70 for value in center),
            "neutral stock requires two finite sketch-plane origin coordinates")
    document = MakePlainDoc(request["case"], *request["size_mm"])
    sketch, = document.sketches

    def translated(point):
        return PlaneVector(point.x + center[0], point.y + center[1])

    entities = tuple(replace(entity, geometry=LineGeometry(translated(entity.geometry.start),
                                                           translated(entity.geometry.end)))
                     for entity in sketch.entities)
    return replace(document, configurations=(replace(document.configurations[0], name="Default"),),
                   sketches=(replace(sketch, name="ChamferStockSketch", entities=entities),),
                   feature_timeline=(replace(document.feature_timeline[0], name="ChamferStockBoss"),),
                   bodies=(replace(document.bodies[0], name="ChamferStockBoss"),))


def compile_part(data):
    wire = json.loads(data)
    require(type(wire) is dict and set(wire) == {"request", "origin_mm"}, "compiler requires only modeled neutral input")
    request = wire["request"]
    stock = neutral_part(request, wire["origin_mm"])
    candidate, bevel, atom, drivers, selection, locator = build_graph(stock, request)
    check_owners(bevel, atom, candidate.SystemValue.RootValue, expected_file=locator, cold=True)
    raw, streams, seed, terminal = emit_cold(candidate, bevel, drivers)
    archive = SldprtArchive.from_bytes(raw)
    require(len(streams) == 10 and KPartitionStream not in archive.streams
            and all(archive.require(name) == value for name, value in streams.items()),
            "cold container differs from ten independently generated streams")
    link = ReadNativeLink(archive, 0, ReadChamfers=True)
    config, resolved = link.ConfigValue, link.ResolvedValue
    replay, end = write_roots(resolved.RootsValue, resolved.ExtraFields, config.MapValue, resolved.ContextValue)
    require(WriteConfigMut(config.RootValue, 19000, config.HeaderValue)[0] == archive.require("Contents/Config-0")
            and replay == archive.require(KResolvedFeaturesStream) and resolved.MapValue == end
            and config.MapValue.CounterValue == seed and end.CounterValue == terminal
            and resolved.ExtraFields == {"n": 0, "fcd8": []},
            "the actual linked graph failed exact Config and Resolved replay")
    real_stock, feature = resolved.RootsValue[-2:]
    real_atom = config.RootValue.FieldsValue["fd88"]["atoms"][0]["o"]
    require(real_stock.FieldsValue["f528"]["items"][0]["o"] is real_atom is feature.FieldsValue["f538"]
            and feature.FieldsValue["f8c8"] == {"n": 0, "items": []},
            "reader lost the independent stock producer or exact ordinary options")
    check_owners(feature, real_atom, config.RootValue, cold=True)
    actual = [ReadChmfDim(link, feature.FieldsValue[owner], angular)
              for owner, angular in (("f810", False), ("f818", True))]
    ids = [driver.DimensionNode.FieldsValue["f50"] for driver in actual]
    require([driver.NameValue for driver in actual] == ["D1", "D2"]
            and [driver.ValueSi for driver in actual] == [request["shape"][key] for key in ("distance_m", "angle_rad")]
            and ids == [driver.DimensionValue.FieldsValue["f50"] for driver in drivers]
            and ids[0] < ids[1] < feature.FieldsValue["f08"], "readback lost the ordered distinct live chamfer drivers")
    require(not audit.DeniedReads and not external, "construction attempted a runtime input or process access")
    return {"schema": "kit.sw2026.sealed-chamfer-compiler.v1", "intent_sha256": digest(data),
            "archive_sha256": digest(raw), "archive_bytes": len(raw), "streams": len(streams),
            "linked_streams_exact": 2, "runtime_accesses": 0, "driver_count": len(ids),
            "selected_endpoints_m": selection.endpoints, "model_base64": b64encode(raw).decode("ascii")}


if __name__ == "__main__":
    tuple(lookup(name) for name in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"))
    audit.BeginBuild()
    data = sys.stdin.buffer.read(65537)
    require(not sys.argv[1:] and 0 < len(data) <= 65536, "invalid sole stdin neutral request")
    print(json.dumps(compile_part(data), sort_keys=True, allow_nan=False))
