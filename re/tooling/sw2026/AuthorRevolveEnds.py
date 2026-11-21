from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path
from shutil import copytree

import Swapp
from AuthorCurves import digest, require, write_json
from AuthorRevolveSources import PLANES, RevolveAuthor, run_phase
from InspectFresh import healthy, inspect


MODES = {"single": "swRevolveTypeOneDirection", "midplane": "swRevolveTypeMidPlane", "two": "swRevolveTypeTwoDirection"}


def read_constants():
    lib = Swapp.pythoncom.LoadRegTypeLib("{4687F359-55D0-4CD3-B6CF-2EB42C11F989}", 34, 0, 0)
    require(lib.GetLibAttr()[3:5] == (34, 0), "wrong SwConst type library version")
    requested = {"swEndConditions_e", "swRevolveType_e"}
    values = {}
    for index in range(lib.GetTypeInfoCount()):
        name = lib.GetDocumentation(index)[0]
        if name in requested:
            info = lib.GetTypeInfo(index)
            members = [info.GetVarDesc(member) for member in range(info.GetTypeAttr().cVars)]
            values[name] = {info.GetNames(member.memid)[0]: member.value for member in members}
    require(set(values) == requested, "missing 2026 revolve API enum")
    return values


def geometry(case, first, second):
    inner, outer = case["radius_m"]
    low, high = case["axial_m"]
    lower, upper = (-first / 2, first / 2) if case["mode"] == "midplane" else (-second, first)
    sweep = upper - lower
    height = high - low
    delta = outer**2 - inner**2
    moment = 2 * (outer**3 - inner**3) / (3 * delta * sweep)
    volume = height * sweep * delta / 2
    area = height * sweep * (inner + outer) + sweep * delta + 2 * height * (outer - inner)
    x = case["axis_x_m"] + moment * (math.sin(upper) - math.sin(lower))
    z = moment * (math.cos(lower) - math.cos(upper))
    return volume, area, x, (low + high) / 2, z


class RevolveEndAuthor(RevolveAuthor):
    constants = {}

    def feature_arguments(self, case):
        end_codes = self.constants["swEndConditions_e"]
        blind = end_codes["swEndCondBlind"]
        primary = end_codes["swEndCondMidPlane"] if case["mode"] == "midplane" else blind
        return (case["mode"] == "single", True, False, False, case["reverse"], False, primary,
                blind, math.radians(case["angle_deg"]), math.radians(case["second_deg"]), False,
                False, 0.0, 0.0, 0, 0.0, 0.0, True, True, True)

    def snapshot(self, case, label, angle_degrees):
        boss, tree, parents, definition = self.rebuilt_feature(label)
        require(self.get(definition, "AccessSelections", self.model, Swapp.nothing()), "revolve definition selections unavailable")
        try:
            mode = int(self.get(definition, "Type"))
            reverse = bool(self.get(definition, "ReverseDirection"))
            angles = [float(self.get(definition, "GetRevolutionAngle", side)) for side in (True, False)]
            require(int(self.get(definition, "GetAxisType")) == 10, "native rotate axis is not the selected sketch segment")
            axis = self.check_axis(self.get(definition, "Axis"), case)
        finally:
            self.get(definition, "ReleaseSelectionAccess")
        bodies = self.rec.call("solid body count", Swapp.bodies, self.model)
        mass = self.rec.call("mass properties", Swapp.mass, self.model)
        observation = {"api_mode": mode, "reverse": reverse, "angles_radians": angles,
                       "axis": axis, "bodies": bodies, "mass": mass, "features": tree, "parents": parents}
        self.rec.data[label] = observation
        self.rec.flush()
        require(mode == self.constants["swRevolveType_e"][MODES[case["mode"]]], "native revolve type differs from authored intent")
        require(reverse == case["reverse"], "native revolve direction differs from authored intent")
        first, second = math.radians(angle_degrees), math.radians(case["second_deg"])
        self.rec.close_number("direction-one angle", angles[0], first)
        if case["mode"] == "two":
            self.rec.close_number("direction-two angle", angles[1], second)
        require(bodies == 1 and mass is not None and "error" not in mass, "native revolve needs one measurable body")
        volume, area, x, y, z = geometry(case, first, second)
        centers = [self.world([x, y, sign * z]) for sign in (1, -1)]
        chosen = min(range(2), key=lambda index: math.dist(centers[index], mass["com"]))
        hand = None if z == 0 else (1 if chosen == 0 else -1) * (-1 if reverse else 1)
        center = centers[chosen]
        self.rec.close_number("volume m3", mass["volume"], volume)
        self.rec.close_number("area m2", mass["area"], area)
        for coordinate, actual, expected in zip("xyz", mass["com"], center, strict=True):
            self.rec.close_number("center of mass " + coordinate, actual, expected, absolute=1e-12)
        observation.update(expected={"volume": volume, "area": area, "com": center}, forward_handedness=hand)
        self.rec.flush()
        return boss

    def edit_angle(self, case, boss):
        pending = [("D1", "angle_deg", "edit_angle_deg")]
        if case["mode"] == "two":
            pending.append(("D2", "second_deg", "edit_second_deg"))
        current = dict(case)
        edits = []
        for index, (name, key, edit_key) in enumerate(pending):
            display = self.get(boss, "GetFirstDisplayDimension")
            drivers = {}
            displays = []
            while display is not None:
                require(len(displays) < 16, "native display dimension list exceeded its bound")
                param = self.get(display, "GetDimension2", 0)
                require(param is not None, "native angular display has no parameter owner")
                qualified = str(self.get(param, "FullName"))
                kind = int(self.get(display, "Type2"))
                editable = not bool(self.get(param, "ReadOnly")) and int(self.get(param, "DrivenState")) == 2
                value = float(self.get(param, "SystemValue"))
                displays.append({"name": qualified, "type": kind, "value": value, "editable": editable})
                if editable and kind == 3:
                    short, *_ = qualified.split("@")
                    require(short not in drivers, "native angular driver names are repeated")
                    drivers[short] = (param, qualified, value)
                display = self.get(boss, "GetNextDisplayDimension", display)
            self.rec.data.setdefault("display_dimensions", []).append(displays)
            self.rec.flush()
            require(set(drivers) == {entry[0] for entry in pending}, "native angular driver ownership differs from authored mode")
            param, qualified, original = drivers[name]
            self.rec.close_number("original " + name, original, math.radians(current[key]))
            target = math.radians(case[edit_key])
            status = int(self.get(param, "SetSystemValue3", target, 1, Swapp.nothing()))
            require(status == 0, f"{name} setter returned {status}")
            self.rec.close_number("edited " + name, self.get(param, "SystemValue"), target)
            current[key] = case[edit_key]
            label = "edited" if index + 1 == len(pending) else "after-d1"
            boss = self.snapshot(current, label, current["angle_deg"])
            edits.append({"name": qualified, "before_radians": original, "after_radians": target, "setter_status": status})
        self.rec.data["edit"] = {"passed": True, "dimensions": edits}


