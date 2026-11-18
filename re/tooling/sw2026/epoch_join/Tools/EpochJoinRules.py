from __future__ import annotations

from pathlib import PureWindowsPath


def concrete(identity, names):
    return (type(identity) is dict and identity.get("class") in names
            and identity.get("schema") == 1 and identity.get("concrete_runtime_class") is True)


def text(value):
    if type(value) is str:
        return value
    if type(value) is dict and value.get("kind") == "CString" and type(value.get("text")) is str:
        return value["text"]
    raise ValueError("epoch join text has no actual supported owner")


def component_binding(row, display):
    records = display["component_reference_closure"]
    owners = {record["identity"]["object_index"]: record for record in records}
    if len(owners) != len(records):
        raise ValueError("epoch join has duplicate component-map identities")
    def fields(identity, name):
        if not concrete(identity, {name}):
            raise ValueError("epoch component path has no concrete current " + name)
        record = owners[identity["object_index"]]
        if record["identity"] != identity:
            raise ValueError("epoch component-map identity differs")
        return record["fields"]
    chain = fields(display["wrapper_fields"]["f58"], "moChainComponent_c")
    reference = fields(chain["f20"], "moReferenceChain_c")
    targets = fields(reference["f08"], "moExtFeatureList_c")
    count = targets["n"]
    if type(count) is not int or count != len(targets["f08"]) or count != 1:
        raise ValueError("epoch component path is not the scoped single actual target")
    external_id = targets["f08"][0]["o"]
    external = fields(external_id, "moExtFeature_c")
    model = row["actual_drawing_model"]
    checks = {
        "concrete_drawing_owner": concrete(model, {"moDrawing_c"}),
        "concrete_component_profile": concrete(display["component_profile"], {"moCompProfile_c"}),
        "concrete_view_reference": concrete(row["actual_view_internal_reference"], {"moReferenceInternal_c"}),
        "reference_f24_is_ordinary_zero": reference["f24"] == 0,
        "chain_and_reference_have_actual_model_owner": chain["owner"] == row["view_reference_fields"]["owner"] == model,
        "external_target_is_actual_view_external": external_id == row["view_reference_fields"]["f4f8"],
        "external_backlink_is_actual_view_reference": external["f50"] == row["actual_view_internal_reference"],
        "actual_display_folder": display["display_fields"]["f30"] == display["actual_folder"],
        "actual_display_view": display["display_fields"]["f40"] == display["actual_display_view"] == row["actual_view"],
        "actual_display_component_wrapper": display["display_fields"]["f48"] == display["component_profile"],
    }
    actual_stamp = chain.get("f30")
    view_stamp = row["view_reference_fields"].get("f3f0")
    return {"passed": all(checks.values()), "checks": checks,
            "actual_chain": display["wrapper_fields"]["f58"], "actual_reference_chain": chain["f20"],
            "actual_external_target": external_id, "raw_chain_stamp": actual_stamp,
            "raw_view_reference_stamp": view_stamp, "reference_f20": reference["f20"],
            "notional_stamp_formula_matches": (actual_stamp == (101 + view_stamp) & 0xffffffff)
                if type(actual_stamp) is int and type(view_stamp) is int else None,
            "notional_stamp_is_diagnostic_only": True,
            "identity_domain": "one actual drawing Definition archive map"}


