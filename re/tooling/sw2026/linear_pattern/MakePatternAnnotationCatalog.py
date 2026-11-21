from math import isfinite

from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import IdentityXform
from convert.adapters.solidworks.Archive.Construction.Views.MakeViewNode import MakeViewNode
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadRows, RequireNode

from PatternPlaneDirectionRule import cross, dot


UNASSIGNED_ANNOTATIONS = 199
WORLD = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def annotation_frame(value):
    require(isinstance(value, (tuple, list)) and len(value) == 3
            and all(isinstance(axis, (tuple, list)) and len(axis) == 3 for axis in value),
            "annotation frame requires three explicit signed model axes")
    bases = tuple(tuple(axis) for axis in value)
    require(all(type(entry) is float and isfinite(entry) and entry in (-1.0, 0.0, 1.0)
                for axis in bases for entry in axis)
            and all(dot(axis, axis) == 1.0 for axis in bases) and cross(*bases[:2]) == bases[2],
            "annotation frame requires a right-handed model-axis rotation")
    if bases == WORLD:
        return IdentityXform()
    return {**IdentityXform(), "has_matrix": 1,
            "f08": {f"m{3 * row + column}": bases[column][row] for row in range(3) for column in range(3)}}


def annotation_node(name, basis, identity):
    require(type(name) is str and name and "\x00" not in name, "annotation view needs an explicit authored name")
    fields = MakeViewNode(name, identity, None).FieldsValue
    fields.update(f368=annotation_frame(basis), f3d8=0, f3d0=None, f3f0=0, f3e0=0.0, f3e8=None, f3f4=0,
                  f3f8=1, f2f0=None, f3fc=-1, f408=0, f400=-1, f404=-1)
    return ArchiveNode(RuntimeClass("moAnnotationView_c", 1), fields)


def add_catalog_mut(model, intents, active, shown, *, version):
    fields = RequireNode(model, "moPart_c").FieldsValue
    catalog = RequireNode(fields["fa48"], "suObList").FieldsValue
    require(version == 19000 and fields["fb4"] == 0 and catalog["n"] == 0 and not catalog["items"]
            and fields["feb0"] == fields["feb4"] == UNASSIGNED_ANNOTATIONS and fields["nec8"] == 0 and not fields["fec0"],
            "research annotation registration requires the empty ordinary part catalog")
    require(isinstance(intents, (tuple, list)) and 1 <= len(intents) <= 3 and isinstance(shown, (tuple, list)),
            "expected an ordered bounded catalog and explicit shown view roles")
    views = {}
    for intent in intents:
        require(type(intent) is dict and set(intent) == {"name", "basis"}, "unknown authored annotation view fields")
        view = annotation_node(intent["name"], intent["basis"], fields["feb0"] + len(views) + 1)
        require(intent["name"] not in views, "ambiguous authored annotation view names")
        views[intent["name"]] = view
    ids = {name: node.FieldsValue["f360"] for name, node in views.items()}
    ids[None] = UNASSIGNED_ANNOTATIONS
    selected_ids = tuple(lookup_id(ids, name) for name in shown)
    require(len(selected_ids) == len(set(selected_ids)), "ambiguous shown annotation membership")
    active_id = lookup_id(ids, active)
    catalog.update(n=len(views), items=tuple({"o": node} for node in views.values()))
    fields.update(feb0=fields["feb0"] + len(views), feb4=active_id, nec8=len(selected_ids),
                  fec0=tuple({"v": identity} for identity in sorted(selected_ids)))
    return views


def lookup_id(catalog, name):
    require((type(name) is str or name is None) and name in catalog, "annotation membership names no registered view")
    return catalog[name]


def display_membership(model, name):
    root = RequireNode(model, "moPart_c").FieldsValue
    catalog = RequireNode(root["fa48"], "suObList").FieldsValue
    views = tuple(RequireNode(row["o"], "moAnnotationView_c").FieldsValue for row in ReadRows(catalog["items"]))
    ids = [view["f360"] for view in views]
    require(catalog["n"] == len(views) == len(set(ids)) and ids
            and min(ids) > UNASSIGNED_ANNOTATIONS and max(ids) == root["feb0"], "angular display cannot join an invalid annotation catalog")
    matches = [view for view in views if view["f358"] == name]
    require(type(name) is str and len(matches) == 1, "angular display requires one actual authored annotation view")
    view = matches[0]
    return {"n2b0": 1, "f2b0": ({"v": view["f360"]},)}
