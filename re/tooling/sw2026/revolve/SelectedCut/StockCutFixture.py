from dataclasses import replace
from math import tau

from BuildPrincipalRevolves import authored_neutral
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.Selection import Selection, SelectPathElem


DESIGNS = (
    {"name": "KitScopeCutFront", "plane": "front", "axis": 6.25, "span": (-76., 91.),
     "radial": ((9., 24.), (39., 56.), (17., 45.)), "axial": ((-38., 52.), (-38., 52.), (-21., 16.)),
     "angle": 63.5, "selected": 0, "epoch": 1760502021},
    {"name": "KitScopeCutRight", "plane": "right", "axis": -4.7, "span": (-89., 64.),
     "radial": ((13., 22.), (31., 49.), (19., 43.)), "axial": ((-53., 31.), (-53., 31.), (-16., 19.)),
     "angle": 144.25, "selected": 1, "epoch": 1760612759},
)


def fixture(design, fault=None):
    documents = []
    angles = (360., 360., design["angle"])
    for index, (radial, axial, angle) in enumerate(zip(design["radial"], design["axial"], angles, strict=True)):
        name = design["name"]
        suffix = ("inner", "outer", "tool")[index]
        spec = {
            "name": name, "radial_mm": radial, "axial_mm": axial,
            "axis_x_mm": design["axis"] + (1.0 if fault == "cross-axis" and index == 2 else 0.0),
            "axis_span_mm": design["span"], "angle_deg": angle, "reverse": fault == "reverse-cut" and index == 2,
            "edit_angle_deg": 245.75, "created_at": design["epoch"], "self_path": f"C:\\KitScope\\{name}.SLDPRT",
        }
        single = authored_neutral(spec, design["plane"], None)
        sketch, = single.sketches
        ids = {value.id: f"{suffix}/{value.id}" for value in sketch.entities}
        profile = replace(sketch, id=f"{suffix}/{sketch.id}", name=f"Profile {suffix}",
                          entities=tuple(replace(value, id=ids[value.id]) for value in sketch.entities),
                          closed_profile_entity_ids=tuple(tuple(ids[value] for value in values)
                                                          for values in sketch.closed_profile_entity_ids),
                          constraints=tuple(replace(value, id=f"{suffix}/{value.id}", references=tuple(
                              replace(ref, entity_id=ids[ref.entity_id]) for ref in value.references
                          )) for value in sketch.constraints))
        selection, = single.selections
        axis = replace(selection, id=f"{suffix}/{selection.id}", path=(
            SelectPathElem("sketch", profile.id), SelectPathElem("sketch_entity", ids[selection.path[1].entity_id]),
        ))
        feature, = single.feature_timeline
        feature_id = f"{suffix}/{feature.id}"
        parameter, = single.parameters
        parameter = replace(parameter, id=f"{suffix}/{parameter.id}", owner_id=feature_id)
        step = replace(feature, id=feature_id, order=index, name=("Inner stock", "Outer stock", "Scoped cut")[index],
                       sketch_id=profile.id, parameter_ids=(parameter.id,), selection_ids=(axis.id,),
                       definition=replace(feature.definition, AxisSelectionId=axis.id, AlongParameterId=parameter.id))
        documents.append((single, profile, axis, parameter, step))

    first, second, third = documents
    stocks = (first[-1], second[-1])
    selected = design["selected"]
    chosen, other = stocks[selected], stocks[1 - selected]
    cut = third[-1]
    target = other if fault == "cross-selection" else chosen
    body_pick = Selection("selection/stock", "Selected historical stock", (SelectPathElem("feature", target.id, "body"),))
    cut = replace(cut, operation=BooleanOp.KCutOperation, input_feature_ids=(chosen.id,),
                  selection_ids=(*cut.selection_ids, body_pick.id))
    parameters = tuple(value[3] for value in documents)
    assert parameters[0].value.value == parameters[1].value.value == tau
    if fault == "cross-driver":
        parameters = (*parameters[:-1], replace(parameters[-1], owner_id=other.id))
    return replace(first[0], sketches=tuple(value[1] for value in documents), parameters=parameters,
                   selections=(*(value[2] for value in documents), body_pick), feature_timeline=(*stocks, cut),
                   bodies=(DesignBody("body/survivor", other.name, other.id), DesignBody("body/cut", cut.name, cut.id)))
