from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw2026"))

import Author
import Swapp
from InspectFresh import healthy


def sketch_record(model, name):
    feature = Swapp.cv(model, "FeatureByName", name)
    sketch = Swapp.cv(feature, "GetSpecificFeature2")
    points = Swapp.cv(sketch, "GetSketchPoints2") or ()
    segments = Swapp.cv(sketch, "GetSketchSegments") or ()
    manager = Swapp.cv(sketch, "RelationManager")
    relations = Swapp.cv(manager, "GetRelations", 0) or ()
    return {
        "name": name,
        "point_count": len(points),
        "segment_count": len(segments),
        "relation_filter": 0,
        "relation_count": int(Swapp.cv(manager, "GetRelationsCount", 0)),
        "relation_types": [int(Swapp.cv(value, "GetRelationType")) for value in relations if value is not None],
        "points_m": [[float(Swapp.cv(point, axis)) for axis in ("X", "Y", "Z")] for point in points],
    }


def author_case(controller, trace, spec, output):
    trace.markphase(spec["name"] + ":new-document")
    controller.app.SetUserPreferenceToggle(Author.INPUT_DIM_ON_CREATE, False)
    builder = Author.Builder(controller, spec)
    builder.m = controller.new_part()
    record = {"spec": spec, "sketches": [], "authority": "instrumented-native-authoring"}
    try:
        for index, operation in enumerate(spec["ops"]):
            trace.markphase(spec["name"] + f":author-{index}-" + operation["op"])
            getattr(builder, "op_" + operation["op"])(operation)
            if operation["op"] == "sketch":
                record["sketches"].append(sketch_record(builder.m, operation["name"]))
        trace.markphase(spec["name"] + ":first-explicit-rebuild")
        record["rebuilt"] = bool(builder.m.ForceRebuild3(False))
        record.update(bodies=Swapp.bodies(builder.m), mass=Swapp.mass(builder.m), features=Swapp.features(builder.m), whats_wrong=Swapp.rebuild_errors(builder.m))
        trace.markphase(spec["name"] + ":save")
        target = output / (spec["name"] + ".SLDPRT")
        record["save"] = controller.save_as(builder.m, target)
        if target.is_file():
            record.update(path=str(target), sha256=hashlib.sha256(target.read_bytes()).hexdigest(), bytes=target.stat().st_size)
        record["sketches_after_save"] = [sketch_record(builder.m, value["name"]) for value in spec["ops"] if value["op"] == "sketch"]
        return record
    finally:
        trace.markphase(spec["name"] + ":close")
        controller.close_doc(builder.m)


def exercise(path, prepared):
    if path is None or prepared is None or "trace" not in prepared:
        raise ValueError("an explicit authoring job and retained traced controller are required")
    job = json.loads(path.read_text(encoding="utf-8"))
    source = Path(job["specifications"])
    cases = json.loads(source.read_text(encoding="utf-8"))
    if not 1 <= len(cases) <= 3:
        raise ValueError("one to three explicitly authored training cases are required")
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=True)
    controller, trace = prepared["controller"], prepared["trace"]
    record = {
        "authority": "native-authoring-lifecycle-observation",
        "instruction_taint": False,
        "controls_share_instrumented_process": True,
        "specifications_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "author_helper_sha256": hashlib.sha256(Path(Author.__file__).read_bytes()).hexdigest(),
        "oracle_helper_sha256": hashlib.sha256(Path(Swapp.__file__).read_bytes()).hexdigest(),
        "revision": controller.revision,
        "cases": [],
    }
    report = output / "Authoring.json"
    try:
        trace.markphase("control-before")
        record["control_before"] = Swapp.measure(controller, job["control"])
        if not healthy(record["control_before"]):
            raise RuntimeError("instrumented authoring control failed before observation")
        for spec in cases:
            record["cases"].append(author_case(controller, trace, spec, output))
            report.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        trace.markphase("control-after")
        record["control_after"] = Swapp.measure(controller, job["control"])
        record["controls_healthy"] = healthy(record["control_after"])
        if not record["controls_healthy"]:
            raise RuntimeError("instrumented authoring control failed after observation")
        trace.markphase("action-complete")
        return record
    finally:
        report.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
