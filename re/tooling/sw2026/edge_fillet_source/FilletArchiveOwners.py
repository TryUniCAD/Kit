from math import isfinite
from struct import unpack

from FilletModel import require

from Core import Obj
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents

CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
SIDE = "moFromSktEntSurfIdRep_c"
END = "moEndFaceSurfIdRep_c"
FILLET_SURFACE = "moFilletSurfIdRep_c"


def node(value, cls):
    require(isinstance(value, Obj) and value.cls == cls, f"expected typed {cls}")
    return value


def span(value, stream=RESOLVED):
    require(type(value.index) is int and value.index > 0 and 0 <= value.pos < value.end,
            "expected a mapped wire object with a complete interval")
    return {"class": value.cls, "schema": value.schema, "slot": value.index,
            "interval": [value.pos, value.end], "stream": stream}


def only_rows(values, count):
    require(values["n"] == len(values["items"]) == count, "fillet typed item count differs")
    return values["items"]


def stock_epoch(roots, *headers):
    result = {root["f08"]: DatumTime(headers[0], root["f08"]) for root in roots}
    require(2592000 not in result.values() and all(
        DatumTime(header, native_id) == value
        for header in headers[1:] for native_id, value in result.items()
    ), "fillet references must belong to a shared recorded creation event")
    return result


def surface(value, epochs):
    reference = node(value["f10"]["f10"], "moFR_c")
    key = reference["f10"]
    feature = key["f00"]
    require(feature in epochs and key["f08"] == epochs[feature], "fillet surface has a different producer event")
    holder = node(reference["f08"], "moExtObject_c")
    cfg = holder["refcfg"]["f08"]
    require(cfg == "Default", "surface reference configuration differs")
    return {"owner": span(value), "feature_id": feature, "creation_word": key["f08"],
            "configuration": cfg, "f38": value.get("f38"), "f3c": value.get("f3c"),
            "feature_reference_slot": reference.index}


def reference(wrapper, ref_class, epochs):
    ref = node(wrapper["fe8"], ref_class)
    rows = [row["f08"] for row in ref["f10"]]
    require(len(rows) == ref["f08"] and ref["has_f18"] == ref["nd0"] == 0
            and (ref.get("nf0") == 0 if ref_class == "moFaceRef_c" else "nf0" not in ref.f),
            "fillet reference has extra surface framing")
    reps = [surface(row, epochs) if row is not None else None for row in rows]
    return ref, {"wrapper": span(wrapper), "reference": span(ref),
                 "wrapper_words_f18_f1c": [wrapper["f18"], wrapper["f1c"]],
                 "reference_words_f70_fe8": [ref["f70"], ref["fe8"]], "surfaces": reps}


def signature(reps):
    return [tuple(rep[k] if k != "owner" else rep[k]["class"]
                  for k in ("owner", "feature_id", "creation_word", "configuration", "f38", "f3c"))
            for rep in reps if rep is not None]


def radius_owner(fillet):
    (row,) = only_rows(node(fillet["f868"], "suObList"), 1)
    radius = node(row["o"], "edgeRadiusObject_c")
    display = node(radius["f08"], "moDisplayRadialDim_c")
    require(display["n850"] == len(display["f850"]) == 1, "expected a single radial dimension handle")
    handle = node(display["f850"][0]["o"], "moFeatureDimHandle_c")
    require(handle["fe8"] is None and handle["f100"] is None, "unexpected radial handle branch")
    dimension = node(handle["ff0"], "ThreeDRadiusDim_c")
    parameter = node(dimension["f28"], "moLengthParameter_c")
    require(ReadNativeName(parameter) == "D1" and parameter["f68"] == 0
            and parameter["f20"] == "" and parameter["f48"] is None
            and type(parameter["f58"]) is float and isfinite(parameter["f58"]) and parameter["f58"] > 0
            and all(fillet[key] is None for key in ("f830", "f838", "f840")),
            "unexpected radial scalar or additional display")
    return radius, display, dimension, parameter, [span(value) for value in (radius, display, handle, dimension, parameter)]


def display_value(display):
    rows = display["f5b0"]
    require(rows["elem"] == len(rows["data"]) == 8 and rows["n"] == 1, "unexpected display scalar vector")
    (value,) = unpack("<d", rows["data"])
    require(isfinite(value), "non-finite display scalar")
    return {"value_si": value, "allocation_words": [rows["alloc_a"], rows["alloc_b"]]}


def keeper_inventory(fillet, selected, epochs):
    edge, face = fillet["f820"], fillet["f828"]
    require(only_rows(edge["ff0"], 1)[0]["o"] is selected, "keeper must alias the primary edge reference")
    only_rows(face["f18"], 0)
    only_rows(face["fe0"], 0)
    keepers = [surface(row["id"]["f08"], epochs) for row in only_rows(edge["f18"], 2)]
    require([value["owner"]["class"] for value in keepers] == ["moSurfaceIdRep_c", FILLET_SURFACE]
            and all(row["feature_id"] == fillet["f08"] for row in keepers) and keepers[1]["f38"] == 1,
            "fillet keeper surface types or producing feature differ")
    return {"edge_f820": keepers, "edge_f820_ff0_ref_slot": selected.index, "face_f828_rows": 0}


