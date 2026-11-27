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
dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=sdk,text=True)
if dirty:raise ValueError('pinned SDK checkout has tracked changes')
job=runtime/'fusion-dual-strict';worker=json.loads((job/'Receipt.json').read_text())
manifest=json.loads((runtime/'Corpus.json').read_text());summary=json.loads((job/'Decode0/summary.json').read_text())
if revision!=manifest['source_revision'] or revision!=summary['sdk_revision'] or revision!=worker['identity']['tool_version']:raise ValueError('replay SDK and corpus revisions disagree')
for row in manifest['assets']:
    raw=subprocess.check_output(['git','show',revision+':'+row['path']],cwd=sdk)
    blob=subprocess.check_output(['git','rev-parse',revision+':'+row['path']],cwd=sdk,text=True).strip()
    if hashlib.sha256(raw).hexdigest()!=row['sha256'] or len(raw)!=row['size_bytes'] or blob!=row['git_blob']:raise ValueError('committed corpus asset binding disagrees')
expected=dict(assets=68,decoded=56,partial=0,reader_error=0,rejected=12,strict=56)
if summary['counts']!=expected or worker['runs'][0]['exit_code']!=3:raise ValueError('unexpected strict replay outcomes')
paths=sorted([*list((job/'Decode0').rglob('*.json')),job/'Reader0.log'])
archive=output/'Readers.tar.gz';members=[]
with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as packed,tarfile.open(mode='w',fileobj=packed) as tar:
    for path in paths:
        data=path.read_bytes();name=path.relative_to(job).as_posix();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data));members.append(dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
with tarfile.open(archive) as tar:
    for row in members:
        stream=tar.extractfile(row['path'])
        if stream is None or hashlib.sha256(stream.read()).hexdigest()!=row['sha256']:raise ValueError('retained reader artifact differs')
unresolved={}
for path in (job/'Decode0').rglob('receipt.json'):
    value=json.loads(path.read_text())
    for finding in value.get('unresolved',[]):
        reason=finding.get('reason','unclassified');unresolved[reason]=unresolved.get(reason,0)+1
report=dict(sdk_revision=revision,corpus_revision=revision,sdk_clean=True,models=False,native_calls=0,counts=summary['counts'],exit_code=3,portable_complete=summary['portable_complete'],semantic_qualification=summary['semantic_qualification'],native_acceptance=summary['native_acceptance'],unresolved=unresolved,worker_receipt_sha256=hashlib.sha256((job/'Receipt.json').read_bytes()).hexdigest(),archive=dict(path=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=members),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(output/'Replay.json').write_text(json.dumps(report,indent=2)+'\n');(output/'Corpus.json').write_bytes((runtime/'Corpus.json').read_bytes());(output/'Supervisor.log').write_bytes((runtime/'Supervisor.log').read_bytes())
print(json.dumps(dict(sdk_revision=revision,counts=expected,retained_artifacts=len(members),native_acceptance=False)))
