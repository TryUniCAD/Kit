from pathlib import Path
import gzip,hashlib,io,json,tarfile

folder=Path(__file__).parent;archive=folder/'Documents.tar.gz'
if archive.exists():raise SystemExit('existing evidence archive must not be overwritten')
members=sorted(p for p in folder.rglob('*') if p.is_file() and ('Documents' in p.relative_to(folder).parts or p.suffix=='.f3d' or (p.parent==folder/'Discovery' and p.name!='Receipt.json')))
records=[]
with archive.open('wb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped:
  with tarfile.open(fileobj=zipped,mode='w') as target:
   for path in members:
    data=path.read_bytes();name=str(path.relative_to(folder));info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
    target.addfile(info,io.BytesIO(data));records.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
with tarfile.open(archive) as packed:
 for expected,member in zip(records,packed.getmembers(),strict=True):
  data=packed.extractfile(member).read();assert expected['path']==member.name and expected['bytes']==len(data) and expected['sha256']==hashlib.sha256(data).hexdigest()
  assert b'/Users/' not in data and b'/home/' not in data
report=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=records,privacy='no private home paths in any member; native candidate bytes unchanged',source_files_removed_only_after_exact_verification=True)
(folder/'DocumentArchive.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
for path in members:path.unlink()
print(json.dumps(dict(members=len(records),bytes=archive.stat().st_size,sha256=report['sha256'])))
