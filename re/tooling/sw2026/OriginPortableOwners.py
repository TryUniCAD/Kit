from __future__ import annotations

from ntpath import normcase, normpath

from OriginPortableGraph import file_origin, require, scalar
from OriginPortableGeometry import creation_time, one


def same_path(first, second):
    return normcase(normpath(first)) == normcase(normpath(second))


def extrusion(graph, link, geometry):
    feature = one([graph.node(value) for value in link["resolved_roots"] if value["class"] == "moExtrusion_c"], "ordinary blind boss")
    allowed = {"moCommentsFolder_c", "moFavoriteFolder_c", "moHistoryFolder_c", "moSelectionSetFolder_c", "moSensorFolder_c", "moDocsFolder_c",
               "moSurfaceBodyFolder_c", "moSolidBodyFolder_c", "moEnvFolder_c", "moInkMarkupFolder_c", "moEqnFolder_c", "moMaterialFolder_c",
               "moDetailCabinet_c", "moRefPlane_c", "moOriginProfileFeature_c", "moProfileFeature_c", "moExtrusion_c"}
    require(all(value["class"] in allowed for value in link["resolved_roots"])
            and len(graph.members("moExtrusion_c")) == 1,
            "portable source has another prior or additional body-producing feature")
    children = graph.children(feature["identity"])
    require(len(children) == 1 and children[0]["identity"] == geometry["profile"], "portable source boss does not own the selected profile")
    end = graph.fields(feature["fields"]["f818"], "moEndSpec_c")
    require((end["f08"], end["f0c"], end["f10"], end["f88"], end["f8c"]) == (1, 0, 0, 0, 0), "portable source boss is not ordinary forward blind")
    require(end["f138"] is None and end["f90"] is None and all(end[key] == 0 for key in ("fa0", "fb8", "fbc", "fc0", "fc4")),
            "portable source boss has draft or referenced termination")
    end_lists = [end_list_state(end, key) for key in ("f28", "f48")]
    from_value = graph.fields(end["f140"], "moFromEndSpec_c")
    require(from_value["t"] == 0, "portable source boss has an authored start condition")
    display = graph.node(end["f18"], "moDisplayDistanceDim_c")
    handles = display["fields"]["f850"]
    require(display["fields"]["n850"] == len(handles) == 1, "portable source depth display has another target")
    handle = graph.fields(handles[0]["o"], "moFeatureDimHandle_c")
    require(handle["fe8"] is None and handle["f100"] is None, "portable source depth is not local")
    dimension = graph.node(handle["ff0"], "ParallelPlaneDistanceDim_c")
    parameter = graph.node(dimension["fields"]["f28"], "moLengthParameter_c")
    length = scalar(parameter["fields"]["f58"])
    require(length > 0 and parameter["fields"]["f68"] == 0 and parameter["fields"]["f48"] is None, "portable source depth is not a plain positive driving length")
    return {"feature": feature["identity"], "native_id": feature["fields"]["f08"], "name": graph.name(feature["identity"]), "depth_m": length,
            "parameter": parameter["identity"], "dimension": dimension["identity"], "display": display["identity"],
            "depth_name": graph.name(parameter["identity"]), "date_code": feature["fields"]["f2bc"], "parasolid_version": feature["fields"]["f2ac"],
            "end_reference_arrays": end_lists}


def end_list_state(end, key):
    presence = end["has_" + key]
    require(type(presence) is int and presence in (0, 1), "portable source boss end reference presence is invalid: " + key)
    if presence == 0:
        require(key not in end or end[key] is None, "portable source absent end reference has unexpected payload: " + key)
        return {"field": key, "presence": presence, "wire_payload_present": False}
    value = end[key]
    require(type(value) is dict and type(value.get("n")) is int and value["n"] == 0
            and type(value.get("items")) is list and not value["items"],
            "portable source boss has an authored or malformed end reference: " + key)
    return {"field": key, "presence": presence, "wire_payload_present": True, "actual_count": value["n"]}