def path_config_binding(row, case):
    declared, self_file = row["declared_reference_file"], row["child_self_file"]
    configurations = row["child_configuration_metadata"]["configurations"]
    owners = row["child_configuration_owners"]
    selector = row["view_reference_fields"]["f3c0"]
    name = text(selector["f08"])
    if len(configurations) != 1 or len(owners) != 1:
        raise ValueError("epoch configuration join requires one actual selected configuration")
    config, owner = configurations[0], owners[0]
    expected_path = PureWindowsPath(case["paths"]["child"])
    checks = {
        "actual_declared_reference_file": declared.get("available") is True,
        "actual_child_self_file": self_file.get("available") is True,
        "exact_native_resolved_path": PureWindowsPath(declared["native_file_path"]) == expected_path,
        "scoped_generated_child_self_path": PureWindowsPath(self_file["native_file_path"]) == expected_path,
        "actual_model_names": declared["native_model_name"] == self_file["native_model_name"] == row["actual_child_model"]["native_name"],
        "actual_part_file_kind": declared["shared_fields"]["f20"] == self_file["shared_fields"]["f20"] == 2,
        "actual_creation_identity": declared["shared_fields"]["f28"] == self_file["shared_fields"]["f28"]
            == row["child_clock_owners"]["model_header"]["SelfCreatedAt"],
        "complete_configuration_metadata": row["child_configuration_metadata"]["status"] == "complete",
        "actual_configuration_manager": concrete(row["child_configuration_manager"], {"moConfigurationMgr_c"}),
        "actual_configuration_directory": row["child_configuration_directory_count"] == 1,
        "concrete_configuration_owner": concrete(owner["identity"], {"moPartConfiguration_c", "moConfiguration_c"}),
        "configuration_name": config["name"] == owner["name"] == name == case["configuration"],
        "configuration_id": type(selector["f10"]) is int and config["native_object_id"] == owner["native_object_id"] == selector["f10"],
        "actual_selected_configuration_aliases": config["selected_by_f360"] is True and config["selected_by_f368"] is True
            and owner["selected_by_f360"] is True and owner["selected_by_f368"] is True,
    }
    return {"passed": all(checks.values()), "checks": checks, "actual_configuration": owner,
            "actual_selector": selector, "native_reference_path": declared["native_file_path"],
            "child_self_path": self_file["native_file_path"],
            "creation_identity": declared["shared_fields"]["f28"],
            "scope": "generated exact-path epoch pairs; no equality rule imposed on unrelated original source metadata",
            "cmgr_global_part_owner_alias_admitted": False}


def check_row(row, case, expected_origin, clock):
    checks = {
        "complete_observation": row.get("observation_complete") is True,
        "complete_definition_byte_identity": row.get("drawing_definition_byte_identity") is True,
        "drawing_immutable": row.get("drawing_unchanged") is True,
        "child_immutable": row.get("child_unchanged") is True,
        "complete_child_config": row.get("child_config_complete") is True,
        "complete_child_resolved": row.get("child_resolved_complete") is True,
        "actual_child_part": concrete(row.get("actual_child_model"), {"moPart_c"}),
        "child_clock_owners_match_independent_collector": row.get("child_clock_owners") == clock["child"],
        "drawing_clock_owners_match_independent_collector": row.get("drawing_clock_owners") == clock["drawing"],
    }
    displays = row.get("profile_displays", [])
    checks["one_actual_display"] = len(displays) == 1
    details = {}
    if len(displays) == 1:
        display = displays[0]
        target = display.get("actual_child_profile")
        checks.update({
            "actual_origin_class": concrete(target, {"moOriginProfileFeature_c"}),
            "actual_native_origin_id": type(expected_origin) is int and target is not None and target.get("native_f08") == expected_origin,
            "unique_owned_profile": display.get("actual_child_id_match_count") == 1,
            "actual_origin_creation_event": display.get("creation_log_epoch_equal") is True,
            "actual_clock_collector_origin": display.get("native_feature_id") == clock["actual_origin_id"]
                and display.get("native_creation_stamp") == clock["actual_origin_creation_time"],
            "source_names_not_used_for_id_selection": display.get("id_selection_uses_source_names") is False,
        })
        component = component_binding(row, display)
        path_config = path_config_binding(row, case)
        checks["component_chain"] = component["passed"]
        checks["external_path_and_config_owner"] = path_config["passed"]
        details = {"component": component, "path_configuration": path_config,
                   "actual_origin": target, "actual_creation_time": display.get("actual_child_creation_log_epoch")}
    return {"passed": all(checks.values()), "checks": checks,
            "failed_checks": [name for name, passed in checks.items() if not passed], **details}
