from math import isfinite

from EllipseModel import require

ENDPOINTS = ("GetStartPoint2", "GetEndPoint2")
INVENTORIES = ("GetSketchPoints2", "GetSketchPoints")
OPTIONAL = {"ISketchEllipse": ENDPOINTS, "ISketch": INVENTORIES}
POINT_METHODS = {"ISketchPoint": ("GetID", "GetSketch", "X", "Y", "Z", "Type")}


def inspect_api():
    import Swapp
    from EllipseAuthor import installed_api
    from FilletApi import MODEL_LIB, load

    api = installed_api()
    library, model = load(Swapp, MODEL_LIB)
    require(model == api["model"], "ellipse seam registry differs from source authority")
    members = OPTIONAL | POINT_METHODS
    observed = {key: {} for key in members}
    for index in range(library.GetTypeInfoCount()):
        name = library.GetDocumentation(index)[0]
        if name not in members:
            continue
        info = library.GetTypeInfo(index)
        for offset in range(info.GetTypeAttr().cFuncs):
            item = info.GetFuncDesc(offset)
            names = info.GetNames(item.memid)
            if not names or names[0] not in members[name] or item.invkind not in (
                Swapp.pythoncom.INVOKE_FUNC, Swapp.pythoncom.INVOKE_PROPERTYGET,
            ):
                continue
            require(not item.args, f"unexpected registered {name}.{names[0]} parameters")
            observed[name][names[0]] = {"member_id": item.memid, "invoke_kind": item.invkind,
                                        "return": repr(item.rettype)}
    require(set(observed["ISketchPoint"]) == set(POINT_METHODS["ISketchPoint"]),
            "live point identity interfaces were not registered in 34.0")
    return api | {"seam_methods": observed}


def point_row(author, sketch, raw):
    point = author.typed(raw, "SketchPoint")
    owner = author.get(point, "GetSketch")
    coords = author.point(point)
    require(owner is not None and author.same(owner, sketch) and all(map(isfinite, coords)),
            "native point does not belong to the actual finite profile sketch")
    return {"id": author.identity(point), "xyz_m": coords, "point_type": int(author.get(point, "Type"))}


def probe_endpoint(author, sketch, ellipse, registered, method):
    if method not in registered["ISketchEllipse"]:
        return {"status": "unregistered"}
    raw = author.get(ellipse, method)
    if raw is None:
        return {"status": "null"}
    return {"status": "observed", "point": point_row(author, sketch, raw)}


def probe_inventory(author, sketch, registered, method):
    if method not in registered["ISketch"]:
        return {"status": "unregistered"}
    rows = [point_row(author, sketch, raw) for raw in author.get(sketch, method) or ()]
    require(len({tuple(row["id"]) for row in rows}) == len(rows),
            "sketch point inventory repeats a scoped point identity")
    return {"status": "observed", "points": rows}


def observe(author, stage, sketch, ordinary, api):
    segment, = author.get(sketch, "GetSketchSegments") or ()
    require(author.identity(segment) == ordinary["segment_id"], "seam observation lost its actual ellipse member")
    ellipse = author.typed(segment, "SketchEllipse")
    registered = api["seam_methods"]
    endpoints = {name: probe_endpoint(author, sketch, ellipse, registered, name) for name in ENDPOINTS}
    inventories = {name: probe_inventory(author, sketch, registered, name) for name in INVENTORIES}
    row = {"stage": stage, "ellipse": ordinary, "endpoints": endpoints, "inventories": inventories}
    author.rec.data.setdefault("seam_stages", []).append(row)
    author.rec.flush()
    return row