def validate_cases(spec):
    cases = spec["cases"]
    split = spec["split"]
    require(split in {"discovery", "heldout"} and 0 < len(cases) <= 6, "invalid source batch")
    require(len({row["name"] for row in cases}) == len(cases), "duplicate source names")
    for case in cases:
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,39}", case["name"]) is not None, "unsafe source name")
        mode = case["mode"]
        require(case["plane"] in PLANES and mode in MODES and type(case["reverse"]) is bool, "invalid revolve intent")
        inner, outer = case["radius_m"]
        low, high = case["axial_m"]
        axis_low, axis_high = case["axis_axial_m"]
        first, second = case["angle_deg"], case["second_deg"]
        edited_first, edited_second = case["edit_angle_deg"], case["edit_second_deg"]
        values = (inner, outer, low, high, axis_low, axis_high, case["axis_x_m"], first, second, edited_first, edited_second)
        require(all(math.isfinite(v) for v in values) and 0 < inner < outer and axis_low < low < high < axis_high, "invalid rectangle or axis")
        require(0 < first < 360 and 0 < edited_first < 360 and first != edited_first, "invalid direction-one edit")
        if mode == "two":
            require(0 < second and 0 < edited_second and second != edited_second and first != second and max(first, edited_first) + max(second, edited_second) < 360, "invalid unequal blind ends")
        else:
            require(second == edited_second == 0, "a second driver is only supplied for Two Directions")
        require(mode != "midplane" or not case["reverse"], "Mid Plane has no authored reverse setting")
        require(split != "heldout" or mode != "single", "single-direction source is outside held-out end coverage")
    return cases


def source_case(case, output, oracle):
    directory = output / case["name"]
    directory.mkdir()
    path = directory / (case["name"] + ".SLDPRT")
    edited_path = directory / (case["name"] + "-edited.SLDPRT")
    written, written_receipt = run_phase(case, "author", path, oracle, author_type=RevolveEndAuthor)
    phases = [(written, written_receipt)]
    native_hash = written.get("native_sha256")
    if written["passed"]:
        reopened, reopened_receipt = run_phase(case, "reopen", path, oracle, native_hash, inspect_profile=True,
                                              inspect_before_rebuild=True, save_edited=edited_path, author_type=RevolveEndAuthor)
        phases.append((reopened, reopened_receipt))
        if reopened["passed"] and reopened.get("edit", {}).get("passed"):
            edited = dict(case, angle_deg=case["edit_angle_deg"], second_deg=case["edit_second_deg"])
            phases.append(run_phase(edited, "edited-reopen", edited_path, oracle,
                                    reopened["edited_derivative"]["sha256"], inspect_profile=True,
                                    inspect_before_rebuild=True, author_type=RevolveEndAuthor))
    row = {"name": case["name"], "mode": case["mode"], "native_sha256": native_hash, "native_bytes": written.get("native_bytes"),
           "phase_record_sha256": [sha for _, sha in phases], "passed": len(phases) == 3 and all(result["passed"] for result, _ in phases)}
    return row, [result for result, _ in phases]


