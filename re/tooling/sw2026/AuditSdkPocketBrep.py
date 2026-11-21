from hashlib import sha256
from json import dumps, load
from math import isclose, pi
from pathlib import Path
from os import getpid
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AuditSdkPocketRead import check_document, require

from convert import open_document
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface


def main(request):
    path = Path(request["path"])
    payload = path.read_bytes()
    require(sha256(payload).hexdigest() == request["source_sha256"], "pocket input differs from its lock")
    mode = request["mode"]
    require(mode in ("path", "bytes"), "expected path or byte read")
    document = open_document(path if mode == "path" else payload,
                             source_format="solidworks.sldprt")
    semantic = check_document(document, request["expectation"])
    model = document.brep
    body, = document.bodies
    require(model is not None and not model.validate(frozenset((body.id,))),
            "default pocket reading did not produce a valid design-body boundary")
    counts = len(model.bodies), len(model.faces), len(model.edges), len(model.vertices)
    require(counts == (1, 8, 14, 10) and len(model.shells) == 1 and model.shells[0].closed,
            "pocket does not have the measured closed solid inventory")
    surfaces = {row.id: row for row in model.surfaces}
    cylindrical_face, = [face for face in model.faces if isinstance(surfaces[face.surface_id], CylinderSurface)]
    annular_face, = [face for face in model.faces
                    if isinstance(surfaces[face.surface_id], PlaneSurface) and len(face.loop_ids) == 2]
    require(len(cylindrical_face.loop_ids) == 2 and len(annular_face.loop_ids) == 2
            and sum(isinstance(row, PlaneSurface) for row in model.surfaces) == 7,
            "cavity lost its inner wall, floor or annular inlet")
    radius = surfaces[cylindrical_face.surface_id].radius
    require(isclose(radius, request["expectation"]["radius_mm"], rel_tol=1e-10),
            "cylindrical wall uses a different radius")
    derived = tuple(item for item in document.diagnostics if item.code == "sldprt.brep_reconstructed")
    if request["expectation"]["binding"] == "cold_all_bodies_intersection":
        require(not document.brep_payloads and len(derived) == 1
                and derived[0].attributes["method"] == "typed_parametric_blind_circular_pocket",
                "cache-free pocket did not derive its own boundary")
        info, expected = body.topology, request["physical"]
        volume_m3, area_m2 = info.volume * 1e-9, info.surface_area * 1e-6
        require(isclose(volume_m3, expected["volume_m3"], rel_tol=1e-10)
                and isclose(area_m2, expected["area_m2"], rel_tol=1e-10),
                "computed pocket measures differ from the native oracle")
        bounds = info.bounding_box
        require(bounds is not None and all(
            isclose(a, b, rel_tol=1e-10, abs_tol=1e-8) for a, b in zip(
                (bounds.minimum.x, bounds.minimum.y, bounds.minimum.z,
                 bounds.maximum.x, bounds.maximum.y, bounds.maximum.z),
                request["bounds_mm"], strict=True)),
                "computed blind cavity changed the stock bounds")
        low, high = sorted((row.center for row in model.curves if isinstance(row, CircleCurve)),
                           key=lambda point: point.z)
        stock_min, stock_max = bounds.minimum, bounds.maximum
        require(not cylindrical_face.same_sense and low.z == stock_min.z
                and (low.x, low.y) == (high.x, high.y) and low.z < high.z < stock_max.z,
                "the inlet and recess must bound the measured inward cavity")
        stock_volume = ((stock_max.x - stock_min.x) * (stock_max.y - stock_min.y)
                        * (stock_max.z - stock_min.z))
        cavity_volume = pi * radius**2 * (high.z - low.z)
        stock_centre = tuple((getattr(stock_min, a) + getattr(stock_max, a)) / 2.0 for a in "xyz")
        cavity_centre = (low.x, low.y, (low.z + high.z) / 2.0)
        centre_m = [(stock_volume * a - cavity_volume * b) / (stock_volume - cavity_volume) / 1000
                    for a, b in zip(stock_centre, cavity_centre, strict=True)]
        require(all(isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
                    for a, b in zip(centre_m, expected["com_m"], strict=True)),
                "the cavity boundary's analytic centre differs from the native oracle")
        evidence = {"volume_m3": volume_m3, "area_m2": area_m2,
                    "com_m": centre_m, "boundary_source": "typed_history"}
    else:
        require(not derived and document.brep_payloads, "existing native partition geometry was replaced")
        evidence = {"boundary_source": "native_partition"}
    return {"passed": True, "process_id": getpid(), "source_sha256": document.source.sha256,
            "mode": mode, "topology": counts, "annular_inlet": True, "radius_mm": radius,
            "cut_history": semantic, **evidence}


if __name__ == "__main__":
    print(dumps(main(load(sys.stdin)), sort_keys=True, allow_nan=False))
