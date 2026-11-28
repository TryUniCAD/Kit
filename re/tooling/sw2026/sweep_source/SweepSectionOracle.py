from math import hypot, pi
from pathlib import Path
from time import time

from AuthorCurves import Recorder, digest, require
from AuthorImportedBody import ImportedBodyAuthor, SHEET, SOLID
from FilletApi import MODEL_LIB, load
from ObserveCylinderExchange import loop_rims, measure_circle, measure_extrema, number, numeric_values
from RunImportedBodySources import oracle_identity


ORIGIN = (0.0, 0.0, 0.0)
NORMAL = (1.0, 0.0, 0.0)
POSITION = 1e-10
STRUCTURE = {
    "IModelDoc2": ("InsertPlanarRefSurface",),
    "ISldWorks": ("LoadFile4",),
    "IFace2": ("GetArea",),
    "ISurface": ("PlaneParams",),
}


def registration(sw):
    library, information = load(sw, MODEL_LIB)
    tables = {}
    for index in range(library.GetTypeInfoCount()):
        name = library.GetDocumentation(index)[0]
        if name not in STRUCTURE:
            continue
        info = library.GetTypeInfo(index)
        signatures = {}
        for slot in range(info.GetTypeAttr().cFuncs):
            member = info.GetFuncDesc(slot)
            names = info.GetNames(member.memid)
            if names and names[0] in STRUCTURE[name]:
                signatures.setdefault(names[0], []).append({
                    "member_id": member.memid, "invoke_kind": member.invkind,
                    "names": list(names), "arguments": repr(member.args), "return": repr(member.rettype),
                })
        require(signatures.keys() == set(STRUCTURE[name]), f"unavailable installed sheet API on {name}")
        tables[name] = signatures
    require(tables.keys() == STRUCTURE.keys(), "incomplete installed sheet API")
    return {"type_library": information, "interfaces": tables}


def measure_seam(observer, vertices, edge, radius):
    require(len(vertices) in (0, 1), "one periodic rim has an unsupported vertex inventory")
    endpoints = tuple(observer.get(edge, name) for name in ("GetStartVertex", "GetEndVertex"))
    if not vertices:
        require(endpoints == (None, None), "vertex-free rim exposes an unowned endpoint")
        return None
    vertex = observer.typed(vertices[0], "Vertex")
    for endpoint in endpoints:
        observer.exact_object(endpoint, vertex, "both periodic endpoints use the body seam")
    point = numeric_values(observer.get(vertex, "GetPoint"), 3, "rim seam point")
    number(observer, "seam station", point[0], 0.0, POSITION)
    number(observer, "seam radius", hypot(*point[1:]), radius, POSITION)
    return point


def measure_disk(observer, radius):
    part = observer.typed(observer.model, "PartDoc")
    bodies = tuple(observer.get(part, "GetBodies2", SHEET, False) or ())
    require(len(bodies) == 1 and not observer.get(part, "GetBodies2", SOLID, False),
            "document does not hold one exclusive sheet")
    body = observer.typed(bodies[0], "Body2")
    require(int(observer.get(body, "GetType")) == SHEET and not observer.get(body, "IsTemporaryBody"),
            "body does not have the persistent sheet kind")
    faces = tuple(observer.get(body, "GetFaces") or ())
    edges = tuple(observer.get(body, "GetEdges") or ())
    vertices = tuple(observer.get(body, "GetVertices") or ())
    require(len(faces) == len(edges) == 1, "disk lacks its single face and rim")
    face = observer.typed(faces[0], "Face2")
    edge = observer.typed(edges[0], "Edge")
    observer.exact_object(observer.get(face, "GetBody"), body, "disk face owned by inspected sheet")
    require(loop_rims(observer, face, {0: edge}, 1) == (0,), "disk loop does not bind the actual rim")
    surface = observer.typed(observer.get(face, "GetSurface"), "Surface")
    require(bool(observer.get(surface, "IsPlane")), "disk has a nonplanar carrier")
    plane = numeric_values(observer.get(surface, "PlaneParams"), 6, "disk plane")
    number(observer, "plane X normal", abs(plane[0]), 1.0, 1e-9)
    for value in plane[1:3]:
        number(observer, "plane transverse normal", value, 0.0, 1e-9)
    number(observer, "plane station", plane[3], 0.0, POSITION)
    area = float(observer.get(face, "GetArea"))
    number(observer, "disk area", area, pi * radius * radius, 1e-18, relative=2e-7)
    _, circle = measure_circle(observer, edge, (ORIGIN, ORIGIN), NORMAL, radius)
    require(int(observer.get(observer.get(observer.model, "Extension"), "GetWhatsWrongCount")) == 0,
            "sheet document reports native diagnostics")
    return {"sheets": 1, "faces": 1, "edges": 1, "vertices": len(vertices), "circle": circle, "plane": plane,
            "area_m2": area, "seam_m": measure_seam(observer, vertices, edge, radius),
            "bounds_m": measure_extrema(observer, body, ((0.0, -radius, -radius), (0.0, radius, radius)))}


