from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import InspectCustomComponentNameRetry01 as retry

original = retry.original
baseline = retry.baseline
VERIFY = retry.verify


def split_name(value):
    base, separator, suffix = value.rpartition("-")
    baseline.require(
        bool(base)
        and separator == "-"
        and suffix.isascii()
        and suffix.isdecimal()
        and 1 <= int(suffix) <= 99999
        and str(int(suffix)) == suffix
        and not any(character in value for character in ("/", "\\", "^")),
        "base-name retry requires an ordinary top-level instance name",
    )
    return base, int(suffix)


def verify(path, expected):
    job, plan = VERIFY(path, expected)
    baseline.require(
        job.get("name_setter_method")
        == "base-name-with-unchanged-authored-full-name-predicate"
        and job.get("prior_retry_trial_sha256")
        == "4fbd3b22ea882e67585eb5450f42204fed8547ab2d09cbc76b8362c2ed90a2c5"
        and job.get("prior_retry_result_sha256")
        == "da64946316bcea15fa51d1dd3662994b8f3ca23ecff9ade283b906f3e0886800"
        and plan["custom_occurrence_names"] == ["AuthoredAxisA-1", "AuthoredAxisB-2"]
        and baseline.digest(retry.ROOT / "FrozenPrediction01.json")
        == "2ed860d27f02eafb59f8e34d672ab68d9b071d9e94d35f3b6bd72badaf78ba90",
        "the independently authored full-name prediction must remain unchanged",
    )
    for value in plan["custom_occurrence_names"]:
        split_name(value)
    return job, plan


def observed_names(author, model, component):
    path = Path(str(author.get(component, "GetPathName")))
    return original.name_probe.names(author, model, path)


def checked_names(value, native_id):
    baseline.require(
        value["observation_complete"]
        and all(
            row["component_path_matches_actual_child"] for row in value["references"]
        ),
        "matched feature and component name observations are incomplete",
    )
    matched = [row for row in value["references"] if row["component_id"] == native_id]
    baseline.require(len(matched) == 1, "rename lost its exact live feature owner")
    return matched[0]


def rename_selected(author, model, component, name, preference):
    import Swapp

    baseline.require(
        preference == 18
        and not bool(author.get(author.app, "GetUserPreferenceToggle", preference)),
        "the owned name-update preference must already be false",
    )
    native_id = int(author.get(component, "GetID"))
    row = {
        "native_id": native_id,
        "expected_full_name": name,
        "method": "base-name-with-unchanged-authored-full-name-predicate",
        "before": str(author.get(component, "Name2")),
    }
    author.rec.data.setdefault("rename_observations", []).append(row)
    row["matched_before"] = observed_names(author, model, component)
    author.rec.flush()
    before = checked_names(row["matched_before"], native_id)
    base, suffix = split_name(name)
    _, old_suffix = split_name(row["before"])
    row.update(
        setter_input=base, expected_suffix=suffix, actual_before_suffix=old_suffix
    )
    author.rec.flush()
    baseline.require(
        suffix == old_suffix
        and before["feature_name"] == before["component_name2"] == row["before"],
        "the explicit desired ordinal differs from the actual source occurrence",
    )
    author.get(model, "ClearSelection2", True)
    baseline.require(
        bool(author.get(component, "Select4", False, Swapp.nothing(), False)),
        "actual component cannot be selected for the base-name setter",
    )
    manager = author.typed(author.get(model, "SelectionManager"), "ISelectionMgr")
    baseline.require(
        int(author.get(manager, "GetSelectedObjectCount2", -1)) == 1,
        "base-name selection is not singular",
    )
    selected = author.typed(
        author.get(manager, "GetSelectedObject6", 1, -1), "Component2"
    )
    owner = author.typed(
        author.get(manager, "GetSelectedObjectsComponent4", 1, -1), "Component2"
    )
    row["selected_component_id"] = int(author.get(selected, "GetID"))
    row["selected_owner_id"] = int(author.get(owner, "GetID"))
    author.rec.flush()
    baseline.require(
        row["selected_component_id"] == row["selected_owner_id"] == native_id,
        "base-name selection lost the exact occurrence owner",
    )
    author.rec.call(
        "set actual selected component base Name2",
        setattr,
        component,
        "Name2",
        base,
        parameters={
            "value": base,
            "expected_full_name": name,
            "native_id": native_id,
        },
    )
    row["after"] = str(author.get(component, "Name2"))
    row["matched_after"] = observed_names(author, model, component)
    author.rec.flush()
    after = checked_names(row["matched_after"], native_id)
    baseline.require(
        after["feature_name"] == after["component_name2"] == row["after"] == name,
        "base-name setter did not retain the original explicit full name",
    )
    others_before = {
        value["component_id"]: (value["feature_name"], value["component_name2"])
        for value in row["matched_before"]["references"]
        if value["component_id"] != native_id
    }
    others_after = {
        value["component_id"]: (value["feature_name"], value["component_name2"])
        for value in row["matched_after"]["references"]
        if value["component_id"] != native_id
    }
    baseline.require(
        others_after == others_before, "base-name setter changed another occurrence"
    )
    author.get(model, "ClearSelection2", True)
    baseline.require(
        not bool(author.get(author.app, "GetUserPreferenceToggle", preference)),
        "base-name setter changed the application preference",
    )
    return row


retry.verify = verify
original.rename_selected = rename_selected


if __name__ == "__main__":
    raise SystemExit(retry.main())
