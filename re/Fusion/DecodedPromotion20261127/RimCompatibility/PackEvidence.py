from pathlib import Path
import gzip,hashlib,io,json,tarfile

folder=Path(__file__).parent;archive=folder/'Documents.tar.gz'
if archive.exists():raise SystemExit('existing evidence archive must not be overwritten')
members=sorted(p for p in folder.rglob('*') if p.is_file() and any(name in p.relative_to(folder).parts for name in ('Documents','Receipts','Logs')))
records=[]
with archive.open('wb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w') as target:
   for path in members:
    data=path.read_bytes();name=str(path.relative_to(folder));info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
    target.addfile(info,io.BytesIO(data));records.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
with tarfile.open(archive) as packed:
 actual=packed.getmembers()
 if len(actual)!=len(records):raise RuntimeError('archive member count differs')
 for expected,member in zip(records,actual,strict=True):
  data=packed.extractfile(member).read()
  if expected['path']!=member.name or expected['bytes']!=len(data) or expected['sha256']!=hashlib.sha256(data).hexdigest():raise RuntimeError('archive member bytes differ')
  if b'/Users/' in data or b'/home/' in data:raise RuntimeError('private home path in archive member')
report=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=records,privacy='no private home paths; exact original JSON bytes preserved',removed_loose_files_only_after_exact_archive_verification=True)
(folder/'DocumentArchive.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
for path in members:path.unlink()
print(json.dumps(dict(members=len(records),bytes=archive.stat().st_size,sha256=report['sha256'])))
