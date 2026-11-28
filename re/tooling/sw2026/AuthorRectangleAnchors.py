from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

from AuthorCurves import CurveAuthor, Recorder, digest, require, write_json


SCHEMA = "kit.sw2026.rectangle-anchor-source.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
TOOLS = {Path(__file__).name, "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"}
SKETCH = "AnchorSketch"
BOSS = "AnchorBoss"
PARAMETERS = ("D1@" + SKETCH, "D2@" + SKETCH, "D1@" + BOSS)
ROLES = ("Original", "WidthEdit", "HeightEdit")


def read_job(path, sha):
    require(digest(path) == sha, "anchor source job changed")
    job = json.loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and
            job["control_sha256"] == CONTROL and job["writer_output_count"] == 0,
            "anchor source job profile differs")
    require(set(job["tools_sha256"]) == TOOLS and Path(__file__).resolve().parent == path.parent / "Tools",
            "use the complete frozen oracle tools")
    for name, expected in job["tools_sha256"].items():
        require(digest(path.parent / "Tools" / name) == expected, f"anchor source tool changed: {name}")
    require(digest(path.parent / "Control.SLDPRT") == CONTROL, "anchor source control changed")
    require(len(job["cases"]) == 2 and tuple(row["kind"] for row in job["cases"]) == ("corner", "center"),
            "the discovery job requires a corner and a centered rectangle")
    for case in job["cases"]:
        require(set(case) == {"kind", "width_m", "height_m", "depth_m", "edit_width_m", "edit_height_m"},
                "unexpected rectangle source fields")
        require(all(type(value) in (int, float) and math.isfinite(value) and 0.001 < value < 0.25
                    for name, value in case.items() if name != "kind"), "rectangle lengths are outside the measured profile")
        require(case["width_m"] != case["edit_width_m"] and case["height_m"] != case["edit_height_m"],
                "width and height edits must each change their driving value")
    return job


def dimension_values(case, role):
    return (case["edit_width_m" if role == "WidthEdit" else "width_m"],
            case["edit_height_m" if role == "HeightEdit" else "height_m"], case["depth_m"])


def rectangle_points(kind, width, height):
    lower = (0.0, 0.0) if kind == "corner" else (-width / 2, -height / 2)
    upper = (lower[0] + width, lower[1] + height)
    return lower, (upper[0], lower[1]), upper, (lower[0], upper[1])


