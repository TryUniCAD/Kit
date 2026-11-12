import ctypes
import hashlib
import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.core
import adsk.drawing

app = common.app
oracle = Path(__file__).resolve().parents[3] / 'LocalOracle'
bridge = Path('/tmp/kit-fusion-native-analysis/SchemaVersions.dylib')
out = common.SCRATCH / 'Schema'
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting'}
owned = []


def checkpoint(stage):
    report['stage'] = stage
    report['documents_now'] = app.documents.count
    common.save_json(out / 'Capture.json', report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def control_files():
    project, _ = common.ensure_project()
    folders = project.rootFolder.dataFolders
    chosen = [folders.item(index) for index in range(folders.count) if folders.item(index).name.startswith('Drawings ')]
    if not chosen:
        raise RuntimeError('Control drawing folder is unavailable')
    folder = sorted(chosen, key=lambda item: item.name)[-1]
    files = [folder.dataFiles.item(index) for index in range(folder.dataFiles.count)]
    sources = [item for item in files if item.fileExtension == 'f3d' and item.name.startswith(common.TOKEN)]
    drawings = [item for item in files if item.fileExtension == 'f2d' and item.name.startswith(common.TOKEN)]
    report['control_files'] = [{'name': item.name, 'extension': item.fileExtension, 'version': item.versionNumber} for item in files]
    if len(sources) != 1 or not drawings:
        raise RuntimeError('Control source or drawings are unavailable')
    return sources[0], drawings


def run():
    out.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((oracle / 'VersionsEvidence.json').read_text())
    report['bridge_sha256'] = hashlib.sha256(bridge.read_bytes()).hexdigest()
    if report['bridge_sha256'] != evidence['verification']['compiled_sha256'] or app.version != evidence['fusion_build']:
        raise RuntimeError('Schema bridge or Fusion build differs')
    source, drawings = control_files()
    checkpoint('opening_source')
    owned.append(app.documents.open(source, True))
    settle(5)
    report['opened'] = []
    for drawing_file in drawings:
        checkpoint('opening_drawing ' + drawing_file.name)
        document = app.documents.open(drawing_file, True)
        owned.append(document)
        settle(10)
        report['opened'].append(common.safe(lambda: common.drawing_info(document)))
    checkpoint('dumping_schema')
    target = out / 'Versions.json'
    library = ctypes.PyDLL(str(bridge))
    library.dump_schema_versions.argtypes = [ctypes.c_char_p]
    library.dump_schema_versions.restype = ctypes.c_int
    report['return_code'] = library.dump_schema_versions(str(target).encode())
    if report['return_code'] != 0:
        raise RuntimeError('Native schema export failed')
    report['schema_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()


try:
    run()
    report['status'] = 'captured'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint('finished')
