import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import sys

folder=Path(__file__).parent
members=sorted(p for p in folder.rglob('*') if p.is_file() and ('Documents' in p.relative_to(folder).parts or 'Candidates' in p.relative_to(folder).parts or p.name=='Discovery.json'))
archive=folder/(sys.argv[1] if len(sys.argv)>1 else 'Documents.tar.gz')
if archive.exists(): raise SystemExit('existing archive must be verified, never overwritten')
manifest=[]
with archive.open('wb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w') as target:
   for path in members:
    content=path.read_bytes();name=str(path.relative_to(folder));info=tarfile.TarInfo(name);info.size=len(content);info.mtime=0;info.mode=0o644
    target.addfile(info,io.BytesIO(content));manifest.append(dict(path=name,bytes=len(content),sha256=hashlib.sha256(content).hexdigest()))
with tarfile.open(archive) as packed:
 for expected,member in zip(manifest,packed.getmembers(),strict=True):
  content=packed.extractfile(member).read();assert member.name==expected['path'] and len(content)==expected['bytes'] and hashlib.sha256(content).hexdigest()==expected['sha256']
  assert b'/Users/' not in content and b'/home/' not in content
result=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,members=manifest,privacy='no private home paths in any packed member; no native file bytes changed',source_bytes_removed_only_after_exact_archive_verification=True)
(folder/('DocumentArchive.json' if archive.name=='Documents.tar.gz' else 'FinalDocumentArchive.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
for path in members: path.unlink()
print(json.dumps(dict(members=len(manifest),bytes=archive.stat().st_size,sha256=result['sha256'])))