class RectangleAuthor(CurveAuthor):
    def relation_graph(self):
        manager = self.get(self.sketch, "RelationManager")
        rows = []
        for relation in self.get(manager, "GetRelations", 0) or ():
            related = list(self.get(relation, "GetEntities") or ())
            kinds = list(self.get(relation, "GetEntitiesType") or ())
            require(len(related) == len(kinds) == self.get(relation, "GetEntitiesCount"),
                    "native rectangle relation has inconsistent entity counts")
            rows.append({"kind": int(self.get(relation, "GetRelationType")),
                         "suppressed": bool(self.get(relation, "Suppressed")),
                         "entity_types": kinds, "entity_ids": [list(self.get(item, "GetID")) for item in related]})
        require(self.get(manager, "GetRelationsCount", 0) == len(rows), "native rectangle relation count differs")
        return rows

    def points_at_origin(self, segments):
        points = list(self.get(self.sketch, "GetSketchPoints2") or ())
        for segment in segments:
            line = self.typed(segment, "SketchLine")
            points.extend(self.get(line, name) for name in ("GetStartPoint2", "GetEndPoint2"))
        result = {}
        for point in points:
            if all(abs(value) < 1e-10 for value in self.point(point)):
                result[tuple(self.get(point, "GetID"))] = point
        return result

    def anchor(self, segments, extension):
        self.get(self.model, "ClearSelection2", True)
        require(self.get(extension, "SelectByID2", "Point1@Origin", "EXTSKETCHPOINT",
                         0.0, 0.0, 0.0, False, 0, self.sw.nothing(), 0), "native model origin selection failed")
        selection = self.get(self.model, "SelectionManager")
        origin = self.typed(self.get(selection, "GetSelectedObject6", 1, -1), "SketchPoint")
        points = self.points_at_origin(segments)
        local = [point for point in points.values() if self.get(self.app, "IsSame", point, origin) == 0]
        require(len(local) == 1, "rectangle must have one native local point at its anchor")
        point, = local
        self.rec.data["anchor_selection"] = {"origin_id": self.get(origin, "GetID"), "local_id": self.get(point, "GetID")}
        self.rec.flush()
        require(self.get(point, "Select4", True, self.sw.nothing()), "native local anchor selection failed")
        require(self.get(selection, "GetSelectedObjectCount2", -1) == 2, "origin and local point were not both selected")
        self.get(self.model, "SketchAddConstraints", "sgCOINCIDENT")
        self.get(self.model, "ClearSelection2", True)

    def add_dimension(self, segment, value, at):
        self.get(self.model, "ClearSelection2", True)
        require(self.get(segment, "Select4", False, self.sw.nothing()), "rectangle edge selection failed")
        display = self.get(self.model, "AddDimension2", *at, 0.0)
        require(display is not None, "rectangle display dimension was not created")
        dimension = self.get(display, "GetDimension2", 0)
        require(dimension is not None and self.get(dimension, "DrivenState") == 2,
                "rectangle dimension is not driving")
        self.rec.close_number("new driving length", self.get(dimension, "SystemValue"), value)

    def build(self, controller, case):
        self.model = self.rec.call("new rectangle source part", controller.new_part)
        width, height, depth = dimension_values(case, "Original")
        extension = self.get(self.model, "Extension")
        require(self.get(extension, "SelectByID2", "Front Plane", "PLANE", 0.0, 0.0, 0.0,
                         False, 0, self.sw.nothing(), 0), "native Front Plane selection failed")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None and not self.get(manager, "AddToDB"), "native interactive sketch creation is unavailable")
        p0, _, p2, _ = rectangle_points(case["kind"], width, height)
        method, first = ("CreateCornerRectangle", p0) if case["kind"] == "corner" else ("CreateCenterRectangle", (0.0, 0.0))
        segments = list(self.get(manager, method, *first, 0.0, *p2, 0.0) or ())
        ordinary = [segment for segment in segments if not self.get(segment, "ConstructionGeometry")]
        require(len(ordinary) == 4, "native rectangle needs four regular edges")
        self.rec.data["automatic_relations"] = self.relation_graph()
        self.rec.flush()
        for axis, value, at in ((0, width, (p0[0] + width / 2, p0[1] - height * 0.3)),
                                (1, height, (p2[0] + width * 0.3, p0[1] + height / 2))):
            edges = []
            for segment in ordinary:
                line = self.typed(segment, "SketchLine")
                start, end = [self.point(self.get(line, name)) for name in ("GetStartPoint2", "GetEndPoint2")]
                if abs(start[axis] - end[axis]) > 1e-9:
                    edges.append((start[1 - axis], segment))
            require(len(edges) == 2, "native rectangle edge directions differ")
            edge = min(edges, key=lambda row: row[0])[1] if axis == 0 else max(edges, key=lambda row: row[0])[1]
            self.add_dimension(edge, value, at)
        state = int(self.get(self.sketch, "GetConstrainedStatus"))
        self.rec.data["constraint_status_before_explicit_anchor"] = state
        self.rec.flush()
        if state == 2:
            self.anchor(segments, extension)
        require(self.get(self.sketch, "GetConstrainedStatus") == 3, "native anchored rectangle is not fully constrained")
        self.get(self.model, "ClearSelection2", True)
        self.get(manager, "InsertSketch", True)
        feature = self.created_sketch_feature()
        self.set(feature, "Name", SKETCH)
        require(self.get(feature, "Select2", False, 0), "native rectangle profile selection failed")
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureExtrusion3",
                        True, False, False, 0, 0, depth, 0.0, False, False, False, False,
                        0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        require(boss is not None, "native rectangle boss creation failed")
        self.set(boss, "Name", BOSS)

    def snapshot(self, case, role):
        require(self.get(self.model, "ForceRebuild3", False), "native rectangle source failed to rebuild")
        require(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount") == 0,
                "native rectangle source has rebuild diagnostics")
        width, height, depth = dimension_values(case, role)
        feature = self.get(self.model, "FeatureByName", SKETCH)
        self.sketch = self.get(feature, "GetSpecificFeature2")
        status = int(self.get(self.sketch, "GetConstrainedStatus"))
        require(status == 3, "anchored rectangle lost full constraint")
        geometry = self.geometry()
        points = rectangle_points(case["kind"], width, height)
        expected_edges = [tuple(sorted((start, end))) for start, end in zip(points, points[1:] + points[:1], strict=True)]
        actual_edges = [(row["start"], row["end"]) for row in geometry if not row["construction"]]
        require(len(actual_edges) == len(expected_edges), "native rectangle edge count differs")
        for actual in actual_edges:
            matches = [(edge, oriented) for edge in expected_edges for oriented in (edge, edge[::-1])
                       if all(abs(value - target) < 1e-10 for lhs, rhs in zip(actual, oriented, strict=True)
                              for value, target in zip(lhs, rhs, strict=True))]
            require(len(matches) == 1, "native segment does not match its intended rectangle edge")
            ((edge, expected),) = matches
            expected_edges.remove(edge)
            for left, right in zip(actual, expected, strict=True):
                for observed, want in zip(left, right, strict=True):
                    self.rec.close_number("anchored rectangle endpoint", observed, want)
        measured = {}
        for name, target in zip(PARAMETERS, (width, height, depth), strict=True):
            dimension = self.get(self.model, "Parameter", name)
            require(dimension is not None and self.get(dimension, "DrivenState") == 2 and not self.get(dimension, "ReadOnly"),
                    f"native dimension is not editable: {name}")
            measured[name] = float(self.get(dimension, "SystemValue"))
            self.rec.close_number(name, measured[name], target)
        tree = self.feature_tree(required_names=(SKETCH, BOSS))
        require(len(self.get(self.model, "GetBodies2", 0, False) or ()) == 1, "native rectangle requires one solid")
        mass = self.rec.call("measure native anchored rectangle", self.sw.mass, self.model)
        self.rec.close_number("rectangle solid volume", mass["volume"], width * height * depth, absolute=1e-16)
        self.rec.close_number("rectangle solid area", mass["area"], 2 * (width * height + width * depth + height * depth))
        center = ((points[0][0] + points[2][0]) / 2, (points[0][1] + points[2][1]) / 2, depth / 2)
        for value, target in zip(mass["com"], center, strict=True):
            self.rec.close_number("anchored solid center", value, target)
        return {"dimensions_m": measured, "constraint_status": status, "geometry": geometry,
                "relations": self.relation_graph(), "tree": tree, "mass_properties": mass, "body_count": 1}

    def edit(self, name, value):
        dimension = self.get(self.model, "Parameter", name)
        require(self.get(dimension, "SetSystemValue3", value, 1, self.sw.nothing()) == 0,
                f"driving rectangle edit failed: {name}")


