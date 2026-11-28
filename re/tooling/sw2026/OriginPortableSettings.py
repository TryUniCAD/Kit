from __future__ import annotations

from OriginPortableGraph import file_origin, require, scalar
from OriginPortableGeometry import one, row_nodes


def history(graph, group):
    require(group.get("complete") is True, "full portable request requires the actual typed version history")
    root = graph.fields(group["root"], "moVersionHistory_c")
    require(root["n"] == len(root["states"]) == 1, "fresh history constructor cannot preserve multiple source version states")
    state = root["states"][0]["st"]
    codes = graph.fields(state["f38"], "moDateCodeHistory_c")
    require(codes["n"] == len(codes["states"]) == 1, "fresh history constructor cannot preserve multiple originating builds")
    return {"created_at": state["f08"]["f18"], "comment": graph.text(state["f08"]["f20"]),
            "originating_build_code": codes["states"][0]["st"]["f08"], "license_origin": root["f30"],
            "language_id": root["f38"], "cjk_saved": bool(root["f3c"])}


def provenance(graph, header_ref, model_ref, history_value):
    header = graph.fields(header_ref, "moHeader_c")
    texts = []
    for key in ("f10", "f18"):
        values = graph.fields(header[key])["values"]
        texts.append(graph.text(one(values, "header author or company")))
    logs = row_nodes(graph, header["f20"])
    root_id = graph.fields(model_ref)["f08"]
    log = one([row for row in logs if row["fields"]["f48"] == root_id], "current model provenance log")
    events = row_nodes(graph, log["identity"])
    event = one(events, "fresh model provenance event")["fields"]
    require(history_value["created_at"] == header["f70"] == event["f18"], "constructor has one creation epoch but source header history and model log differ")
    require(history_value["comment"] == graph.text(event["f20"]), "constructor has one history comment but source version and model log comments differ")
    require(1 <= history_value["originating_build_code"] <= 0xFFFFFF,
            "source originating build cannot be reused as truthful fresh nonnative writer provenance")
    return {"author": texts[0], "company": texts[1], "comment": history_value["comment"],
            "created_at": header["f70"], "modified_at": header["f50"], "updated_at": header["f48"],
            "originating_build_code": history_value["originating_build_code"], "license_origin": history_value["license_origin"],
            "language_id": history_value["language_id"], "cjk_saved": history_value["cjk_saved"]}


def styles(graph, model_ref, language_id):
    fields = graph.fields(model_ref)["fae0"]
    if "$node" in fields:
        fields = graph.fields(fields)
    widths = fields["fb0"]
    names = fields["f58"]
    require(fields["n58"] == len(names) and fields["fb8"]["n"] == len(fields["fb8"]["items"]) == 5,
            "portable source style text arrays are incomplete")
    return {"standard": fields["f10"], "font_name": graph.text(fields["f90"]["f08"]),
            "line_style_name": graph.text(fields["f13b0"]["fe0"]["fd0"]["f08"]), "language_id": language_id,
            "print_widths_m": [scalar(widths["f" + format(8 + 4 * index, "x")]) for index in range(8)],
            "exclusion_names": [graph.text(row["s"]) for row in names],
            "task_labels": [graph.text(row["s"]) for row in fields["fb8"]["items"]],
            "cutlist_expressions": [graph.text(fields[key]) for key in ("f200", "f208", "f210")]}


def units(graph, value):
    table = graph.fields(value, "moUnitsTable_c")
    require(table["n"] == len(table["items"]) == 16, "portable source units require the complete sixteen-class constructor profile")
    by_class = {row["o"]["$node"]["class"]: graph.fields(row["o"]) for row in table["items"]}
    require(len(by_class) == 16, "portable source unit classes are duplicated")
    length = {0: "mm", 1: "cm", 2: "m", 3: "in", 4: "ft", 6: "angstrom", 7: "nm", 8: "um", 9: "mil", 10: "microinch"}
    angle = {0: "degree", 1: "arcminute", 2: "arcsecond", 3: "radian"}
    system = {0: "cgs", 1: "mks", 2: "ips", 4: "mmgs"}
    precision = {row["f0c"] for row in by_class.values()}
    require(len(precision) == 1, "one constructor precision cannot preserve distinct source unit-format precisions")
    return {"length_unit": length[by_class["moLengthUserUnits_c"]["fb0"]], "angle_unit": angle[by_class["moAngleUserUnits_c"]["fb0"]],
            "unit_system": system[by_class["moUnitSysUnits_c"]["fb0"]], "decimal_places": precision.pop()}


def ui_settings(graph, group):
    require(group.get("complete", True) is True, "portable source model Definition is incomplete")
    fields = graph.fields(group["root"])
    bits = (fields["fad8_0"] & 0xFFFFFFFF) | ((fields["fad8_1"] & 0xFFFFFFFF) << 32)
    require(fields["fa64"] in (0, 1) and fields["fa90"] in (0, 1), "portable source UI preferences have unsupported modes")
    journal = graph.fields(fields["ffd8"]["f18"])
    return {"drafting_standard": fields["fba8"]["$node"]["class"], "detail_flags": [index for index in range(64) if bits & (1 << index)],
            "tessellation": [fields["fa58"], fields["fa5c"], fields["fa60"], bool(fields["fa64"])],
            "system_preference_7a": bool(fields["fa90"]), "journal_name": graph.text(journal["f08"])}