def plane_names(graph, case, geometry):
    source = case["public_child_strict"]["document_wire"]
    planes = source["support_planes"]["$tuple"]
    canonical = {"z": ([1., 0., 0.], [0., 1., 0.], [0., 0., 1.]),
                 "y": ([1., 0., 0.], [0., 0., -1.], [0., 1., 0.]),
                 "x": ([0., 0., -1.], [0., 1., 0.], [1., 0., 0.])}
    selected = graph.fields(graph.fields(geometry["profile"])["pd_f78"], "moCompRefPlane_c")
    native_plane_id = selected["ff0"]["f00"]
    result = {}
    selected_plane = None
    for axis, expected in canonical.items():
        matches = []
        for row in planes:
            frame = row["transform"]
            vectors = tuple([scalar(frame[key][coordinate]) for coordinate in ("x", "y", "z")] for key in ("x_axis", "y_axis", "z_axis"))
            if all(scalar(frame["origin"][key]) == 0. for key in ("x", "y", "z")) and vectors == expected:
                matches.append(row)
        row = one(matches, "canonical principal support plane " + axis)
        result[axis] = row["name"]
        if row["id"] == "sldprt:plane:" + str(native_plane_id):
            require(axis == "z", "portable source sketch does not use the canonical front support")
            selected_plane = row
    require(selected_plane is not None, "portable source sketch support does not resolve to its actual child plane")
    return result, selected_plane