def phase(root, case, name, prior):
    import Swapp
    from OracleIdentity import application_identity

    directory = root / case["kind"] / name
    directory.mkdir(parents=True, exist_ok=False)
    rec = Recorder(directory / "Record.json", {"case": case, "phase": name})
    result, controller, author, preference = {"passed": False, "files": {}, "observed": {}}, None, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle oracle", Swapp.sweep)
            controller = rec.call("start exact native rectangle oracle", Swapp.Sw)
            identity = rec.call("verify native rectangle oracle identity", application_identity, controller.app)
            require(identity["sha256"] == ORACLE and identity["version_matches"] and controller.revision == "34.5.2",
                    "native rectangle oracle build differs")
            result["oracle_identity"] = identity
            author = RectangleAuthor(controller.app, rec, Swapp)
            if name == "Author":
                preference = bool(author.get(author.app, "GetUserPreferenceToggle", 10))
                author.get(author.app, "SetUserPreferenceToggle", 10, False)
                require(not author.get(author.app, "GetUserPreferenceToggle", 10), "native dimension prompt remained enabled")
                author.build(controller, case)
            for role in ROLES:
                filename = role + ".SLDPRT"
                if name == "Author":
                    if role == "WidthEdit":
                        author.edit(PARAMETERS[0], case["edit_width_m"])
                    elif role == "HeightEdit":
                        author.edit(PARAMETERS[0], case["width_m"])
                        author.edit(PARAMETERS[1], case["edit_height_m"])
                    result["observed"][role] = author.snapshot(case, role)
                    target = directory / filename
                    status = rec.call("save native rectangle source sibling", controller.save_as, author.model, target)
                    require(tuple(status) == (True, 0, 0) and target.stat().st_size > 0, "native rectangle save failed")
                    result["files"][role] = {"sha256": digest(target), "bytes": target.stat().st_size, "status": list(status)}
                else:
                    source = directory.parent / "Author" / filename
                    require(digest(source) == prior["files"][role]["sha256"], "native rectangle source sibling changed")
                    model, error, warning = rec.call("fresh open native rectangle source sibling", controller.open, source, read_only=True)
                    require(model is not None and error == warning == 0 and Path(author.get(model, "GetPathName")).samefile(source),
                            "native rectangle fresh open failed or warned")
                    author.model = model
                    state = author.snapshot(case, role)
                    require(state["tree"] == prior["observed"][role]["tree"], "native rectangle source tree changed after reopen")
                    require(state["relations"] == prior["observed"][role]["relations"], "native rectangle relation bindings changed after reopen")
                    result["observed"][role] = state
                    result["files"][role] = prior["files"][role] | {"open_errors": error, "open_warnings": warning}
                    controller.close_doc(model)
                    author.model = None
                rec.data["result"] = result
                rec.flush()
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and preference is not None:
                try:
                    author.get(author.app, "SetUserPreferenceToggle", 10, preference)
                    require(bool(author.get(author.app, "GetUserPreferenceToggle", 10)) == preference,
                            "native dimension prompt preference restoration failed")
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                if author is not None and author.model is not None:
                    controller.close_doc(author.model)
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = dialogs.log
    result["passed"] = bool(result["passed"] and not dialogs.log and not rec.data["cleanup_errors"] and not result.get("controller_diagnostics"))
    for role, entry in result["files"].items():
        location = directory.parent / "Author" / (role + ".SLDPRT")
        require(entry["bytes"] == location.stat().st_size and entry["sha256"] == digest(location), "native rectangle sibling custody changed")
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def control(root, name, seed):
    from InspectFresh import healthy, inspect

    destination = root / name
    destination.mkdir()
    report = destination / "Record.json"
    result = inspect(seed)
    require(result["sha256"] == digest(seed) == CONTROL, "rectangle control file changed")
    write_json(report, result)
    return {"passed": healthy(result) and result["oracle_identity"]["sha256"] == ORACLE,
            "oracle_identity": result.get("oracle_identity"), "record_sha256": digest(report)}


