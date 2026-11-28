import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import urllib.parse
import zlib

run=Path(sys.argv[1])
session=Path(sys.argv[2])
config=json.loads((run/'Paths.json').read_text())
sys.path[:0]=[str(Path(config['root'])/'re/automation'),config['client']]
from InferenceSession import read_session
import client
client.BASE=Path(config['client'])
packet,identity=read_session(session)
job=packet['job']
output=run/job['id']
output.mkdir()
record=dict(job=job['id'],controller_identity=identity,models=False,started=time.time())
outcome='completed'
try:
    if job['kind']=='offline.fusion':
        args=[config['cli'],'research','--offline','--root',config['root'],'fusion','--manifest',str(run/'Corpus.json'),'--output',str(output/'Decode')]
        if job['options']['partial']:
            args.append('--allow-partial')
        for asset in job['options']['assets']:
            args.extend(['--asset',asset])
        with (output/'Reader.log').open('w') as log:
            record['exit_code']=subprocess.run(args,stdout=log,stderr=log,timeout=1200).returncode
        record['argv']=args
        record['summary']=json.loads((output/'Decode/summary.json').read_text())
    else:
        case=job['options']['case']
        source=Path(config['capture'])/(case['id']+'.f3d')
        raw=source.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=case['archives'][0]['sha256']:
            raise ValueError('source hash differs')
        template=Path(config['verify']).read_text()
        if hashlib.sha256(template.encode()).hexdigest()!=job['options']['verify_sha256']:
            raise ValueError('verification worker bytes changed')
        controls={name:base64.b64encode(zlib.compress((Path(config['capture'])/(name+'.f3d')).read_bytes(),9)).decode() for name in ('control_before',)}
        script=template.replace('SOURCE_HASH=None','SOURCE_HASH = '+repr(digest)).replace('SPEC=None','SPEC = '+repr(case['spec'])).replace('CONTROLS=None','CONTROLS = '+repr(controls))
        if len(script.encode())>256*1024:
            raise ValueError('rendered script exceeds the existing API limit')
        record['script_sha256']=hashlib.sha256(script.encode()).hexdigest()
        (output/'RequestScript.py').write_text(script)
        submitted=client.request('/v1/jobs',dict(application='fusion',operation='script',script=script,source=base64.b64encode(raw).decode(),source_sha256=digest))
        (output/'Submitted.json').write_text(json.dumps(submitted))
        identifier=submitted['job']
        record['remote_job']=identifier
        until=time.monotonic()+1200
        while True:
            state=client.request('/v1/jobs/'+identifier)
            (output/'RemoteJob.json').write_text(json.dumps(state))
            if state['status']=='failed':
                raise RuntimeError(state.get('error'))
            if state['status']=='completed':
                break
            if time.monotonic()>until:
                raise TimeoutError('existing native request timed out; do not resubmit')
            time.sleep(2)
        native=output/'Native'
        native.mkdir()
        for artifact in state['artifacts']:
            name=artifact['name']
            if name!=Path(name).name or '\\' in name or name.startswith('.') or artifact['size']>32*1024*1024:
                raise ValueError('invalid artifact envelope')
            raw=client.request('/v1/jobs/'+identifier+'/files/'+urllib.parse.quote(name),binary=True)
            if len(raw)!=artifact['size'] or hashlib.sha256(raw).hexdigest()!=artifact['sha256']:
                raise ValueError('artifact hash differs')
            (native/name).write_bytes(raw)
        record['verification']=json.loads((native/'Verification.json').read_text())
        if record['verification']['errors']:
            outcome='waiting_evidence'
except Exception:
    record['error']=traceback.format_exc()
    outcome='waiting_evidence'
record['ended']=time.time()
(output/'Receipt.json').write_text(json.dumps(record,indent=2))
(session/'result.json').write_text(json.dumps(dict(outcome=outcome,reason='recorded native observations and deterministic outcomes; conversion unqualified',records=record)))
print(json.dumps(dict(job=job['id'],outcome=outcome)))
