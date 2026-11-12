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

app = common.app
store = common.state()
variants = common.SCRATCH / 'Variants'
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting', 'uploads': {}}


def run():
    plan = json.loads((variants / 'Plan.json').read_text())
    wanted = json.loads((variants / 'Selection.json').read_text())['labels']
    project, created = common.ensure_project()
    report['project_created'] = created
    stamp = time.strftime('%Y%m%d%H%M%S')
    folder = project.rootFolder.dataFolders.add('KitDrw Uploads ' + stamp)
    if folder is None:
        raise RuntimeError('Upload folder creation failed')
    report['folder'] = folder.name
    uploads = store.setdefault('uploads', {})
    for row in plan['variants']:
        if row['label'] not in wanted:
            continue
        path = variants / row['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('Variant changed after planning: ' + row['label'])
        child = folder.dataFolders.add('KitDrw ' + row['label'])
        future = child.uploadFile(str(path))
        if future is None:
            raise RuntimeError('Upload did not start for ' + row['label'])
        uploads[row['label']] = {'future': future, 'folder': child, 'sha256': row['sha256'], 'started': time.time()}
        report['uploads'][row['label']] = {'sha256': row['sha256'], 'state': int(future.uploadState)}
    report['stage'] = 'uploads_started'


try:
    run()
    report['status'] = 'started'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    common.save_json(variants / 'BeginUploads.json', report)
