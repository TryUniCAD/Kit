from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path

import Swapp
from AuthorCurves import CurveAuthor, Recorder, digest, planar_properties, require, write_json
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


PLANES = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}
BOSS_SKETCH, BOSS = "CurveSketch", "CurveBoss"
CUT_SKETCH, CUT = "CutSketch", "OrdinaryBlindCut"
CUT_ARGUMENTS = (
    "Sd", "Flip", "Dir", "T1", "T2", "D1", "D2", "Dchk1", "Dchk2", "Ddir1", "Ddir2",
    "Dang1", "Dang2", "OffsetReverse1", "OffsetReverse2", "TranslateSurface1", "TranslateSurface2",
    "NormalCut", "UseFeatScope", "UseAutoSelect", "AssemblyFeatureScope", "AutoSelectComponents",
    "PropagateFeatureToParts", "T0", "StartOffset", "FlipStartOffset", "OptimizeGeometry",
)


def validate_cases(specs):
    require(specs["schema"] == "kit.sw2026.ordinary-blind-cut-specs.v1", "unexpected cut specification schema")
    cases = specs["cases"]
    require([case["split"] for case in cases] == ["discovery"] * 3 + ["heldout"] * 2, "expected three discovery and two held-out cases")
    require(len({case["name"].casefold() for case in cases}) == len(cases), "cut source names must be unique")
    for case in cases:
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,49}", case["name"]) is not None and case["plane"] in PLANES, "invalid cut source name or plane")
        rectangle, circle = case["boss_profile"], case["cut_profile"]
        require(rectangle.keys() == {"kind", "center_mm", "width_mm", "height_mm"} and rectangle["kind"] == "rectangle", "boss requires a simple rectangular sketch")
        require(circle.keys() == {"kind", "center_mm", "radius_mm"} and circle["kind"] == "circle", "cut requires a simple circular sketch")
        x, y = rectangle["center_mm"]
        u, v = circle["center_mm"]
        w, h, r = rectangle["width_mm"], rectangle["height_mm"], circle["radius_mm"]
        boss, cut, edit = (case[key] for key in ("boss_depth_mm", "cut_depth_mm", "edit_depth_mm"))
        require(all(math.isfinite(value) for value in (x, y, u, v, w, h, r, boss, cut, edit)), "nonfinite cut source input")
        require(0 < r and abs(u - x) + r < w / 2 and abs(v - y) + r < h / 2, "circular cut must lie strictly inside the rectangle")
        require((u, v) != (x, y), "an eccentric cut is required to observe centroid movement")
        require(0 < cut < boss and 0 < edit < boss and edit != cut, "both depths must describe distinct blind pockets in the boss")
    first, second, third, *heldouts = cases
    fixed = ("plane", "boss_profile", "cut_profile", "boss_depth_mm")
    require(all(first[key] == case[key] for key in fixed for case in (second, third)), "discovery sources must share one base geometry")
    require(first["cut_depth_mm"] < second["cut_depth_mm"] < third["cut_depth_mm"], "discovery cut depths must form an increasing ladder")
    for key in ("boss_profile", "cut_profile", "boss_depth_mm", "cut_depth_mm"):
        require(heldouts[0][key] != heldouts[1][key] and all(case[key] not in (first[key], second[key], third[key]) for case in heldouts), f"held-out {key} must be independently varied")
    return cases


def expected_geometry(case, cut_mm):
    rect_area, rect_perimeter, rect_xy = planar_properties({"profile": case["boss_profile"]})
    circle_area, circle_perimeter, circle_xy = planar_properties({"profile": case["cut_profile"]})
    boss = case["boss_depth_mm"] / 1000
    cut = cut_mm / 1000
    base_volume, removed_volume = rect_area * boss, circle_area * cut
    volume = base_volume - removed_volume
    area = 2 * rect_area + rect_perimeter * boss + circle_perimeter * cut
    center = [(base_volume * before - removed_volume * removed) / volume
              for before, removed in zip((*rect_xy, boss / 2), (*circle_xy, cut / 2), strict=True)]
    return {"bodies": 1, "volume": volume, "area": area, "com_sketch": center, "removed_volume": removed_volume}


