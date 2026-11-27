import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

root=Path(sys.argv[1]).resolve()
run=Path(sys.argv[2]).resolve()
session=Path(sys.argv[3]).resolve()
sys.path.insert(0,str(root/'re/automation'))
from InferenceSession import read_session
packet,identity=read_session(session)
job=packet['job']
output=run/job['id']
output.mkdir()
record=dict(job=job['id'],identity=identity,models=False,started=time.time())
outcome='completed'
try:
    options=job['options']
    manifest=Path(options['manifest'])
    assets=json.loads(manifest.read_text())['assets']
    argv=['/private/tmp/KitOffsetBin20261127/kit','research','--offline','--root',str(root),'fusion','--manifest',str(manifest),'--output',str(output/'Decode')]
    if options['partial']:argv.append('--allow-partial')
    for asset in assets:argv.extend(['--asset',asset['path']])
    with (output/'Reader.log').open('w') as log:
        record['exit_code']=subprocess.run(argv,stdout=log,stderr=log,timeout=1200).returncode
    record['manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
    record['summary']=json.loads((output/'Decode/summary.json').read_text())
except Exception:
    outcome='waiting_evidence'
    record['error']=traceback.format_exc()
record['ended']=time.time()
(output/'Receipt.json').write_text(json.dumps(record,indent=2))
(session/'result.json').write_text(json.dumps(dict(outcome=outcome,reason='recorded strict and explicit fallback outcomes without a CAD runtime or models',records=record)))
