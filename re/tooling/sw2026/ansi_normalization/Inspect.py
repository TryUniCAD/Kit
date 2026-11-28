from ansi_normalization.Rules import (
    LENGTH_CHILDREN,
    METRIC_MINIMUM_ONE,
    METRIC_MINIMUM_TWO,
)
from SpatialTextMut import concrete, require


def expected_paths():
    result = {
        "f13b0/" + key + "/ff0/" + field
        for key in LENGTH_CHILDREN
        for field in ("fb0", "fb8")
    }
    result.add("f13b0/fa68/ff8/f0c")
    result.update("ff68/" + key for key in (*METRIC_MINIMUM_ONE, *METRIC_MINIMUM_TWO))
    result.update(("ff68/f220#0", "ff68/f220#1", "ff68/f10"))
    return result


def inspect_initialization(model, observed):
    table = concrete(model.FieldsValue["f9b8"], "moUnitsTable_c")
    actual = {
        row["o"].ClassValue.NameValue: row["o"] for row in table.FieldsValue["items"]
    }
    places = actual["moLengthUserUnits_c"].FieldsValue["f0c"]
    require(places in (3, 5), "experiment document precision differs")
    require(
        actual["moLengthUserUnits_c"].FieldsValue["fb0"] == 0,
        "actual document unit is not millimetres",
    )
    dimensions = observed["f13b0"]
    dual_ids = []
    for key in LENGTH_CHILDREN:
        style = dimensions[key]
        unit = style["ff0"]
        dual = unit["fb8"]
        require(
            unit["fb0"] == 0
            and unit["f0c"] == min(style["f80"], 16)
            and dual["$class"] == "moLengthUserUnits_c"
            and dual["$fields"]["fb0"] == 3
            and dual["$fields"]["f0c"] == min(style["f84"], 16)
            and dual["$fields"]["fb8"] is None,
            "length style lost actual primary or dual precision ownership",
        )
        raw = model.FieldsValue["fae0"]["f13b0"][key]["ff0"]["fb8"]
        dual_ids.append(id(concrete(raw, "moLengthUserUnits_c")))
    require(len(set(dual_ids)) == 8, "dimension styles share their owned dual units")
    require(
        dimensions["fa68"]["ff8"]["f0c"] == places,
        "base angle did not retain actual document precision",
    )
    require(
        dimensions["f1f0"]["ff8"]["f0c"] == dimensions["f1f0"]["f80"]
        and dimensions["f830"]["ff8"]["f0c"] == dimensions["f830"]["f108"],
        "angle or chamfer precision came from another owner",
    )
    swift = observed["ff68"]
    require(swift["f10"] == 1, "Swift initialization is not persisted")
    require(
        all(
            swift[key] == places
            for key in (*METRIC_MINIMUM_ONE, *METRIC_MINIMUM_TWO, "f220#0", "f220#1")
        ),
        "Swift precision differs from the actual document owner",
    )
    return {
        "document_precision": places,
        "owned_dual_units": 8,
        "complete_presentation_required": True,
    }