class BlindCutAuthor(CurveAuthor):
    def create_sketch(self, plane, name, method, arguments, prior_name=None):
        extension = self.get(self.model, "Extension")
        self.get(self.model, "ClearSelection2", True)
        require(self.get(extension, "SelectByID2", PLANES[plane], "PLANE", 0.0, 0.0, 0.0, False, 0, Swapp.nothing(), 0), "named sketch plane selection failed")
        manager = self.get(self.model, "SketchManager")
        self.get(manager, "InsertSketch", True)
        require(self.get(manager, "ActiveSketch") is not None, "there is no active sketch")
        self.set(manager, "AddToDB", True)
        try:
            result = self.get(manager, method, *arguments)
            require(result is not None and (method != "CreateCornerRectangle" or len(result) == 4), "sketch primitive creation failed")
        finally:
            self.set(manager, "AddToDB", False)
        self.get(manager, "InsertSketch", True)
        if prior_name is None:
            feature = self.created_sketch_feature()
        else:
            feature = self.get(self.model, "FeatureByPositionReverse", 0)
            require(feature is not None and self.get(feature, "GetTypeName2") == "ProfileFeature" and self.get(feature, "Name") != prior_name, "latest feature is not the new cut profile")
        self.set(feature, "Name", name)
        self.get(self.model, "ClearSelection2", True)
        require(self.get(feature, "Select2", False, 0), "profile selection at mark 0 failed")
        selection = self.get(self.model, "SelectionManager")
        require(int(self.get(selection, "GetSelectedObjectCount2", -1)) == int(self.get(selection, "GetSelectedObjectCount2", 0)) == 1, "expected only the selected profile")
        return feature

    def require_cut_signature(self):
        library_id = "{83A33D31-27C5-11CE-BFD4-00400513BB57}"
        library = self.rec.call("load registered 2026 sldworks type library", Swapp.pythoncom.LoadRegTypeLib, library_id, 34, 0, 0)
        attributes = library.GetLibAttr()
        require(str(attributes[0]).casefold() == library_id.casefold() and attributes[3:5] == (34, 0), "wrong sldworks type library identity")
        typeinfo = next(
            (library.GetTypeInfo(index) for index in range(library.GetTypeInfoCount())
             if library.GetDocumentation(index)[0] == "IFeatureManager"),
            None,
        )
        require(typeinfo is not None, "IFeatureManager is absent from the registered sldworks type library")
        for index in range(typeinfo.GetTypeAttr().cFuncs):
            descriptor = typeinfo.GetFuncDesc(index)
            names = typeinfo.GetNames(descriptor.memid)
            if names and names[0] == "FeatureCut4":
                require(tuple(name.casefold() for name in names[1:]) == tuple(name.casefold() for name in CUT_ARGUMENTS), "installed FeatureCut4 argument order differs")
                self.rec.data["feature_cut_type_info"] = {"library_guid": str(attributes[0]), "library_version": list(attributes[3:5]), "interface": typeinfo.GetDocumentation(-1)[0], "names": names, "member_id": descriptor.memid, "invoke_kind": descriptor.invkind, "arguments": repr(descriptor.args), "return_type": repr(descriptor.rettype)}
                self.rec.flush()
                return
        raise RuntimeError("FeatureCut4 is absent from the registered IFeatureManager declaration")

    def build(self, case, session):
        self.model = self.rec.call("new part", session.new_part)
        rectangle = case["boss_profile"]
        cx, cy = (value / 1000 for value in rectangle["center_mm"])
        half_width, half_height = rectangle["width_mm"] / 2000, rectangle["height_mm"] / 2000
        self.create_sketch(case["plane"], BOSS_SKETCH, "CreateCornerRectangle", (cx - half_width, cy - half_height, 0.0, cx + half_width, cy + half_height, 0.0))
        feature_manager = self.get(self.model, "FeatureManager")
        boss_args = (True, False, False, 0, 0, case["boss_depth_mm"] / 1000, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
        boss = self.get(feature_manager, "FeatureExtrusion3", *boss_args)
        require(boss is not None, "native rectangular boss creation failed")
        self.set(boss, "Name", BOSS)
        self.snapshot(case, "uncut_boss", 0.0)
        circle = case["cut_profile"]
        u, v = (value / 1000 for value in circle["center_mm"])
        self.create_sketch(case["plane"], CUT_SKETCH, "CreateCircleByRadius", (u, v, 0.0, circle["radius_mm"] / 1000), prior_name=BOSS_SKETCH)
        self.require_cut_signature()
        cut_args = (True, False, True, 0, 0, case["cut_depth_mm"] / 1000, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False)
        cut = self.get(feature_manager, "FeatureCut4", *cut_args)
        require(cut is not None, "native blind circular cut creation failed")
        self.set(cut, "Name", CUT)

    def inspect_feature(self, name, sketch_name, requested, is_boss):
        feature = self.get(self.model, "FeatureByName", name)
        require(feature is not None, f"named feature is missing: {name}")
        kind = str(self.get(feature, "GetTypeName2"))
        if kind == "ICE":
            kind = str(self.get(feature, "GetTypeName"))
        require(kind in (("Extrusion", "BaseBody", "Boss") if is_boss else ("Cut",)), f"unexpected native feature type: {kind}")
        definition = self.typed(self.get(feature, "GetDefinition"), "ExtrudeFeatureData2")
        depth = float(self.get(definition, "GetDepth", True))
        self.rec.close_number(name + " forward depth", depth, requested / 1000)
        observed = {"type": kind, "depth_m": depth, "end": int(self.get(definition, "GetEndCondition", True)), "start": int(self.get(definition, "FromType")), "reverse": bool(self.get(definition, "ReverseDirection")), "two_directions": bool(self.get(definition, "BothDirections")), "draft": bool(self.get(definition, "GetDraftWhileExtruding", True)), "thin": bool(self.get(definition, "IsThinFeature"))}
        require(observed["end"] == observed["start"] == 0 and not any(observed[key] for key in ("two_directions", "draft", "thin")), f"feature left the single-direction native blind scope: {name}")
        if not is_boss:
            observed["outside"] = bool(self.get(definition, "FlipSideToCut"))
            observed["normal_cut"] = bool(self.get(definition, "NormalCut"))
            require(not observed["outside"] and not observed["normal_cut"], "feature is not an ordinary inside-profile cut")
        observed["parents"] = [str(self.get(parent, "Name")) for parent in self.get(feature, "GetParents") or ()]
        child = self.get(feature, "GetFirstSubFeature")
        nested = []
        while child is not None:
            require(len(nested) < 64, "feature children exceeded the traversal bound")
            nested.append(str(self.get(child, "Name")))
            child = self.get(child, "GetNextSubFeature")
        observed["children"] = nested
        require(sketch_name in observed["parents"] or sketch_name in nested, f"feature lost its authored profile: {name}")
        return observed

    def inspect_profile(self, name, expected):
        feature = self.get(self.model, "FeatureByName", name)
        require(feature is not None, f"saved profile is missing: {name}")
        self.sketch = self.get(feature, "GetSpecificFeature2")
        require(self.sketch is not None, f"saved profile has no sketch interface: {name}")
        observed = self.geometry()
        self.check_geometry({"profile": expected}, observed)
        transform = self.get(self.sketch, "ModelToSketchTransform")
        inverse = self.get(transform, "Inverse")
        return {"geometry": observed, "model_to_sketch": list(self.get(transform, "ArrayData"))[:13]}, inverse

    def snapshot(self, case, label, cut_depth):
        require(self.get(self.model, "ForceRebuild3", False), "native solid rebuild failed")
        require(int(self.get(self.get(self.model, "Extension"), "GetWhatsWrongCount")) == 0, "document contains rebuild errors or warnings")
        tree = self.feature_tree()
        snapshot = {"tree": tree, "boss": self.inspect_feature(BOSS, BOSS_SKETCH, case["boss_depth_mm"], True)}
        snapshot["boss_profile"], inverse = self.inspect_profile(BOSS_SKETCH, case["boss_profile"])
        if cut_depth:
            names = [row["name"] for row in tree if not row["suppressed"]]
            require(CUT_SKETCH in names and CUT in names and names.index(BOSS) < names.index(CUT), "cut is missing, suppressed or out of feature order")
            snapshot["cut"] = self.inspect_feature(CUT, CUT_SKETCH, cut_depth, False)
            snapshot["cut_profile"], _ = self.inspect_profile(CUT_SKETCH, case["cut_profile"])
            for index, values in enumerate(zip(snapshot["cut_profile"]["model_to_sketch"], snapshot["boss_profile"]["model_to_sketch"], strict=True)):
                self.rec.close_number(f"shared sketch frame element {index}", *values)
        solid_count = self.rec.call("solid body count", Swapp.bodies, self.model)
        mass = self.rec.call("mass properties", Swapp.mass, self.model)
        require(solid_count == 1 and mass is not None and "error" not in mass, "source lacks one measurable solid body")
        expected = expected_geometry(case, cut_depth)
        utility = self.get(self.app, "GetMathUtility")
        coordinates = Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY | Swapp.pythoncom.VT_R8, expected["com_sketch"])
        point = self.get(utility, "CreatePoint", coordinates)
        target = list(self.get(self.get(point, "MultiplyTransform", inverse), "ArrayData"))
        self.rec.close_number(label + " volume", mass["volume"], expected["volume"], absolute=1e-22)
        self.rec.close_number(label + " area", mass["area"], expected["area"], absolute=1e-18)
        for index, values in enumerate(zip(mass["com"], target, strict=True)):
            self.rec.close_number(f"{label} centre of mass coordinate {index}", *values, absolute=1e-10)
        snapshot.update(mass=mass, bodies=solid_count, expected={**expected, "com_model": target})
        self.rec.data[label] = snapshot
        self.rec.flush()
        return snapshot

    def edit_depth(self, case):
        dimension = self.get(self.model, "Parameter", f"D1@{CUT}")
        require(dimension is not None, "native cut driving dimension is missing")
        name = str(self.get(dimension, "FullName"))
        require(name.split("@")[1:2] == [CUT], "found dimension does not belong to the cut")
        require(not self.get(dimension, "ReadOnly") and int(self.get(dimension, "DrivenState")) == 2, "cut depth is not driving and editable")
        before, target = case["cut_depth_mm"] / 1000, case["edit_depth_mm"] / 1000
        self.rec.close_number("initial cut driving dimension", self.get(dimension, "SystemValue"), before)
        status = int(self.get(dimension, "SetSystemValue3", target, 1, Swapp.nothing()))
        require(status == 0, f"cut depth dimension setter failed with status {status}")
        self.rec.close_number("edited cut driving dimension", self.get(dimension, "SystemValue"), target)
        self.snapshot(case, "edited", case["edit_depth_mm"])
        self.rec.data["edit"] = {"name": name, "before_m": before, "after_m": target, "setter_status": status}


