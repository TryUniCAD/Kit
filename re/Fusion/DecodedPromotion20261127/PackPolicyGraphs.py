import gzip,hashlib,io,json,sys,tarfile
from pathlib import Path
root=Path(sys.argv[1]).resolve();folder=root/'re/Fusion/DecodedPromotion20261127/RimFilletPolicy';manifest=json.loads((folder/'Manifest.json').read_text());members=[];archive=folder/'Discovery/Graphs.tar.gz'
with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as packed,tarfile.open(mode='w',fileobj=packed) as tar:
 for row in manifest['files']:
  if not row['path'].startswith('Discovery/Graph') or not row['path'].endswith('.json'):continue
  path=folder/row['path'];data=path.read_bytes()
  if hashlib.sha256(data).hexdigest()!=row['sha256'] or len(data)!=row['bytes']:raise ValueError('sealed graph changed')
  info=tarfile.TarInfo(row['path']);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data));members.append(row)
if len(members)!=6:raise ValueError('expected exactly six source discovery graphs')
with tarfile.open(archive) as tar:
 for row in members:
  stream=tar.extractfile(row['path'])
  if stream is None or hashlib.sha256(stream.read()).hexdigest()!=row['sha256']:raise ValueError('packed source graph mismatch')
report=dict(original_manifest_sha256=hashlib.sha256((folder/'Manifest.json').read_bytes()).hexdigest(),original_seal_sha256=hashlib.sha256((folder/'Seal.json').read_bytes()).hexdigest(),archive=dict(path='Discovery/Graphs.tar.gz',sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=members),disposition='lossless archival; original sealed manifest and receipts unchanged; logical member paths resolve within archive')
(folder/'GraphArchive.json').write_text(json.dumps(report,indent=2)+'\n');(folder/'.gitignore').write_text('!Discovery/Graphs.tar.gz\n')
for row in members:(folder/row['path']).unlink()
print(json.dumps(dict(members=len(members),archive_bytes=archive.stat().st_size)))