def part_settings(graph, case, geometry, boss, names):
    model_ref, header_ref = case["typed_child"]["root"], case["typed_child"]["header"]
    model = graph.fields(model_ref)
    history_value = history(graph, case["typed_child_history"])
    provenance_value = provenance(graph, header_ref, model_ref, history_value)
    manager = graph.fields(case["typed_child_manager"]["root"], "moConfigurationMgr_c")
    require(manager["f18"] is not None, "source configuration manager is anonymous but the current constructor requires an authored nonempty name")
    folders = []
    folder_classes = {"moCommentsFolder_c", "moFavoriteFolder_c", "moHistoryFolder_c", "moSelectionSetFolder_c", "moSensorFolder_c", "moDocsFolder_c", "moSurfaceBodyFolder_c", "moSolidBodyFolder_c", "moEnvFolder_c", "moInkMarkupFolder_c", "moEqnFolder_c", "moMaterialFolder_c"}
    root_nodes = [graph.node(value) for value in case["typed_child"]["resolved_roots"]]
    for row in root_nodes:
        if row["identity"]["class"] in folder_classes:
            folders.append([row["identity"]["class"], graph.name(row["identity"])])
    require(len(folders) == len(folder_classes), "portable source has missing duplicate or additional system folders")
    cabinet = one([row for row in root_nodes if row["identity"]["class"] == "moDetailCabinet_c"], "part annotation cabinet")
    planes = [row for row in root_nodes if row["identity"]["class"] == "moRefPlane_c"]
    construction = {bool(row["fields"]["f6dc"] & 4) for row in planes}
    require(len(construction) == 1, "portable source principal plane construction flags differ")
    displays = [graph.fields(value["display"]) for value in geometry["drivers"]] + [graph.fields(boss["display"])]
    intent = {bool(value["fb60"] & 256) for value in displays}; leaders = {value["ff80"] for value in displays}
    require(len(intent) == len(leaders) == 1, "one constructor display policy cannot preserve distinct source dimension presentation")
    own_file = file_origin(graph, graph.fields(header_ref)["f38"])
    result = {"styles": styles(graph, model_ref, history_value["language_id"]), "document_units": units(graph, model["f9b8"]),
              "analysis_units": units(graph, model["f9c0"]), "system": {"folders": folders, "planes": names, "cabinet_name": graph.name(cabinet["identity"]),
              "origin_name": geometry["origin"]["name"], "origin_axis": "z", "created_at": provenance_value["created_at"], "construction_flag": construction.pop()},
              "target": {"date_code": boss["date_code"], "parasolid_version": boss["parasolid_version"]},
              "provenance": {key: value for key, value in provenance_value.items() if key != "language_id"}, "definition": ui_settings(graph, case["typed_child_definition"]),
              "output": {"path_name": own_file["path"], "saved_at": own_file["saved_at"]}, "hatch_name": graph.text(graph.fields(model["f1418"], "gcXhatch_c")["f08"]),
              "manager_name": graph.text(manager["f18"]), "density_kg_m3": scalar(graph.fields(case["typed_child_definition"]["root"])["f1688"]),
              "design_intent": intent.pop(), "selected_leader": leaders.pop()}
    return result


def drawing_settings(graph, case, owners):
    model_ref, header_ref = owners["model"], owners["drawing_header"]
    model = graph.fields(model_ref)
    sheet = graph.fields(owners["sheet"])
    history_value = history(graph, case["typed_drawing_history"])
    provenance_value = provenance(graph, header_ref, model_ref, history_value)
    children = graph.children(model_ref)
    folders = {}
    for key, kind in (("annotations", "moDetailCabinet_c"), ("binder", "moDocsFolder_c"), ("comments", "moCommentsFolder_c"),
                      ("blocks", "moBlockFolder_c"), ("ink_markups", "moInkMarkupFolder_c"), ("review_markups", "moMarkupCommentFolder_c")):
        folders[key] = graph.name(one([row for row in children if row["identity"]["class"] == kind], "drawing folder " + kind)["identity"])
    supports = graph.children(owners["sheet"])
    plane = one([row for row in supports if row["identity"]["class"] == "moRefPlane_c"], "sheet support plane")
    block = graph.node(model["fe80"], "moSketchBlockMgr_c")["typed_block_identity"]
    require(block["version"] == 4, "current drawing constructor requires a source uuid4 block identity")
    target_fields = graph.fields(owners["sheet"])
    return {"options": {"name": graph.name(model_ref), "property_view": owners["property_view"],
             "sheet_names": {"plane_name": graph.name(plane["identity"]), "profile_name": graph.name(sheet["f408"]), "detail_name": graph.name(sheet["f390"])},
             "folder_names": folders, "styles": styles(graph, model_ref, history_value["language_id"]), "units": units(graph, model["f9b8"]),
             "target": {"date_code": target_fields["f2bc"], "parasolid_version": target_fields["f2ac"]}, "created_at": provenance_value["created_at"],
             "block_identity": block["uuid"], "auto_dim_text_link": bool(model["f1444"] & 1)}, "provenance": provenance_value,
             "ui": ui_settings(graph, case["typed_drawing"]), "output": {"path_name": owners["drawing_file"]["path"], "saved_at": owners["drawing_file"]["saved_at"]}}