def main():
    parser = argparse.ArgumentParser(description="Author and reopen native rectangle source controls")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    path = args.job.resolve()
    job = read_job(path, args.job_sha256)
    if args.verify_only:
        print(json.dumps({"verified": True, "native_processes": 0}))
        return 0
    output = path.parent / "RectangleAnchorResults"
    output.mkdir(exist_ok=False)
    seed = path.parent / "Control.SLDPRT"
    result = {"schema": SCHEMA, "job_sha256": args.job_sha256, "cases": {}, "writer_output_count": 0,
              "heldout_inputs_tested": 0, "native_acceptance": False}
    result["control_before"] = control(output, "ControlBefore", seed)
    try:
        if result["control_before"]["passed"]:
            for case in job["cases"]:
                row = result["cases"][case["kind"]] = {}
                row["author"] = phase(output, case, "Author", None)
                if row["author"]["passed"]:
                    row["reopen"] = phase(output, case, "Reopen", row["author"])
                write_json(output / "Progress.json", result)
    finally:
        result["control_after"] = control(output, "ControlAfter", seed)
    read_job(path, args.job_sha256)
    phases = [result["control_before"], *(item for row in result["cases"].values() for item in row.values()), result["control_after"]]
    identities = {(item["oracle_identity"]["process_id"], item["oracle_identity"]["process_creation_filetime"])
                  for item in phases if item.get("oracle_identity")}
    result["distinct_processes"] = len(identities)
    result["controls_healthy"] = all(result[name]["passed"] for name in ("control_before", "control_after"))
    result["source_measurement_passed"] = len(identities) == len(phases) == 6 and all(item["passed"] for item in phases)
    write_json(output / "Result.json", result)
    print(json.dumps({key: result[key] for key in ("distinct_processes", "controls_healthy", "source_measurement_passed")}))
    return 0 if result["source_measurement_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
