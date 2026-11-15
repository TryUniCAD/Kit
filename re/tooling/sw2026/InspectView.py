from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import Swapp
from OracleIdentity import application_identity


def rotations(model):
    result = {"standard": {}}
    for index in range(1, 10):
        try:
            transform = model.GetStandardViewRotation(index)
            data = transform if isinstance(transform, (list, tuple)) else Swapp.cv(transform, "ArrayData")
            result["standard"][str(index)] = [float(value) for value in data]
        except Exception as error:
            result["standard"][str(index)] = {"exception": repr(error)}
    try:
        view = Swapp.cv(model, "ActiveView")
        transform = Swapp.cv(view, "Orientation3")
        result["active"] = list(Swapp.cv(transform, "ArrayData"))
    except Exception as error:
        result["active"] = {"exception": repr(error)}
    return result


def capture(path, bitmap, result, checkpoint):
    initial = bitmap.with_name(bitmap.stem + "_initial.bmp")
    if bitmap.exists() or initial.exists() or bitmap.suffix.casefold() != ".bmp":
        raise ValueError("native viewport capture requires a new explicit BMP path")
    result.update(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bitmap=str(bitmap), stages=[])

    def mark(stage):
        result["stage"] = stage
        result["stages"].append({"stage": stage, "time": time.time()})
        checkpoint()

    Swapp.sweep()
    with Swapp.Dismisser() as dismisser:
        controller = None
        model = None
        try:
            controller = Swapp.Sw(visible=True)
            result["oracle_identity"] = application_identity(controller.app)
            if not result["oracle_identity"]["version_matches"]:
                raise RuntimeError("viewport inspection requires the exact selected 2026 oracle")
            mark("open_start")
            model, errors, warnings = controller.open(path)
            result.update(opened=model is not None, open_errors=errors, open_warnings=warnings)
            mark("open_return")
            if model is None:
                raise RuntimeError("viewport input did not open")
            mark("rebuild_start")
            result["rebuilt"] = bool(model.ForceRebuild3(False))
            mark("rebuild_return")
            result.update(bodies=Swapp.bodies(model), mass=Swapp.mass(model), features=Swapp.features(model))
            if errors or warnings or not result["rebuilt"] or result["bodies"] < 1 or not result["features"] or any(feature.get("error") != 0 or feature.get("warning") is not False for feature in result["features"]):
                raise RuntimeError("viewport input does not have clean native geometry and feature status")
            time.sleep(1)
            mark("initial_capture_start")
            result["initial_bitmap_saved"] = bool(model.SaveBMP(str(initial), 960, 720))
            if not result["initial_bitmap_saved"] or not initial.is_file():
                raise RuntimeError("initial native viewport bitmap was not created")
            initial_data = initial.read_bytes()
            result.update(initial_bitmap=str(initial), initial_bitmap_sha256=hashlib.sha256(initial_data).hexdigest(), initial_bitmap_bytes=len(initial_data))
            result["rotations_before"] = rotations(model)
            mark("initial_capture_return")
            mark("orient_start")
            model.ShowNamedView2("", 7)
            Swapp.cv(model, "ViewZoomtofit2")
            Swapp.cv(model, "GraphicsRedraw2")
            mark("orient_return")
            time.sleep(1)
            mark("capture_start")
            result["bitmap_saved"] = bool(model.SaveBMP(str(bitmap), 960, 720))
            mark("capture_return")
            if not result["bitmap_saved"] or not bitmap.is_file():
                raise RuntimeError("native viewport bitmap was not created")
            data = bitmap.read_bytes()
            result.update(bitmap_sha256=hashlib.sha256(data).hexdigest(), bitmap_bytes=len(data), bitmap_signature=data[:2].hex())
            result["rotations_after"] = rotations(model)
        except Exception as error:
            result.update(exception=repr(error), failure_stage=result.get("stage", "oracle_setup"))
        finally:
            if controller is not None:
                if model is not None:
                    controller.close_doc(model)
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dismisser.log, progress_windows=dismisser.progress, sha256_after=hashlib.sha256(path.read_bytes()).hexdigest())
    result["unchanged_input"] = result["sha256"] == result["sha256_after"]
    checkpoint()


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    result = {"authority": "native-visible-document-viewport", "started_at": time.time(), "job_sha256": hashlib.sha256(job_path.read_bytes()).hexdigest(), "inspector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "results": [], "limitation": "bitmap creation alone is not visual acceptance; every image needs inspection"}

    def checkpoint():
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    for case in job["cases"]:
        row = {"kind": case["kind"], "name": case["name"]}
        result["results"].append(row)
        capture(Path(case["source"]), Path(case["bitmap"]), row, checkpoint)
    result["finished_at"] = time.time()
    checkpoint()
    return int(any(row.get("exception") or not row.get("bitmap_saved") or not row.get("unchanged_input") or row.get("controller_diagnostics") for row in result["results"]))


if __name__ == "__main__":
    raise SystemExit(main())
