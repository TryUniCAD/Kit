from __future__ import annotations

from contextlib import contextmanager
from math import isclose, isfinite

import AuthorCurves as curves
import InspectFrontDrawingMap as native


PATH_FIELDS = frozenset(("reference_name", "resolved_reference_path"))
VOLATILE_FIELDS = frozenset(("child_update_stamp",))


def feature_tree(author, model):
    count = 0

    def walk(feature, parent, depth):
        nonlocal count
        while feature is not None:
            count += 1
            curves.require(count <= 1000 and depth < 20, "blind child tree exceeds its traversal bound")
            name = str(author.get(feature, "Name"))
            yield [name, str(author.get(feature, "GetTypeName2")), parent]
            yield from walk(author.get(feature, "GetFirstSubFeature"), name, depth + 1)
            feature = author.get(feature, "GetNextFeature" if parent is None else "GetNextSubFeature")

    return list(walk(author.get(model, "FirstFeature"), None, 0))


def complete_state(author, drawing, state):
    views = []
    view = author.typed(author.get(drawing, "GetFirstView"), "View")
    child = None
    while view is not None:
        curves.require(len(views) < 2, "blind layout has an unexpected extra view")
        annotations = []
        annotation = author.get(view, "GetFirstAnnotation3")
        while annotation is not None:
            curves.require(len(annotations) < 1000, "blind annotation walk exceeds its bound")
            typed = author.typed(annotation, "Annotation")
            annotations.append(int(author.get(typed, "GetType")))
            annotation = author.get(typed, "GetNext3")
        views.append({"view_name": str(author.get(view, "GetName2")), "annotation_types": annotations})
        actual_child = author.get(view, "ReferencedDocument")
        if actual_child is not None:
            curves.require(child is None, "blind drawing has an unexpected second child")
            child = actual_child
        next_view = author.get(view, "GetNextView")
        view = None if next_view is None else author.typed(next_view, "View")
    state["annotation_inventory"] = views
    state["child_feature_tree"] = [] if child is None else feature_tree(author, child)
    curves.require(len(views) == 2 and child is not None and state["child_feature_tree"],
                   "blind layout requires one complete model view and live child tree")
    curves.require(not any(row["annotation_types"] for row in views),
                   "source annotations require their complete semantic writer and comparison profile")
    return state


@contextmanager
def complete_observations():
    original_project, original_edit = native.project, native.edit_position

    def project(author, drawing, expected, staged_child, original_child, child_hash):
        state, request, child, paper = original_project(author, drawing, expected, staged_child, original_child, child_hash)
        return complete_state(author, drawing, state), request, child, paper

    def edit(author, model, drawing, request, child, paper, prior):
        state = complete_state(author, drawing, original_edit(author, model, drawing, request, child, paper, prior))
        curves.require(state["child_feature_tree"] == prior["child_feature_tree"]
                       and state["annotation_inventory"] == prior["annotation_inventory"],
                       "drawing edit changed its child history or annotation inventory")
        return state

    native.project, native.edit_position = project, edit
    try:
        yield
    finally:
        native.project, native.edit_position = original_project, original_edit


def compare_values(source, generated, path="state"):
    mismatches = []
    count = 0

    def visit(left, right, location):
        nonlocal count
        count += 1
        if type(left) in (int, float) and type(right) in (int, float):
            absolute = 1e-15 if "child_volume_m3" in location or "child_area_m2" in location else 1e-12
            relative = 5e-7 if "child_" in location else 1e-9
            if not isfinite(left) or not isfinite(right) or not isclose(left, right, rel_tol=relative, abs_tol=absolute):
                mismatches.append({"path": location, "source": left, "generated": right})
            return
        if isinstance(left, dict) and isinstance(right, dict):
            if set(left) != set(right):
                mismatches.append({"path": location, "source_keys": sorted(left), "generated_keys": sorted(right)})
                return
            for key in sorted(left):
                if location.endswith(".view") and key in PATH_FIELDS | VOLATILE_FIELDS:
                    continue
                visit(left[key], right[key], location + "." + key)
            return
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            if len(left) != len(right):
                mismatches.append({"path": location, "source_length": len(left), "generated_length": len(right)})
                return
            for index, (first, second) in enumerate(zip(left, right, strict=True)):
                visit(first, second, f"{location}[{index}]")
            return
        if type(left) is not type(right) or left != right:
            mismatches.append({"path": location, "source": left, "generated": right})

    visit(source, generated, path)
    return {"passed": not mismatches, "compared_value_count": count, "mismatches": mismatches}


def compare_lanes(source, generated):
    reports = []
    for phase_name, states in (("open_edit_save", ("initial", "rebuilt", "edited")), ("fresh_reopen", ("initial", "rebuilt"))):
        for state in states:
            left, right = source.get(phase_name), generated.get(phase_name)
            if left is None or right is None or state not in left or state not in right:
                reports.append({"passed": False, "path": phase_name + "." + state, "reason": "required native state was not measured"})
                continue
            reports.append(compare_values(left[state], right[state], phase_name + "." + state))
        if source.get(phase_name) is not None and generated.get(phase_name) is not None:
            reports.append(compare_values(source[phase_name].get("tree"), generated[phase_name].get("tree"), phase_name + ".tree"))
    return {"passed": bool(source["passed"] and generated["passed"] and all(row["passed"] for row in reports)),
            "reports": reports, "path_role_fields": sorted(PATH_FIELDS), "volatile_fields": sorted(VOLATILE_FIELDS),
            "path_and_child_hashes_checked_separately": True}