def author_disk(observer, radius):
    get, model = observer.get, observer.model
    extension = get(model, "Extension")
    require(get(extension, "SelectByID2", "Right Plane", "PLANE", *ORIGIN, False, 0, observer.sw.nothing(), 0),
            "control cannot select its native Right plane")
    manager = get(model, "SketchManager")
    get(manager, "InsertSketch", True)
    require(get(manager, "ActiveSketch") is not None, "control cannot start its circle sketch")
    observer.set(manager, "AddToDB", True)
    try:
        segment = get(manager, "CreateCircleByRadius", *ORIGIN, radius)
    finally:
        observer.set(manager, "AddToDB", False)
    arc = observer.typed(segment, "SketchArc")
    require(bool(get(arc, "IsCircle")) and not get(segment, "ConstructionGeometry"), "control circle is not ordinary")
    number(observer, "native sketch radius", float(get(arc, "GetRadius")), radius, POSITION)
    get(manager, "InsertSketch", True)
    require(get(manager, "ActiveSketch") is None, "control circle sketch remains open")
    sketch = get(model, "FeatureByPositionReverse", 0)
    require(sketch is not None and get(sketch, "GetTypeName2") == "ProfileFeature", "control lost its sketch feature")
    get(model, "ClearSelection2", True)
    require(get(extension, "SelectByID2", get(sketch, "Name"), "SKETCH", *ORIGIN,
                False, 1, observer.sw.nothing(), 0), "control cannot mark its exact boundary sketch")
    selection = get(model, "SelectionManager")
    require(get(selection, "GetSelectedObjectCount2", -1) == get(selection, "GetSelectedObjectCount2", 1) == 1,
            "control lacks a single mark-one boundary")
    require(bool(get(model, "InsertPlanarRefSurface")), "registered planar surface authoring failed")
    observer.rebuild()


def export_phase(directory, role, radius):
    import Swapp
    from OracleIdentity import application_identity

    rec = Recorder(directory / (role + ".json"), {"case": role, "radius_m": radius})
    result, controller, observer = {"passed": False}, None, None
    artifact = directory / (role + "Disk.x_b")
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle oracle", Swapp.sweep)
            controller = rec.call("launch native disk author", Swapp.Sw)
            result["oracle_identity"] = oracle_identity(rec.call("bind native disk oracle", application_identity, controller.app))
            require(controller.revision == Swapp.EXPECTED_BUILD, "native disk author revision differs")
            result["api"] = rec.call("bind installed sheet APIs", registration, Swapp)
            template = Path(rec.call("read native part template", controller.template)).resolve(strict=True)
            result["source_template_sha256"] = digest(template)
            observer = ImportedBodyAuthor(controller.app, rec, Swapp)
            observer.model = rec.call("create standalone native disk control", controller.new_part)
            author_disk(observer, radius)
            result["authored"] = measure_disk(observer, radius)
            require(not artifact.exists(), "control export already exists")
            status = rec.call("export native binary disk control", controller.save_as, observer.model, artifact)
            require(status == (True, 0, 0) and artifact.is_file() and artifact.stat().st_size > 0,
                    "control sheet export failed or warned")
            result["export"] = {"sha256": digest(artifact), "bytes": artifact.stat().st_size}
            require(digest(template) == result["source_template_sha256"], "native author template changed")
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    if observer is not None and observer.model is not None:
                        controller.close_doc(observer.model)
                except Exception as error:
                    rec.failure(error, cleanup=True)
                finally:
                    try:
                        controller.close()
                    except Exception as error:
                        rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress, first_failure=rec.data["first_failure"],
                  numeric_checks=len(rec.data["checks"]))
    result["passed"] = bool(result["passed"] and not dialogs.log and not result.get("controller_diagnostics")
                            and not rec.data["first_failure"] and not rec.data["cleanup_errors"])
    rec.data.update(result=result, passed=result["passed"], finished_at=time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}