def run_phase(case, phase, path, oracle_hash, expected_hash=None):
    record_path = path.with_suffix(f".{phase}.json")
    recorder = Recorder(record_path, {"case": case, "phase": phase})
    recorder.data["schema"] = "kit.sw2026.ordinary-blind-cut-source-phase.v1"
    session = None
    complete = False
    with Swapp.Dismisser() as monitor:
        try:
            session = recorder.call("launch .34 COM", Swapp.Sw)
            identity = recorder.call("oracle identity", application_identity, session.app)
            recorder.data["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == oracle_hash and identity["pe_machine"] == "0x8664" and session.revision == "34.5.2", "incorrect SOLIDWORKS executable")
            author = BlindCutAuthor(session.app, recorder, Swapp)
            if phase == "author":
                require(not path.exists(), "case output exists before authoring")
                author.build(case, session)
                author.snapshot(case, "authored", case["cut_depth_mm"])
                save = recorder.call("save standalone native source", session.save_as, author.model, path)
                require(save == (True, 0, 0) and path.is_file() and path.stat().st_size > 0, f"native save failed or warned: {save}")
            else:
                require(digest(path) == expected_hash, "native source changed before fresh reopen")
                author.model, errors, warnings = recorder.call("open native source", session.open, path)
                require(author.model is not None and errors == warnings == 0, "native open failed or warned")
                author.snapshot(case, "reopened", case["cut_depth_mm"])
                author.edit_depth(case)
            complete = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                recorder.data["controller_diagnostics"] = session.diagnostics
    recorder.data["dialogs"] = monitor.log
    if phase == "author" and complete and path.is_file():
        expected_hash = digest(path)
        recorder.data.update(native_sha256=expected_hash, native_bytes=path.stat().st_size)
    recorder.data["source_immutable"] = bool(expected_hash and path.is_file() and digest(path) == expected_hash)
    recorder.data["passed"] = bool(complete and recorder.data["source_immutable"] and not recorder.data["first_failure"] and not recorder.data["dialogs"] and not recorder.data.get("controller_diagnostics"))
    recorder.data["finished_at"] = time.time()
    recorder.flush()
    return recorder.data, digest(record_path)


def main():
    job_path = Path(sys.argv[1]).resolve()
    job = json.loads(job_path.read_bytes())
    require(job["schema"] == "kit.sw2026.ordinary-blind-cut-job.v1" and re.fullmatch(r"[0-9a-f]{40}", job["source_revision"]), "invalid cut job schema or revision")
    checkout, specs_path, output, control = (Path(job[key]) for key in ("checkout_root", "specs", "output", "control"))
    require(all(path.is_absolute() for path in (checkout, specs_path, output, control)), "oracle and private paths must be absolute")
    require(all(not path.resolve().is_relative_to(checkout.resolve()) for path in (job_path, specs_path, output)), "seal job, specs and output outside the checkout")
    require(digest(specs_path) == job["specs_sha256"] and digest(control) == job["control_sha256"], "source specification or control digest differs")
    cases = validate_cases(json.loads(specs_path.read_bytes()))
    tools = [Path(__file__).with_name(name) for name in ("AuthorBlindCutSources.py", "AuthorCurves.py", "InspectFresh.py", "Swapp.py", "OracleIdentity.py")]
    tool_hashes = {path.name: digest(path) for path in tools}
    output.mkdir(parents=True, exist_ok=False)
    evidence = {"schema": "kit.sw2026.ordinary-blind-cut-source-lock.v1", "source_revision": job["source_revision"], "job_sha256": digest(job_path), "specs_sha256": job["specs_sha256"], "control_sha256": job["control_sha256"], "oracle_sha256": job["oracle_sha256"], "tool_sha256": tool_hashes, "started_at": time.time(), "cases": [], "passed": False, "writer_output_count": 0, "heldout_results_sealed": True, "native_acceptance": False, "heldout_acceptance": False}
    controls = []
    phase_identities = []

    def control_phase(kind):
        record = {}
        try:
            require(digest(control) == job["control_sha256"], "control file hash changed before inspection")
            inspect(control, result=record)
        except Exception as error:
            record["exception"] = repr(error)
        controls.append(record)
        write_json(output / f"{kind}.json", record)
        return healthy(record) and record["sha256"] == job["control_sha256"] and record["oracle_identity"]["sha256"] == job["oracle_sha256"]

    try:
        evidence["control_before_healthy"] = control_phase("control-before")
        if evidence["control_before_healthy"]:
            for case in cases:
                directory = output / case["split"] / case["name"]
                directory.mkdir(parents=True)
                path = directory / (case["name"] + ".SLDPRT")
                authored, author_receipt = run_phase(case, "author", path, job["oracle_sha256"])
                phases = [(authored, author_receipt)]
                native_hash = authored.get("native_sha256")
                if authored["passed"]:
                    phases.append(run_phase(case, "reopen", path, job["oracle_sha256"], native_hash))
                reopened = phases[-1][0]
                edit_passed = "edit" in reopened and reopened["passed"]
                directions_match = bool(edit_passed and all(authored["authored"][kind]["reverse"] == reopened["reopened"][kind]["reverse"] == reopened["edited"][kind]["reverse"] for kind in ("boss", "cut")))
                phase_identities.extend(row["oracle_identity"]["process_creation_filetime"] for row, _ in phases if "oracle_identity" in row)
                evidence["cases"].append({"name": case["name"], "split": case["split"], "native_sha256": native_hash, "native_bytes": authored.get("native_bytes"), "phase_record_sha256": [receipt for _, receipt in phases], "driving_depth_edit_passed": edit_passed, "passed": bool(authored["passed"] and edit_passed and directions_match)})
                write_json(output / "SourceLock.json", evidence)
    except Exception as error:
        write_json(output / "PrivateFailure.json", {"exception": repr(error)})
        evidence["batch_exception"] = True
    finally:
        evidence["control_after_healthy"] = control_phase("control-after")
        phase_identities.extend(record["oracle_identity"]["process_creation_filetime"] for record in controls if "oracle_identity" in record)
        evidence.update(controls_unchanged=digest(control) == job["control_sha256"], control_record_sha256={path.name: digest(path) for path in sorted(output.glob("control-*.json"))}, distinct_processes=len(set(phase_identities)), tools_unchanged={path.name: digest(path) for path in tools} == tool_hashes, inputs_unchanged=digest(job_path) == evidence["job_sha256"] and digest(specs_path) == job["specs_sha256"], finished_at=time.time())
        evidence["passed"] = bool(evidence.get("control_before_healthy") and evidence["control_after_healthy"] and evidence["controls_unchanged"] and evidence["inputs_unchanged"] and evidence["tools_unchanged"] and len(phase_identities) == evidence["distinct_processes"] == 12 and len(evidence["cases"]) == len(cases) and all(row["passed"] for row in evidence["cases"]) and not evidence.get("batch_exception"))
        write_json(output / "SourceLock.json", evidence)
    Swapp.emit({"passed": evidence["passed"], "sources": len(evidence["cases"]), "writer_output_count": 0})
    return int(not evidence["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
