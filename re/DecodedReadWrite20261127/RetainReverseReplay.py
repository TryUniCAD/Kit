import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

runtime = Path(sys.argv[1]).resolve()
pinned = Path(sys.argv[2]).resolve()
output = Path(sys.argv[3]).resolve()
output.mkdir(exist_ok=False)
job = runtime / 'solidworks-reader08df-host'
record = json.loads((job / 'Receipt.json').read_text())
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=pinned, text=True).strip()
assert revision == record['identity']['tool_version']
assert all(row['exit_code'] == 0 for row in record['runs']) and len(record['runs']) == 6
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=pinned,text=True)
manifest = json.loads((runtime / 'SolidworksCorpus.json').read_text())
assert manifest['source_revision'] == revision
for row in manifest['assets']:
    data = subprocess.check_output(['git', 'show', revision + ':' + row['path']], cwd=pinned)
    assert len(data) == row['size_bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    assert subprocess.check_output(['git','rev-parse',revision+':'+row['path']],cwd=pinned,text=True).strip() == row['git_blob']
paths = sorted([*job.glob('Decode*/document.json'), *job.glob('Decode*/receipt.json'), *job.glob('Reader*.log')])
assert len(paths) == 18
members = []
archive_path = output / 'Readers.tar.gz'
with archive_path.open('xb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed, tarfile.open(mode='w',fileobj=compressed) as archive:
    for path in paths:
        data = path.read_bytes()
        name = path.relative_to(job).as_posix()
        member = tarfile.TarInfo(name); member.size = len(data); member.mode = 0o644
        archive.addfile(member, io.BytesIO(data))
        members.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
with tarfile.open(archive_path) as archive:
    for row in members:
        stream = archive.extractfile(row['path']); assert stream is not None
        assert hashlib.sha256(stream.read()).hexdigest() == row['sha256']
outcomes = []
for row in record['runs']:
    receipt = json.loads((job / row['output'] / 'receipt.json').read_text())
    assert receipt['corpus_revision'] == revision
    assert receipt['validation'] == 'model_and_reconstruction_passed'
    outcomes.append(dict(asset=row['assets'][0], exit_code=row['exit_code'], counts=receipt['counts'], validation=receipt['validation'], unresolved_reasons=sorted({item['reason'] for item in receipt['unresolved']})))
failed_result = runtime/'Store/objects/fd/fdb084cb00915bbf1301b4375bac186f767ddac2860bf3f27a74b74f4eff3bac'
assert hashlib.sha256(failed_result.read_bytes()).hexdigest() == failed_result.name
summary = dict(sdk_revision=revision, corpus_revision=revision, sdk_clean=True, models=False, native_calls=0,
    accepted=6, refused=0, qualified_conversion=False, outcomes=outcomes,
    supervisor_summary=json.loads((runtime/'SupervisorHost.log').read_text().splitlines()[-1])['summary'],
    worker_receipt_sha256=hashlib.sha256((job/'Receipt.json').read_bytes()).hexdigest(),
    failed_attempt=dict(job='solidworks-reader08df', state='failed', reason='session setup failed: OSError: process identity unavailable before runner release', result_sha256=failed_result.name, worker_started=False, resolution='separate job after approved host execution; original failed controller job retained'),
    archive=dict(path='Readers.tar.gz', sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(), members=members),
    remaining=['all six receipts retain forty unresolved items', 'retained native record bytes are not portable semantics', 'direction frame operation independent source acceptance remains unqualified', 'generated reversed native lifecycle and holdouts unavailable'])
(output/'Replay.json').write_text(json.dumps(summary,indent=2)+'\n')
(output/'Corpus.json').write_text(json.dumps(manifest,indent=2)+'\n')
(output/'Supervisor.log').write_bytes((runtime/'SupervisorHost.log').read_bytes())
print(json.dumps(dict(sdk_revision=revision, accepted=6, artifacts=len(members), conversion_acceptance=False)))
