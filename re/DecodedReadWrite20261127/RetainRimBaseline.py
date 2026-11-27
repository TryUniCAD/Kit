import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

runtime=Path(sys.argv[1]).resolve();sdk=Path(sys.argv[2]).resolve();output=Path(sys.argv[3]).resolve();output.mkdir(exist_ok=False)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=sdk,text=True).strip()
if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=sdk,text=True):raise ValueError('pinned SDK has tracked changes')
manifest=json.loads((runtime/'Corpus.json').read_text())
if revision!=manifest['source_revision']:raise ValueError('SDK/corpus revision mismatch')
for row in manifest['assets']:
 raw=subprocess.check_output(['git','show',revision+':'+row['path']],cwd=sdk);blob=subprocess.check_output(['git','rev-parse',revision+':'+row['path']],cwd=sdk,text=True).strip()
 if hashlib.sha256(raw).hexdigest()!=row['sha256'] or len(raw)!=row['size_bytes'] or blob!=row['git_blob']:raise ValueError('committed source binding mismatch')
report=dict(sdk_revision=revision,source_revision=revision,sdk_tracked_clean=True,models=False,native_calls=0,jobs=[],members=[],unresolved={})
archive=output/'Readers.tar.gz'
with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as packed,tarfile.open(mode='w',fileobj=packed) as tar:
 for mode in ['strict','partial']:
  job=runtime/('fusion-rim-'+mode);worker=json.loads((job/'Receipt.json').read_text());summary=json.loads((job/'Decode0/summary.json').read_text());expected=dict(assets=22,decoded=22 if mode=='partial' else 0,partial=22 if mode=='partial' else 0,reader_error=0,rejected=22 if mode=='strict' else 0,strict=0);exit_code=3 if mode=='strict' else 0
  if worker['runs'][0]['exit_code']!=exit_code or summary['counts']!=expected or summary['sdk_revision']!=revision or worker['identity']['tool_version']!=revision:raise ValueError('unexpected baseline outcomes')
  if summary['portable_complete'] is not False or summary['semantic_qualification']!='unverified' or summary['native_acceptance']!='not_established':raise ValueError('baseline falsely claims qualification')
  for path in (job/'Decode0').rglob('receipt.json'):
   receipt=json.loads(path.read_text());doc=json.loads(path.with_name('document.json').read_text())
   if doc['metadata'].get('kit.research_read_status')!='unqualified' or not receipt['unresolved']:raise ValueError('lost partial qualification gaps')
   for finding in receipt['unresolved']:
    reason=finding['reason'];report['unresolved'][reason]=report['unresolved'].get(reason,0)+1
  paths=sorted([*list((job/'Decode0').rglob('*.json')),job/'Reader0.log'])
  for path in paths:
   data=path.read_bytes();name=mode+'/'+path.relative_to(job).as_posix();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data));report['members'].append(dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
  report['jobs'].append(dict(mode=mode,exit_code=exit_code,counts=summary['counts'],worker_receipt_sha256=hashlib.sha256((job/'Receipt.json').read_bytes()).hexdigest()))
with tarfile.open(archive) as tar:
 for row in report['members']:
  stream=tar.extractfile(row['path'])
  if stream is None or hashlib.sha256(stream.read()).hexdigest()!=row['sha256']:raise ValueError('retained artifact mismatch')
report.update(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),portable_complete=False,semantic_qualification='unverified',native_acceptance='not_established')
(output/'Replay.json').write_text(json.dumps(report,indent=2)+'\n');(output/'Corpus.json').write_bytes((runtime/'Corpus.json').read_bytes());(output/'Supervisor.log').write_bytes((runtime/'Supervisor.log').read_bytes());(output/'.gitignore').write_text('!Readers.tar.gz\n!Supervisor.log\n')
print(json.dumps(dict(revision=revision,jobs=len(report['jobs']),artifacts=len(report['members']),strict=0,partial=22)))
