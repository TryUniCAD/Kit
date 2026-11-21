import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).with_name("CaptureBodies.py")),
    init_globals={"ONLY": ["RemoveFirstDefaultBody"], "REPORT": "CaptureDefaultNames.json"},
    run_name="kit_feature_capture",
)