def drawing_owners(graph, case, geometry, binding):
    drawing = case["public_drawing_layout"]["document_wire"]["drawing"]
    sheet, = drawing["sheets"]["$tuple"]
    view_wire, = sheet["views"]["$tuple"]
    reference_wire, = drawing["model_refs"]["$tuple"]
    document = graph.fields(case["typed_drawing"]["root"], "uiDrawingDoc_c")
    model_ref = document["model"]
    model = graph.fields(model_ref, "moDrawing_c")
    sheet_ref = model["f1430"]
    sheet_fields = graph.fields(sheet_ref, "moDrSheet")
    view = one([row for row in graph.children(sheet_ref) if row["identity"]["class"] == "moAbsoluteView"], "actual linked model view")
    view_ref, view_fields = view["identity"], view["fields"]
    require(graph.name(view_ref) == view_wire["name"] and graph.name(sheet_ref) == sheet["name"], "portable source captions disagree between typed ownership and public layout")
    internal = graph.node(view_fields["f5d8"], "moReferenceInternal_c")
    declared = file_origin(graph, internal["fields"]["f3b0"])
    child_header = graph.fields(case["typed_child"]["header"], "moHeader_c")
    child_file = file_origin(graph, child_header["f38"])
    require(binding["case"] == case["case"] and binding["child_sha256"] == case["child"]["sha256"]
            and binding["drawing_sha256"] == case["drawing"]["sha256"], "portable source native pair binding has different artifact custody")
    require(same_path(declared["path"], binding["resolved_child_path"])
            and same_path(reference_wire["source_path"], binding["resolved_child_path"]),
            "portable source drawing declaration differs from the actual hash-bound paired child resolution")
    config = internal["fields"]["f3c0"]
    name = graph.text(config["f08"])
    configs = case["typed_child"]["configuration_info"]["configurations"]
    active = one([row for row in configs if row["selected_by_f360"] and row["selected_by_f368"]], "actual selected child configuration")
    require(name == active["name"] == child_file["configuration_name"] == view_wire["configuration_name"] == binding["configuration_name"] and config["f10"] == active["native_object_id"] == child_file["configuration_id"],
            "portable source drawing configuration does not resolve to the actual child selection")
    displays = graph.members("moDisplayProfileFeature_c")
    require(len(displays) == 1, "portable source has multiple or absent displayed profiles")
    display = displays[0]["fields"]
    wrapper = graph.fields(display["f48"], "moCompProfile_c")
    require(wrapper["ff0"] == {"f00": geometry["origin"]["native_id"], "f08": geometry["origin"]["creation_time"]["value"]},
            "portable source displays another child sketch or creation event")
    chain = graph.fields(wrapper["f58"], "moChainComponent_c")
    reference_chain = graph.fields(chain["f20"], "moReferenceChain_c")
    entries = graph.fields(reference_chain["f08"], "moExtFeatureList_c")
    require(entries["n"] == len(entries["f08"]) == 1, "portable source profile has a nested occurrence path")
    external_ref = entries["f08"][0]["o"]
    external = graph.fields(external_ref, "moExtFeature_c")
    require(external_ref == internal["fields"]["f4f8"] and external["f50"]["$node"] == internal["identity"] and chain["owner"] == model_ref,
            "portable source profile component path lost its actual view or drawing owner")
    require(display["f40"]["$node"] == view_ref and display["f30"] == view_fields["f630"], "portable source profile is published in another view or detail folder")
    require(display["n1e0"] == 0 and not display["f1e0"] and display["ff8"] is None and display["linked"] == 0,
            "portable source profile has authored ghost geometry or linked display state")
    drawing_header_ref = model["fa8"]
    drawing_header = graph.fields(drawing_header_ref, "moHeader_c")
    drawing_file = file_origin(graph, drawing_header["f38"])
    require(drawing_file["kind"] == 4 and child_file["kind"] == 2, "portable source file kinds do not match the drawing and child")
    support_names = {"detail": graph.name(view_fields["f630"])}
    support_owners = []
    for role, profile_key in (("sheet", "f7c8"), ("model", "fde0")):
        profile_ref = view_fields[profile_key]
        profile = graph.fields(profile_ref, "moProfileFeature_c")
        selected = graph.fields(profile["pd_f78"], "moCompRefPlane_c")
        plane = graph.node(selected["ff8"], "moRefPlane_c")
        component = graph.fields(selected["f58"], "moUnitComponent_c")
        require(selected["ff0"] == {"f00": -1, "f08": 2592000}, "portable source inline view support has another persistent-reference mode")
        require(profile["owner"]["$node"] == view_ref and plane["fields"]["owner"]["$node"] == view_ref
                and component["owner"] == model_ref and component["has_ext"] == 0,
                "portable source inline view support lost its actual view or drawing owner")
        require(sum(row["identity"] == plane["identity"] for row in graph.children(view_ref)) == 1,
                "portable source inline view support plane is not published once in the actual view")
        support_names[role + "_profile"] = graph.name(profile_ref)
        support_names[role + "_plane"] = graph.name(plane["identity"])
        support_owners.append({"role": role, "profile": profile_ref["$node"], "plane": plane["identity"],
                               "component": selected["f58"]["$node"], "actual_plane_id": plane["fields"]["f08"],
                               "retained_preallocation_reference": selected["ff0"], "physical_plane_alias": True})
    return {"drawing_wire": drawing, "view": view_ref, "sheet": sheet_ref["$node"], "model": model_ref["$node"],
            "drawing_header": drawing_header_ref["$node"], "drawing_file": drawing_file, "child_file": child_file,
            "configuration": active, "support_names": support_names, "support_owners": support_owners, "property_view": graph.text(sheet_fields["f3d0"]),
            "sheet_geometry": {"owner": sheet_ref["$node"], "width_m": scalar(sheet_fields["f3f0"]), "height_m": scalar(sheet_fields["f3e8"]),
                               "scale_ratio": [scalar(sheet_fields["f3f8"]), scalar(sheet_fields["f400"])]},
            "resolved_child": {"path": declared["path"], "model_name": declared["model_name"], "binding": binding,
                               "independent_header_self_path_equal": same_path(declared["path"], child_file["path"])},
            "display": displays[0]["identity"], "internal_reference": internal["identity"], "source_names_used_for_selection": False}