def selection(fillet, stock, radius, epochs):
    (primary_row,) = only_rows(node(fillet["f848"], "suObList"), 1)
    primary = node(primary_row["o"], "moCompEdge_c")
    radial_choice = node(radius["f10"], "moCompEdge_c")
    primary_ref, primary_report = reference(primary, "moEdgeRef_c", epochs)
    radius_ref, radius_report = reference(radial_choice, "moEdgeRef_c", epochs)
    require(primary is not radial_choice and primary_ref is radius_ref, "radial choice lost its selected edge alias")
    require(fillet["n9b8"] == len(fillet["f9b8"]) == fillet["nbf0"] == len(fillet["fbf0"]) == 1,
            "unexpected fillet output face or radius map inventory")
    (mapping,), (radius_row,) = fillet["f9b8"], fillet["fbf0"]
    _, face = reference(node(mapping["k"], "moCompFace_c"), "moFaceRef_c", epochs)
    output_ref, output_report = reference(node(mapping["v"], "moCompEdge_c"), "moEdgeRef_c", epochs)
    repeat_ref, repeat_report = reference(node(radius_row["edge"], "moCompEdge_c"), "moEdgeRef_c", epochs)
    expected = signature(primary_report["surfaces"])
    require(len(expected) == len(primary_report["surfaces"]) == 4
            and all(row[0] in (SIDE, END) and row[1] == stock["f08"] for row in expected)
            and expected == signature(output_report["surfaces"]) == signature(repeat_report["surfaces"])
            and len({primary_ref, output_ref, repeat_ref}) == 3,
            "fillet choices lack distinct output references with the same typed stock identity")
    face_reps = signature(face["surfaces"])
    generated = [item for item in face_reps if item[0] == FILLET_SURFACE]
    require(len(face_reps) == 5 and len(face["surfaces"]) == 6 and face["surfaces"][-1] is None
            and len(generated) == 1 and generated[0][1] == fillet["f08"] and generated[0][4] == 1
            and sorted(row for row in face_reps if row[0] != FILLET_SURFACE) == sorted(expected),
            "output face does not retain the fillet and its ordered stock owners")
    return {
        "f848_selected_edge": primary_report, "f868_radial_edge_alias_slot": radius_ref.index,
        "f868_radial_edge_wrapper": radius_report["wrapper"],
        "f868_radial_wrapper_words_f18_f1c": radius_report["wrapper_words_f18_f1c"],
        "f9b8_result_face": face, "f9b8_detached_edge": output_report, "fbf0_detached_edge": repeat_report,
        "fbf0_row_fields": {k: radius_row[k] for k in ("f00", "f04", "f08")},
    } | keeper_inventory(fillet, primary_ref, epochs)


def linked_body(config, stock, fillet):
    root, = config.roots
    manager = root["fd88"]
    atom = node(manager["atoms"][0]["o"], "moAtom_c")
    (reference,) = only_rows(stock["f528"], 1)
    require(manager["n6c"] == len(manager["atoms"]) == 1 and stock["f498"] == [{"v": atom["f140"]}]
            and fillet["f498"] == [] and reference["o"] is atom and fillet["f538"] is atom
            and atom["body_kind"] == 0 and atom["f12c"] == stock["f08"] and atom["f130"] == fillet["f08"]
            and atom["f180"] == atom["f1b0"], "fillet must modify the one stock-created configured atom")
    return atom, {"owner": span(atom, CONFIG), "atom_id": atom["f140"], "body_kind": atom["body_kind"],
                  "creator_id": atom["f12c"], "last_modifier_id": atom["f130"], "body_stamp": atom["f180"],
                  "config_mark": root["fe38"]["f18"], "stock_mark": stock["f3d0"]["f18"],
                  "fillet_mark": fillet["f3d0"]["f18"]}


def audit_owners(config, resolved, headers, observed):
    fillet, = (row for row in resolved.roots if isinstance(row, Obj) and row.cls == "Fillet_c")
    stock, = (row for row in resolved.roots if isinstance(row, Obj) and row.cls == "moExtrusion_c")
    sketch, = (row for row in resolved.roots if isinstance(row, Obj) and row.cls == "moProfileFeature_c")
    require(fillet.schema == 1 and ReadNativeName(fillet) == observed["fillet_name"]
            and ReadNativeName(stock) == observed["stock_name"], "disclosed fillet root identity differs")
    radius, display, dimension, parameter, radial_chain = radius_owner(fillet)
    edge = selection(fillet, stock, radius, stock_epoch((stock, fillet), *headers))
    require(parameter["f58"] == observed["radius_m"] == edge["fbf0_row_fields"]["f08"]
            and ReadParents(fillet) == () and ReadParents(stock) == (sketch,),
            "live radial driver, keyed map radius or ordinary root list differs")
    atom, body = linked_body(config, stock, fillet)
    stock_display = node(node(stock["f818"], "moEndSpec_c")["f18"], "moDisplayDistanceDim_c")
    vectors = {"stock_distance": display_value(stock_display), "fillet_radial": display_value(display)}
    require(vectors["stock_distance"]["value_si"] == observed["stock_depth_m"]
            and vectors["fillet_radial"]["value_si"] == parameter["f58"],
            "display vector differs from the independently confirmed driver")
    return atom, {
        "fillet": span(fillet) | {"name": ReadNativeName(fillet), "native_id": fillet["f08"], "f60_rows": 0},
        "stock": span(stock) | {"name": ReadNativeName(stock), "native_id": stock["f08"]},
        "stock_sketch": span(sketch) | {"name": ReadNativeName(sketch), "native_id": sketch["f08"]},
        "radial_driver": {"name": ReadNativeName(parameter), "radius_m": parameter["f58"],
                          "dimension_native_id": dimension["f50"], "owners": radial_chain},
        "display_vectors": vectors,
        "edge_owners": edge, "body_owner": body,
    }
