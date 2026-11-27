import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile


root=Path(sys.argv[1]).resolve();archive_path=root/'Documents.tar.gz'
if archive_path.exists():raise ValueError('archive must be unused')
paths=[root/'Discovery.json',root/'Holdout.json',*sorted((root/'Proof/Documents').glob('*.json'))]
members=[]
with archive_path.open('wb') as target:
    with gzip.GzipFile(fileobj=target,mode='wb',filename='',mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|') as archive:
            for path in paths:
                info=archive.gettarinfo(str(path),arcname=str(path.relative_to(root)))
                info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
                with path.open('rb') as stream:archive.addfile(info,stream)
with tarfile.open(archive_path,'r:gz') as archive:
    for path in paths:
        data=path.read_bytes();name=str(path.relative_to(root))
        if archive.extractfile(name).read()!=data:raise ValueError('archive changed document bytes')
        if b'/Users/' in data or b'/home/' in data:raise ValueError('document contains a private home path')
        members.append(dict(member=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(root/'DocumentArchive.json').write_text(json.dumps(dict(archive='Documents.tar.gz',sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),exact_original_bytes_verified=True,members=members),indent=2,sort_keys=True))
for path in paths:path.unlink()
print(json.dumps(dict(members=len(members),bytes=archive_path.stat().st_size,sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest())))
