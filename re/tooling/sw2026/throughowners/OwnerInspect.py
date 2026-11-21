from math import hypot, isclose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from OwnerDto import require


def array(value, cls=None):
    require(type(value) is dict and value["n"] == len(value["items"]), "owner array has inconsistent count")
    nodes = tuple(row["o"] for row in value["items"])
    if cls is not None:
        require(all(isinstance(node, ArchiveNode) and node.ClassValue.NameValue == cls for node in nodes), "owner array has an unexpected native class")
    return nodes


def inspect(input_value, config, resolved, factory=False):
    shape = input_value.ShapeValue
    stock = shape.StockValue
    root = config.RootValue
    features = resolved.RootsValue
    named = {ReadNodeName(node): node for node in features}
    require(len(named) == len(features), "fresh owner feature names are ambiguous")
    profile, boss, tool, cut = (named[key] for key in (stock.SketchName, stock.FeatureName, shape.SketchName, shape.FeatureName))
    require(features[-4:] == (profile, boss, tool, cut), "generated profile and operation order differs")
    planes = {value.AxisValue: named[value.NameValue] for value in input_value.PlaneValues}
    require(len({id(value) for value in planes.values()}) == 3 and all(value.ClassValue.NameValue == "moRefPlane_c" for value in planes.values()), "generated graph lost an actual principal datum")
    active = planes[stock.AxisValue]
    active_id = active.FieldsValue["f08"]
    for owner, feature in ((profile, boss), (tool, cut)):
        if factory:
            require(owner.FieldsValue["owner"] is root and feature.FieldsValue["owner"] is root, "generated profile or operation belongs to a different model")
        require(array(feature.FieldsValue["f60"]["list"]) == (owner,), "extrusion actual parent is not its own profile")
        support = owner.FieldsValue["pd_f78"].FieldsValue
        require(support["ff0"]["f00"] == active_id and support["f58"].FieldsValue["owner"] is root, "profile support does not target its actual principal datum")
    polygon, circle = profile.FieldsValue["pd_f80"], tool.FieldsValue["pd_f80"]
    require(polygon.FieldsValue["nlines"] == polygon.FieldsValue["npoints"] == 4, "source stock lost actual rectangle topology")
    require(tuple((row["point"]["pos"]["x"], row["point"]["pos"]["y"]) for row in polygon.FieldsValue["points"]) == stock.VerticesValue, "stock coordinates do not match their portable source input")
    logical = polygon.FieldsValue["dims"]["log_g1"]
    require(len(logical) == 4, "stock lost its four unary line relations")
    for mapping in input_value.LineValues:
        index = mapping.TargetIndex
        line = polygon.FieldsValue["lines"][index]["line"]
        relation = logical[index]["d"]
        require(line.get("fc8",line["fc8_s"]) == index and line.get("fcc",line["fcc_s"]) == (index+1)%4 and relation["f80"] == (4 if mapping.AxisKind == "horizontal" else 5) and relation["h1"].FieldsValue["idx"] == index, "source line and relation correspondence lost actual endpoints")
    require(circle.FieldsValue["narcs"] == 1 and circle.FieldsValue["npoints"] == 2, "free circle lost its actual distinct centre and seam")
    arc = circle.FieldsValue["arcs"][0]["arc"]
    center = circle.FieldsValue["points"][arc.get("fdc",arc["fdc_s"])]["point"]["pos"]
    seam = circle.FieldsValue["points"][arc.get("fc8",arc["fc8_s"])]["point"]["pos"]
    require(arc.get("fc8",arc["fc8_s"]) == arc.get("fcc",arc["fcc_s"]) and arc.get("fdc",arc["fdc_s"]) != arc.get("fc8",arc["fc8_s"]), "free circle centre and seam are not distinct actual point owners")
    require((center["x"], center["y"]) == shape.CircleValue.CenterValue and isclose(hypot(seam["x"]-center["x"],seam["y"]-center["y"]),shape.CircleValue.RadiusValue,rel_tol=1e-14), "generated circle geometry differs from the portable source geometry")
    require(boss.ClassValue.NameValue == "moExtrusion_c" and boss.FieldsValue["f810"] == -1 and cut.ClassValue.NameValue == "moICE_c" and cut.FieldsValue["f810"] == 1, "stock join and cut concrete ownership differs")
    stock_end, cut_end = boss.FieldsValue["f818"].FieldsValue, cut.FieldsValue["f818"].FieldsValue
    display = stock_end["f18"]
    handle, = (row["o"] for row in display.FieldsValue["f850"])
    dimension = handle.FieldsValue["ff0"]
    parameter = dimension.FieldsValue["f28"]
    require(parameter.FieldsValue["f58"] == stock.DepthValue and parameter.ClassValue.NameValue=="moLengthParameter_c", "stock depth does not bind its actual driving parameter")
    if factory:
        require(all(value.FieldsValue["owner"] is boss for value in (parameter,dimension,handle)), "fresh driving graph belongs to a different stock")
    both = shape.EndValue.ModeValue == "through_all_both"
    require(tuple(cut_end[key] for key in ("f08","f0c","f10","f88","f8c")) == (int(not both),1,int(both),0,int(shape.EndValue.IsReversed)), "cut termination or signed direction differs")
    require(all(cut_end[key] is None for key in ("f18","f20","fc8","fd0","f138","f90")), "depthless cut acquired an unused end owner")
    manager = root.FieldsValue["fd88"]
    require(manager["n6c"] == len(manager["atoms"]) == 1, "selected scope must own one actual cold stock atom")
    atom = manager["atoms"][0]["o"]
    require(array(boss.FieldsValue["f528"],"moAtom_c") == (atom,), "stock producer does not share the manager's actual atom")
    wrapper, = array(cut.FieldsValue["f548"],"moCompSolidBody_c")
    require(wrapper.FieldsValue["f18"] == wrapper.FieldsValue["f1c"] == atom.FieldsValue["f140"] and wrapper.FieldsValue["f108"] == boss.FieldsValue["f08"] and wrapper.FieldsValue["f58"].FieldsValue["owner"] is root, "selected stock wrapper lost its actual atom producer or self component")
    require(boss.FieldsValue["f544"] == cut.FieldsValue["f544"] == 1 and cut.FieldsValue["has_f528"] == 0 and cut.FieldsValue["f538"] is None, "selected scope precomputed an unqualified final body")
    require("f558" not in boss.FieldsValue and "f558" not in cut.FieldsValue and atom.FieldsValue["f18"] is None, "component output acquired runtime automatic scope or kernel bytes")
    axes = tuple({"selection_id":value.SelectionId,"operation_id":value.FeatureId,"sketch_id":value.SketchId,"plane_id":value.PlaneId,"normal":PrincipalFrame(stock.AxisValue).NormalValue} for value in input_value.AxisValues)
    return {"factory_owner_checked":factory,"principal_datums":3,"sketch_normal_bindings":axes,"stock_relations":4,"circle_centres":1,"actual_profile_parents":2,"selected_stock_wrappers":1,"cut_depth_owners":0,"stock_depth_m":stock.DepthValue,"wire_parent_is_own_profile":True,"stock_producer_is_actual_atom_alias":True,"final_body_pending_native_regeneration":True,"source_semantic_parents_preserved_in_input":input_value.RefsValue.CutParents,"source_line_reversal_map":[{"source_id":value.EntityId,"target_index":value.TargetIndex,"reversed":value.IsReversed} for value in input_value.LineValues]}
