from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path

import Swapp
from AuthorCurves import CurveAuthor, Recorder, digest, require, write_json
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


PLANES = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}
PROFILE = "RevolveSketch"
BOSS = "OrdinaryBossRevolve"


def validate_cases(specs):
    cases = specs["cases"]
    require(specs["schema"] == "kit.sw2026.ordinary-revolve-specs.v1", "unexpected revolve source specification schema")
    require([case["split"] for case in cases] == ["discovery"] * 3 + ["heldout"] * 2, "revolve cohort requires three discovery and two held-out cases")
    require(len({case["name"] for case in cases}) == len(cases), "revolve source names must be distinct")
    for case in cases:
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,49}", case["name"]) is not None, "unsafe revolve source name")
        require(case["plane"] in PLANES and isinstance(case["reverse"], bool), "invalid sketch plane or direction")
        inner, outer = case["radius_m"]
        low, high = case["axial_m"]
        axis_low, axis_high = case["axis_axial_m"]
        angle, edit = case["angle_deg"], case["edit_angle_deg"]
        require(all(math.isfinite(v) for v in (inner, outer, low, high, axis_low, axis_high, case["axis_x_m"], angle, edit)), "nonfinite input")
        require(0 < inner < outer and axis_low < low < high < axis_high and axis_high - axis_low >= 1e-8, "invalid closed rectangle or construction axis")
        require(0 < angle <= 360 and 0 < edit < 360 and angle != edit, "invalid initial or edited angle")
    full, forward, reverse, *heldout = cases
    require(full["angle_deg"] == 360 and not full["reverse"], "first discovery source must be a forward full turn")
    pair = ("plane", "radius_m", "axial_m", "axis_axial_m", "axis_x_m", "angle_deg", "edit_angle_deg")
    require(forward["angle_deg"] < 360 and not forward["reverse"] and reverse["reverse"] and all(forward[key] == reverse[key] for key in pair), "discovery partial turn must include a direction-only pair")
    for key in ("radius_m", "axial_m", "axis_axial_m", "axis_x_m", "angle_deg"):
        require(heldout[0][key] != heldout[1][key] and all(case[key] not in (full[key], forward[key]) for case in heldout), f"held-out {key} must vary independently from discovery")
    require(all(case["angle_deg"] < 360 for case in heldout), "initial held-out scope is partial one-direction turns")
    return cases


def geometry(case, angle_degrees, sign):
    inner, outer = case["radius_m"]
    low, high = case["axial_m"]
    angle = math.radians(angle_degrees)
    delta = outer**2 - inner**2
    height = high - low
    volume = height * angle * delta / 2
    area = height * angle * (inner + outer) + angle * delta
    if angle_degrees == 360:
        return volume, area, [case["axis_x_m"], (low + high) / 2, 0.0]
    area += 2 * height * (outer - inner)
    radius_factor = 2 * (outer**3 - inner**3) / (3 * angle * delta)
    center = [case["axis_x_m"] + radius_factor * math.sin(angle), (low + high) / 2, sign * radius_factor * (1 - math.cos(angle))]
    return volume, area, center


