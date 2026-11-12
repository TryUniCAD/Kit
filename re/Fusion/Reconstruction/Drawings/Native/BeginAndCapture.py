import importlib
import runpy
import sys
import time
from pathlib import Path

base = Path(__file__).resolve().parent
sys.path.insert(0, str(base))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk
import adsk.core

runpy.run_path(str(base / 'BeginUploads.py'), run_name='__kit_fusion_oracle__')
uploads = common.state().get('uploads', {})
deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    states = [entry['future'].uploadState for entry in uploads.values()]
    if all(state != adsk.core.UploadStates.UploadProcessing for state in states):
        break
    adsk.doEvents()
common.save_json(common.SCRATCH / 'Variants' / 'UploadStates.json', {label: int(entry['future'].uploadState) for label, entry in uploads.items()})
runpy.run_path(str(base / 'CaptureSchema.py'), run_name='__kit_fusion_oracle__')