def main():
    job_path = Path(sys.argv[1]).resolve()
    job = json.loads(job_path.read_bytes())
    require(job["schema"] == "kit.sw2026.revolve-end-authoring.v1" and re.fullmatch(r"[0-9a-f]{40}", job["source_revision"]), "invalid source authoring job")
    spec_path, control, output, publication = (Path(job[name]).resolve() for name in ("spec", "control", "output", "publication"))
    checkout = Path(job["checkout"]).resolve()
    require(all(not path.is_relative_to(checkout) for path in (job_path, spec_path, control, output, publication)), "native research paths must be outside the checkout")
    require(digest(spec_path) == job["spec_sha256"] and digest(control) == job["control_sha256"], "private spec or control digest differs")
    spec = json.loads(spec_path.read_bytes())
    cases = validate_cases(spec)
    output.mkdir(parents=True)
    RevolveEndAuthor.constants = read_constants()
    tools = {name: Path(__file__).with_name(name) for name in ("AuthorRevolveEnds.py", "AuthorRevolveSources.py", "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py")}
    tool_hashes = {name: digest(path) for name, path in tools.items()}
    oracle = job["oracle_sha256"]
    evidence = {"schema": "kit.sw2026.revolve-end-source-lock.v1", "split": spec["split"], "source_revision": job["source_revision"],
                "job_sha256": digest(job_path), "spec_sha256": digest(spec_path), "control_sha256": digest(control),
                "oracle_sha256": oracle, "registered_swconst": RevolveEndAuthor.constants, "tool_sha256": tool_hashes,
                "started_at": time.time(), "sources": [], "writer_output_count": 0, "heldout_writer_acceptance": False}
    processes = []
    signs = set()

    def measure_control(label):
        result = inspect(control)
        path = output / (label + ".json")
        write_json(path, result)
        if "oracle_identity" in result:
            processes.append(result["oracle_identity"]["process_creation_filetime"])
        evidence[label] = {"sha256": digest(path), "passed": healthy(result) and result["sha256"] == evidence["control_sha256"] and result["oracle_identity"]["sha256"] == oracle}

    try:
        measure_control("control-before")
        if evidence["control-before"]["passed"]:
            for case in cases:
                row, phases = source_case(case, output, oracle)
                evidence["sources"].append(row)
                for phase in phases:
                    if "oracle_identity" in phase:
                        processes.append(phase["oracle_identity"]["process_creation_filetime"])
                    signs.update(phase[label]["forward_handedness"] for label in ("authored", "reopened", "after-d1", "edited")
                                 if label in phase and phase[label].get("forward_handedness") is not None)
    except Exception as error:
        write_json(output / "PrivateFailure.json", {"exception": repr(error)})
        evidence["batch_exception"] = True
    finally:
        measure_control("control-after")

    evidence.update(finished_at=time.time(), distinct_processes=len(set(processes)), direction_consistent=len(signs) <= 1,
                    idle_after=not Swapp.process_ids(), inputs_unchanged=digest(control) == evidence["control_sha256"]
                    and digest(spec_path) == evidence["spec_sha256"] and digest(job_path) == evidence["job_sha256"],
                    tools_unchanged={name: digest(path) for name, path in tools.items()} == tool_hashes)
    evidence["passed"] = bool(evidence.get("control-before", {}).get("passed") and evidence["control-after"]["passed"]
                              and evidence["distinct_processes"] == 2 + 3 * len(cases) and evidence["direction_consistent"]
                              and evidence["idle_after"] and evidence["inputs_unchanged"] and evidence["tools_unchanged"]
                              and not evidence.get("batch_exception") and len(evidence["sources"]) == len(cases)
                              and all(row["passed"] for row in evidence["sources"]))
    write_json(output / "SourceLock.json", evidence)
    if spec["split"] == "discovery":
        copytree(output, publication)
    else:
        require(not publication.exists(), "held-out summary path already exists")
        write_json(publication, evidence)
    Swapp.emit({"passed": evidence["passed"], "sources": len(evidence["sources"]), "writer_output_count": 0})
    return int(not evidence["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