class RevolveAuthor(CurveAuthor):
    def world(self, xyz):
        inverse = self.get(self.get(self.sketch, "ModelToSketchTransform"), "Inverse")
        utility = self.get(self.app, "GetMathUtility")
        array = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, xyz)
        point = self.get(utility, "CreatePoint", array)
        return [float(value) for value in self.get(self.get(point, "MultiplyTransform", inverse), "ArrayData")]

    def axis_data(self, raw):
        segment = self.typed(raw, "SketchSegment")
        line = self.typed(segment, "SketchLine")
        require(int(self.get(segment, "GetType")) == 0 and bool(self.get(segment, "ConstructionGeometry")), "revolve axis is not a construction line")
        points = [self.point(self.get(line, name)) for name in ("GetStartPoint2", "GetEndPoint2")]
        return {"name": str(self.get(segment, "GetName")), "id": list(self.get(segment, "GetID")), "points": points}

    def check_axis(self, raw, case):
        observed = self.axis_data(raw)
        for point, height in zip(observed["points"], case["axis_axial_m"], strict=True):
            for coord, actual, expected in zip("xyz", point, (case["axis_x_m"], height, 0.0), strict=True):
                self.rec.close_number("axis endpoint " + coord, actual, expected)
        owner = self.get(self.typed(raw, "SketchSegment"), "GetSketch")
        require(owner is not None, "selected revolve line has no sketch owner")
        owner_ids = [tuple(self.get(segment, "GetID")) for segment in self.get(owner, "GetSketchSegments") or ()]
        profile_segments = self.get(self.sketch, "GetSketchSegments") or ()
        profile_ids = [tuple(self.get(segment, "GetID")) for segment in profile_segments]
        require(len(profile_ids) == len(set(profile_ids)) == 5 and sorted(profile_ids) == sorted(owner_ids) and tuple(observed["id"]) in profile_ids, "revolve line does not belong to the exact five-segment profile sketch")
        observed["owner_segment_ids"] = owner_ids
        return observed

    def build(self, case, session):
        self.model = self.rec.call("new part", session.new_part)
        extension = self.get(self.model, "Extension")
        require(self.get(extension, "SelectByID2", PLANES[case["plane"]], "PLANE", 0.0, 0.0, 0.0, False, 0, Swapp.nothing(), 0), "default sketch plane selection failed")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        self.sketch = self.get(manager, "ActiveSketch")
        require(self.sketch is not None, "new part has no active sketch")
        inner, outer = case["radius_m"]
        low, high = case["axial_m"]
        axis_low, axis_high = case["axis_axial_m"]
        x = case["axis_x_m"]
        self.set(manager, "AddToDB", True)
        try:
            rectangle = self.get(manager, "CreateCornerRectangle", x + inner, low, 0.0, x + outer, high, 0.0)
            require(rectangle is not None and len(rectangle) == 4, "rectangle creation did not return four sides")
            axis = self.get(manager, "CreateCenterLine", x, axis_low, 0.0, x, axis_high, 0.0)
            require(axis is not None, "construction centerline creation failed")
            before = self.axis_data(axis)
        finally:
            self.set(manager, "AddToDB", False)
        self.get(manager, "InsertSketch", True)
        sketch_feature = self.created_sketch_feature()
        self.set(sketch_feature, "Name", PROFILE)
        self.sketch = self.get(sketch_feature, "GetSpecificFeature2")
        self.get(self.model, "ClearSelection2", True)
        selection = self.get(self.model, "SelectionManager")
        self.set(selection, "EnableContourSelection", False)
        require(self.get(extension, "SelectByID2", PROFILE, "SKETCH", 0.0, 0.0, 0.0, False, 0, Swapp.nothing(), 0), "mark-0 profile selection failed")
        point = self.world([x, (axis_low + axis_high) / 2, 0.0])
        require(self.get(extension, "SelectByID2", f"{before['name']}@{PROFILE}", "EXTSKETCHSEGMENT", *point, True, 4, Swapp.nothing(), 0), "explicit mark-4 centerline selection failed")
        marks = {mark: int(self.get(selection, "GetSelectedObjectCount2", mark)) for mark in (-1, 0, 4)}
        require(marks == {-1: 2, 0: 1, 4: 1}, "active feature selections do not contain exactly the marked profile and axis")
        require(int(self.get(selection, "GetSelectedObjectType3", 1, 0)) == 9 and int(self.get(selection, "GetSelectedObjectType3", 1, 4)) in (10, 24), "selected profile or axis has an unexpected native selection type")
        actual = self.check_axis(self.get(selection, "GetSelectedObject6", 1, 4), case)
        require(actual["id"] == before["id"], "marked axis identity differs from the newly authored line")
        self.rec.data["feature_selections"] = {"marks": marks, "axis": actual}
        arguments = (True, True, False, False, case["reverse"], False, 0, 0, math.radians(case["angle_deg"]), 0.0, False, False, 0.0, 0.0, 0, 0.0, 0.0, True, True, True)
        boss = self.get(self.get(self.model, "FeatureManager"), "FeatureRevolve2", *arguments)
        require(boss is not None, "ordinary boss revolve creation failed")
        self.set(boss, "Name", BOSS)

    def snapshot(self, case, label, angle_degrees):
        require(self.get(self.model, "ForceRebuild3", False), "revolve rebuild failed")
        require(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0, "document contains rebuild errors or warnings")
        tree = self.rec.call("feature tree", Swapp.features, self.model)
        require(tree and all(feature.get("error") == 0 and feature.get("warning") is False for feature in tree), "feature tree has errors or warnings")
        require(sum(feature["type"] == "Revolution" for feature in tree) == 1, "native revolution identity was not unique")
        boss = self.get(self.model, "FeatureByName", BOSS)
        sketch_feature = self.get(self.model, "FeatureByName", PROFILE)
        require(boss is not None and sketch_feature is not None, "saved named feature or profile is missing")
        self.sketch = self.get(sketch_feature, "GetSpecificFeature2")
        require(self.sketch is not None, "saved profile has no sketch interface")
        parents = [str(self.get(parent, "Name")) for parent in (self.get(boss, "GetParents") or ())]
        require(PROFILE in parents, "native revolve does not depend on the saved profile")
        definition = self.typed(self.get(boss, "GetDefinition"), "RevolveFeatureData2")
        require(self.get(definition, "IsBossFeature") and not self.get(definition, "IsThinFeature"), "reopened feature is not an ordinary boss revolve")
        require(self.get(definition, "AccessSelections", self.model, Swapp.nothing()), "revolve definition selections unavailable")
        try:
            mode = int(self.get(definition, "Type"))
            require(mode in ((0, 3) if angle_degrees == 360 else (0,)), "unexpected one-direction revolve API mode")
            reverse = bool(self.get(definition, "ReverseDirection"))
            require(reverse == case["reverse"], "native direction differs from authored request")
            angle = float(self.get(definition, "GetRevolutionAngle", True))
            self.rec.close_number("forward angle in radians", angle, math.radians(angle_degrees))
            require(int(self.get(definition, "GetAxisType")) == 10, "definition axis is not a sketch segment")
            axis = self.check_axis(self.get(definition, "Axis"), case)
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        actual_bodies = self.rec.call("solid body count", Swapp.bodies, self.model)
        require(actual_bodies == 1, "native revolve did not produce one solid body")
        mass = self.rec.call("mass properties", Swapp.mass, self.model)
        require(mass is not None and "error" not in mass, "native mass properties unavailable")
        volume, area, first = geometry(case, angle_degrees, 1)
        centers = [self.world(first)]
        if angle_degrees < 360:
            centers.append(self.world(geometry(case, angle_degrees, -1)[2]))
        com = mass["com"]
        closest = min(range(len(centers)), key=lambda index: math.dist(com, centers[index]))
        self.rec.close_number("volume m3", mass["volume"], volume)
        self.rec.close_number("area m2", mass["area"], area)
        for coord, actual, expected in zip("xyz", com, centers[closest], strict=True):
            self.rec.close_number("center of mass " + coord, actual, expected, absolute=1e-10)
        handedness = None if angle_degrees == 360 else (1 if closest == 0 else -1) * (-1 if reverse else 1)
        self.rec.data[label] = {"axis": axis, "angle_radians": angle, "reverse": reverse, "api_mode": mode, "parents": parents, "features": tree, "bodies": actual_bodies, "mass": mass, "expected": {"volume": volume, "area": area, "com": centers[closest]}, "forward_handedness": handedness}
        self.rec.flush()
        return boss

    def edit_angle(self, case, boss):
        request = math.radians(case["angle_deg"])
        display = self.get(boss, "GetFirstDisplayDimension")
        candidates = []
        observations = []
        while display is not None:
            require(len(observations) < 16, "revolve display dimension list exceeded its bound")
            kind = int(self.get(display, "Type2"))
            dimension = self.get(display, "GetDimension2", 0)
            require(dimension is not None, "revolve display dimension has no parameter")
            name = str(self.get(dimension, "FullName"))
            value = float(self.get(dimension, "SystemValue"))
            editable = not bool(self.get(dimension, "ReadOnly")) and int(self.get(dimension, "DrivenState")) == 2
            observations.append({"name": name, "type": kind, "value": value, "editable": editable})
            if kind == 3 and editable and math.isclose(value, request, rel_tol=2e-7, abs_tol=1e-12):
                candidates.append((name, dimension))
            display = self.get(boss, "GetNextDisplayDimension", display)
        self.rec.data["display_dimensions"] = observations
        self.rec.flush()
        if case["angle_deg"] == 360 and not candidates:
            self.rec.data["edit"] = {"passed": False, "reason": "no editable full-turn angular display"}
            return
        require(len(candidates) == 1, "one editable angular driving dimension was expected")
        name, dimension = candidates[0]
        target = math.radians(case["edit_angle_deg"])
        status = int(self.get(dimension, "SetSystemValue3", target, 1, Swapp.nothing()))
        require(status == 0, f"angular dimension setter rejected edit with status {status}")
        self.rec.close_number("edited angular display in radians", self.get(dimension, "SystemValue"), target)
        self.snapshot(case, "edited", case["edit_angle_deg"])
        self.rec.data["edit"] = {"passed": True, "name": name, "before_radians": request, "after_radians": target, "setter_status": status}


