import argparse
import hashlib
import json
import math
from pathlib import Path

import ObserveRadialScene

PLAN = "02183274b1dac25beada7c523d8b2d08cf98074bb0a8ff57f58cbc9cbef1115c"
OBSERVER = "9ad6104107be9090d9187ff4687c101ac988e0f2ac8e7a926df144a729667084"


def checked(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"unexpected file identity: {path.name}")
    return data


def observe(author, original, job, depth_factor, plan, candidate):
    measured = original(author, job, depth_factor)
    state = plan["initial" if depth_factor == 1.0 else "edited_and_reopen"]
    extension = author.get(author.model, "ConfigurationManager")
    active = author.get(author.get(extension, "ActiveConfiguration"), "Name")
    if active != plan["active_configuration"]:
        raise ValueError("active radial configuration differs")
    bodies = tuple(author.get(author.model, "GetBodies2", 0, False) or ())
    if len(bodies) != state["body_count"]:
        raise ValueError("standalone radial solid count differs")
    body, = bodies
    body = author.typed(body, "Body2")
    faces = len(author.get(body, "GetFaces") or ())
    name = author.get(body, "Name")
    if faces != state["face_count"] or candidate and name != plan["geometry_owner"]:
        raise ValueError(f"standalone radial body differs: {faces} faces, name {name!r}")
    observed_tree = [[row["name"], row["type"], row["parent"]] for row in measured["tree"]]
    if candidate and observed_tree != plan["expected_tree"]:
        raise ValueError("standalone radial native tree differs")
    mass = measured["shape"]["extrusion"]["mass"]
    for value, target in zip(
        (mass["volume"], mass["area"], *mass["com"]),
        (state["volume_m3"], state["area_m2"], *state["centre_of_mass_m"]),
        strict=True,
    ):
        if not math.isclose(value, target, rel_tol=4e-7, abs_tol=1e-12):
            raise ValueError("standalone radial native mass properties differ")
    drivers = {}
    for owner, target in state["native_drivers_m"].items():
        dimension = author.get(author.model, "Parameter", owner)
        if dimension is None or author.get(dimension, "ReadOnly") or author.get(dimension, "DrivenState") != 2:
            raise ValueError(f"standalone radial native driver is not editable: {owner}")
        value = author.get(dimension, "SystemValue")
        if not math.isclose(value, target, rel_tol=4e-7, abs_tol=1e-12):
            raise ValueError(f"standalone radial native driver differs: {owner}")
        drivers[owner] = value
    measured["standalone"] = {"configuration": active, "body_name": name, "face_count": faces, "drivers_m": drivers}
    return measured


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trial", type=Path)
    parser.add_argument("trial_sha256")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan = json.loads(checked(args.plan, PLAN))
    checked(Path(ObserveRadialScene.__file__), OBSERVER)
    trial = args.trial.resolve(strict=True)
    job = json.loads(checked(trial, args.trial_sha256))
    candidate = job["files"]["candidate"]
    if (
        candidate["sha256"] != plan["standalone_candidate_sha256"]
        or candidate["guest_path"] != r"C:\KitAttachedRadiusChild01\Working\DisclosedRadialSceneProbe.SLDPRT"
        or job["edited_depth_m"] != plan["edited_and_reopen"]["depth_m"]
        or job["files"]["control"]["sha256"] != plan["matching_control_sha256"]
        or job["plan_sha256"] != PLAN
    ):
        raise ValueError("standalone native trial does not match the frozen intent")
    ObserveRadialScene.KNOWN = ObserveRadialScene.KNOWN | {"candidate": candidate["sha256"]}
    ObserveRadialScene.verify(trial, args.trial_sha256)
    original = ObserveRadialScene.capture

    def phase(role):
        def capture(author, current, factor):
            return observe(author, original, current, factor, plan, candidate=role in ("Generated", "Reopen"))

        ObserveRadialScene.capture = capture
        passed = ObserveRadialScene.phase(trial, args.trial_sha256, role)
        print(json.dumps({"phase": role, "passed": passed}), flush=True)
        return passed

    try:
        if phase("ControlBefore") and phase("Generated"):
            phase("Reopen")
    finally:
        phase("ControlAfter")
        ObserveRadialScene.capture = original
    return 0 if ObserveRadialScene.summary(trial, args.trial_sha256) else 1


if __name__ == "__main__":
    raise SystemExit(main())
