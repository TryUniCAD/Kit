from dataclasses import dataclass
from math import isfinite

from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyLabel import (
    ReadBodyLabel,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckIdentity import (
    CheckIdentity,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxText import (
    ReadDocProps,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropChild,
    ReadPropText,
    RequireEmpty,
    RequireProp,
)
from FcstdRectangleOwners01 import require, source_objects
from interchange import ParameterValue, ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd
from PlanFcstdCorner import CornerIntent, plan_corner

BODY_FIELDS = {
    "BaseFeature",
    "ExpressionEngine",
    "Group",
    "Label",
    "Label2",
    "Origin",
    "Placement",
    "Shape",
    "Tip",
    "Visibility",
}
PAD_ROWS = {
    "AllowMultiFace": ("Bool", ValueKind.BOOLEAN, "", "unrepresented_profile_policy"),
    "AlongSketchNormal": ("Bool", ValueKind.BOOLEAN, "", "guarded_sketch_normal"),
    "Label": ("String", ValueKind.STRING, "", "live_boss_name"),
    "Label2": ("String", ValueKind.STRING, "", "empty_alternate_label"),
    "Length": ("Length", ValueKind.LENGTH, "mm", "live_forward_length"),
    "Length2": ("Length", ValueKind.LENGTH, "mm", "distinct_dormant_length"),
    "Midplane": ("Bool", ValueKind.BOOLEAN, "", "single_forward_extent"),
    "Offset": ("Length", ValueKind.LENGTH, "mm", "guarded_inactive_zero_offset"),
    "Refine": ("Bool", ValueKind.BOOLEAN, "", "unrepresented_refinement_policy"),
    "Reversed": ("Bool", ValueKind.BOOLEAN, "", "forward_direction"),
    "TaperAngle": ("Angle", ValueKind.ANGLE, "deg", "zero_forward_draft"),
    "TaperAngle2": ("Angle", ValueKind.ANGLE, "deg", "zero_dormant_draft"),
    "Type": ("Enumeration", ValueKind.INTEGER, "", "finite_length_extent"),
    "UseCustomVector": ("Bool", ValueKind.BOOLEAN, "", "guarded_sketch_normal"),
    "Visibility": ("Bool", ValueKind.BOOLEAN, "", "guarded_visible_source"),
}
PAD_FIELDS = set(PAD_ROWS) | {
    "AddSubShape",
    "BaseFeature",
    "Direction",
    "ExpressionEngine",
    "Placement",
    "Profile",
    "ReferenceAxis",
    "Shape",
    "UpToFace",
}
SOURCE_MODE = {
    "AllowMultiFace": True,
    "AlongSketchNormal": True,
    "Label2": "",
    "Midplane": False,
    "Offset": 0.0,
    "Refine": False,
    "Reversed": False,
    "TaperAngle": 0.0,
    "TaperAngle2": 0.0,
    "Type": 0,
    "UseCustomVector": False,
    "Visibility": True,
}
TAGS = {
    "Bool": "Bool",
    "String": "String",
    "Enumeration": "Integer",
    "Length": "Float",
    "Angle": "Float",
}


@dataclass(frozen=True)
class SourceOwners:
    corner: CornerIntent
    body_name: str
    dormant_m: float
    body_roles: dict
    pad_parameters: dict
    document_label: str


def actual_object(owners, neutral, kind):
    actual = neutral.attributes["freecad"]
    require(
        actual == owners[actual["name"]]
        and actual["type_id"] == kind
        and not actual["touched"],
        "source object metadata differs from its actual neutral owner",
    )
    properties = actual["properties"]
    require(
        tuple(properties) == tuple(actual["property_order"])
        and all(
            key == value["attributes"]["name"] for key, value in properties.items()
        ),
        "source object property ordering or declaration ownership differs",
    )
    return actual


def check_body(document, actual, body, sketch_name, pad_name):
    properties = actual["properties"]
    require(set(properties) == BODY_FIELDS, "source Body property set differs")
    require(
        body.attributes["tip"] == pad_name,
        "source Body tip differs from the actual Pad",
    )
    label = ReadBodyLabel(document)
    RequireProp(properties, "Label", "String", "String", label)
    RequireProp(properties, "Label2", "String", "String", "")
    RequireProp(properties, "BaseFeature", "Link", "Link", "")
    RequireProp(properties, "Origin", "Link", "Link", "Origin")
    RequireProp(properties, "Tip", "Link", "Link", pad_name)
    RequireProp(properties, "Visibility", "Bool", "Bool", "true")
    RequireEmpty(properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    CheckIdentity(properties, "Placement")
    links = ReadPropChild(properties["Group"], "LinkList", "LinkList")
    require(
        links["attributes"] == {"count": "2"}
        and links["children"]
        == [
            {"tag": "Link", "attributes": {"value": name}}
            for name in (sketch_name, pad_name)
        ],
        "source Body group differs from its actual ordered Sketch and Pad",
    )
    require(
        label.isascii() and body.material_id is None and not document.materials,
        "source Body is outside the authored ASCII unassigned profile",
    )
    return label


def check_pad_graph(document, actual, sketch_name, sketch):
    properties = actual["properties"]
    require(set(properties) == PAD_FIELDS, "source Pad property set differs")
    RequireProp(properties, "BaseFeature", "Link", "Link", "")
    CheckIdentity(properties, "Placement")
    for key, owner in (
        ("Profile", sketch_name),
        ("ReferenceAxis", ""),
        ("UpToFace", ""),
    ):
        link = ReadPropChild(properties[key], "LinkSub", "LinkSub")
        require(
            link["attributes"] == {"count": "0", "value": owner}
            and not link.get("children"),
            f"source Pad {key} differs from its scoped whole owner",
        )
    direction = ReadPropChild(properties["Direction"], "Vector", "PropertyVector")
    attrs = direction["attributes"]
    (support,) = (
        value
        for value in document.support_planes
        if value.id == sketch.support_plane_id
    )
    normal = support.transform.z_axis
    require(
        set(attrs) == {"valueX", "valueY", "valueZ"}
        and tuple(float(attrs[value]) for value in ("valueX", "valueY", "valueZ"))
        == (normal.x, normal.y, normal.z)
        == (0.0, 0.0, 1.0),
        "source Pad direction differs from its actual signed sketch normal",
    )


def read_pad_rows(document, feature, properties):
    by_id = {param.id: param for param in document.parameters}
    ordered = tuple(by_id[key] for key in feature.parameter_ids)
    rows = {param.attributes.get("freecad_path"): param for param in ordered}
    require(
        len(ordered) == len(rows) == len(PAD_ROWS) and set(rows) == PAD_ROWS.keys(),
        "source Pad neutral parameter property set differs",
    )
    result = {}
    for key, (dtype, kind, unit, role) in PAD_ROWS.items():
        param = rows[key]
        text = ReadPropText(properties, key, dtype, TAGS[dtype])
        if kind is ValueKind.BOOLEAN:
            require(text in ("true", "false"), "malformed source Pad boolean")
            value = text == "true"
        elif kind is ValueKind.INTEGER:
            value = int(text)
        elif kind is ValueKind.STRING:
            value = text
        else:
            value = float(text)
            require(isfinite(value), "nonfinite source Pad scalar")
        require(
            param.owner_id == feature.id
            and param.value == ParameterValue(value, kind, unit)
            and type(param.value.value) is type(value)
            and (param.expression is None) == (key != "Length"),
            f"source Pad {key} differs from its owned neutral parameter",
        )
        if key in SOURCE_MODE:
            require(
                value == SOURCE_MODE[key],
                f"source Pad {key} differs from the bounded mode",
            )
        result[key] = {
            "parameter_id": param.id,
            "value": value,
            "unit": unit,
            "classification": role,
            "saved_status": properties[key]["attributes"].get("status"),
        }
    return result, rows


def source_owners(document, target_name):
    corner = plan_corner(document, target_name)
    (sketch,) = document.sketches
    (pad,) = document.feature_timeline
    (body,) = document.bodies
    owners = source_objects(document)
    body_object = actual_object(owners, body, "PartDesign::Body")
    sketch_object = actual_object(owners, sketch, "Sketcher::SketchObject")
    pad_object = actual_object(owners, pad, "PartDesign::Pad")
    sketch_name, pad_name = sketch_object["name"], pad_object["name"]
    label = check_body(document, body_object, body, sketch_name, pad_name)
    check_pad_graph(document, pad_object, sketch_name, sketch)
    properties, rows = read_pad_rows(document, pad, pad_object["properties"])
    definition = pad.definition
    require(
        rows["Label"].value.value == pad.name
        and sketch.id == pad.sketch_id
        and body.final_feature_id == pad.id
        and definition.length == rows["Length"].value
        and definition.second_length == rows["Length2"].value
        and definition.offset == rows["Offset"].value
        and definition.draft_angle == rows["TaperAngle"].value
        and definition.second_draft_angle == rows["TaperAngle2"].value
        and definition.end_condition == ExtrudeEnd.KBlind
        and definition.second_end_condition is None
        and not definition.reversed
        and not definition.symmetric,
        "source Pad native properties differ from its actual creation and inactive end",
    )
    props = ReadDocProps(document.source, document.metadata["freecad"], "0.21")
    source_label = ReadPropText(props, "Label", "String", "String")
    return SourceOwners(
        corner,
        label,
        ReadLength(rows["Length2"].value),
        {
            "body_id": body.id,
            "body_group": [sketch.id, pad.id],
            "tip_feature": pad.id,
            "origin_source_object": "Origin",
            "support": sketch.support_plane_id,
        },
        properties,
        source_label,
    )