def run_phase(case, phase, path, oracle_hash, source_hash=None):
    record_path = path.with_suffix(f".{phase}.json")
    recorder = Recorder(record_path, {"case": case, "phase": phase})
    recorder.data["schema"] = "kit.sw2026.ordinary-revolve-source-phase.v1"
    session = None
    author = None
    work_completed = False
    with Swapp.Dismisser() as monitor:
        try:
            session = recorder.call("launch .34 COM", Swapp.Sw)
            identity = recorder.call("oracle identity", application_identity, session.app)
            recorder.data["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == oracle_hash and identity["pe_machine"] == "0x8664" and session.revision == "34.5.2", "wrong SOLIDWORKS oracle")
            author = RevolveAuthor(session.app, recorder, Swapp)
            if phase == "author":
                require(not path.exists(), "native source output already exists")
                author.build(case, session)
                author.snapshot(case, "authored", case["angle_deg"])
                saved = recorder.call("save standalone source", session.save_as, author.model, path)
                require(saved == (True, 0, 0) and path.is_file() and path.stat().st_size > 0, f"native save failed or warned: {saved}")
                recorder.data.update(native_sha256=digest(path), native_bytes=path.stat().st_size)
            else:
                require(digest(path) == source_hash, "source changed before reopening")
                author.model, errors, warnings = recorder.call("fresh open standalone source", session.open, path)
                require(author.model is not None and errors == warnings == 0, "native source failed to open cleanly")
                boss = author.snapshot(case, "reopened", case["angle_deg"])
                author.edit_angle(case, boss)
            work_completed = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    session.close_doc(author.model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                author.model = None
            if session is not None:
                try:
                    session.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                recorder.data["controller_diagnostics"] = session.diagnostics
    recorder.data["dialogs"] = monitor.log
    expected_hash = source_hash or recorder.data.get("native_sha256")
    recorder.data["source_immutable"] = bool(expected_hash and path.is_file() and digest(path) == expected_hash)
    recorder.data["passed"] = bool(work_completed and recorder.data["source_immutable"] and not recorder.data["first_failure"] and not recorder.data["dialogs"] and not recorder.data.get("controller_diagnostics"))
    recorder.data["finished_at"] = time.time()
    recorder.flush()
    return recorder.data, digest(record_path)


def main():
    job_path = Path(sys.argv[1]).resolve()
    job = json.loads(job_path.read_bytes())
    require(job["schema"] == "kit.sw2026.ordinary-revolve-job.v1" and re.fullmatch(r"[0-9a-f]{40}", job["source_revision"]), "invalid revolve job schema or source revision")
    specs_path = Path(job["specs"])
    control = Path(job["control"])
    checkout = Path(job["checkout_root"]).resolve()
    output = Path(job["output"])
    private_paths = (job_path, specs_path, output)
    require(all(path.is_absolute() and not path.resolve().is_relative_to(checkout) for path in private_paths), "job, source specs, and output must be outside the checkout")
    require(digest(specs_path) == job["specs_sha256"] and digest(control) == job["control_sha256"], "immutable specification or control digest differs")
    cases = validate_cases(json.loads(specs_path.read_bytes()))
    tool_paths = [Path(__file__).with_name(name) for name in ("AuthorRevolveSources.py", "AuthorCurves.py", "InspectFresh.py", "Swapp.py", "OracleIdentity.py")]
    tool_hashes = {path.name: digest(path) for path in tool_paths}
    output.mkdir(parents=True, exist_ok=False)
    evidence = {"schema": "kit.sw2026.ordinary-revolve-source-lock.v1", "source_revision": job["source_revision"], "job_sha256": digest(job_path), "specs_sha256": job["specs_sha256"], "control_sha256": job["control_sha256"], "oracle_sha256": job["oracle_sha256"], "tool_sha256": tool_hashes, "started_at": time.time(), "cases": [], "passed": False, "writer_output_count": 0, "heldout_results_sealed": True, "native_acceptance": False, "heldout_acceptance": False}
    controls = []
    identities = []
    handedness = set()

    def control_phase(kind):
        record = {}
        try:
            require(digest(control) == job["control_sha256"], "control source hash changed before inspection")
            inspect(control, result=record)
        except Exception as error:
            record["exception"] = repr(error)
        controls.append(record)
        write_json(output / f"{kind}.json", record)
        return healthy(record) and record["sha256"] == job["control_sha256"] and record["oracle_identity"]["sha256"] == job["oracle_sha256"]

    try:
        before = control_phase("control-before")
        evidence["control_before_healthy"] = before
        if before:
            for case in cases:
                directory = output / case["split"] / case["name"]
                directory.mkdir(parents=True)
                path = directory / (case["name"] + ".SLDPRT")
                authored, authored_record = run_phase(case, "author", path, job["oracle_sha256"])
                phases = [(authored, authored_record)]
                native_hash = authored.get("native_sha256")
                if authored["passed"]:
                    phases.append(run_phase(case, "reopen", path, job["oracle_sha256"], native_hash))
                reopened = phases[-1][0]
                for phase, _ in phases:
                    for label in ("authored", "reopened", "edited"):
                        sign = phase.get(label, {}).get("forward_handedness")
                        if sign is not None:
                            handedness.add(sign)
                    if "oracle_identity" in phase:
                        identities.append(phase["oracle_identity"]["process_creation_filetime"])
                evidence["cases"].append({"name": case["name"], "split": case["split"], "native_sha256": native_hash, "native_bytes": authored.get("native_bytes"), "phase_record_sha256": [record for _, record in phases], "dimension_edit_passed": bool(reopened.get("edit", {}).get("passed")), "passed": len(phases) == 2 and all(phase["passed"] for phase, _ in phases)})
                write_json(output / "SourceLock.json", evidence)
    except Exception as error:
        write_json(output / "PrivateFailure.json", {"exception": repr(error)})
        evidence["batch_exception"] = True
    finally:
        evidence["control_after_healthy"] = control_phase("control-after")
        identities.extend(record["oracle_identity"]["process_creation_filetime"] for record in controls if "oracle_identity" in record)
        evidence.update(controls_unchanged=digest(control) == job["control_sha256"], control_record_sha256={path.name: digest(path) for path in sorted(output.glob("control-*.json"))}, distinct_processes=len(set(identities)), direction_consistent=len(handedness) == 1, tools_unchanged={path.name: digest(path) for path in tool_paths} == tool_hashes, inputs_unchanged=digest(job_path) == evidence["job_sha256"] and digest(specs_path) == job["specs_sha256"], finished_at=time.time())
        evidence["passed"] = bool(evidence.get("control_before_healthy") and evidence["control_after_healthy"] and evidence["controls_unchanged"] and evidence["direction_consistent"] and evidence["tools_unchanged"] and evidence["inputs_unchanged"] and len(identities) == evidence["distinct_processes"] == 12 and len(evidence["cases"]) == len(cases) and all(row["passed"] for row in evidence["cases"]) and not evidence.get("batch_exception"))
        write_json(output / "SourceLock.json", evidence)
    Swapp.emit({"passed": evidence["passed"], "sources": len(evidence["cases"]), "writer_output_count": 0})
    return int(not evidence["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
