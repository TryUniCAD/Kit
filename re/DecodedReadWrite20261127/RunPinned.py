import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

root=Path(sys.argv[1]);run=Path(sys.argv[2]);session=Path(sys.argv[3])
sys.path.insert(0,str(root/'re/automation'))
from InferenceSession import read_session
packet,identity=read_session(session);job=packet['job'];options=job['options']
output=run/job['id'];output.mkdir()
record=dict(job=job['id'],identity=identity,models=False,started=time.time(),runs=[])
try:
 manifest=Path(options['manifest']);assets=json.loads(manifest.read_text())['assets']
 groups=[assets] if options['format']=='fusion' else [[asset] for asset in assets]
 for index,group in enumerate(groups):
  target=output/('Decode'+str(index));log=output/('Reader'+str(index)+'.log')
  argv=['/private/tmp/KitOffsetBin20261127/kit','research','--offline','--root',str(root),options['format'],'--manifest',str(manifest),'--output',str(target)]
  if options.get('partial'):argv.append('--allow-partial')
  for asset in group:argv.extend(['--asset',asset['path']])
  with log.open('w') as stream:code=subprocess.run(argv,stdout=stream,stderr=stream,timeout=1200).returncode
  record['runs'].append(dict(assets=[asset['path'] for asset in group],exit_code=code,output=target.name,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
 record['manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
except Exception:record['error']=traceback.format_exc()
record['ended']=time.time();(output/'Receipt.json').write_text(json.dumps(record,indent=2))
outcome='waiting_evidence' if 'error' in record else 'completed'
(session/'result.json').write_text(json.dumps(dict(outcome=outcome,reason='recorded pinned strict refusals and explicit fallback outcomes without native acceptance or models',records=record)))
print(json.dumps(dict(job=job['id'],outcome=outcome)))
