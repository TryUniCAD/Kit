import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile


root = Path(sys.argv[1]).resolve()
paths = sorted(root.glob('**/Geometry/*.json'))
archive_path = root / 'Documents.tar.gz'
if archive_path.exists() or not paths:
    raise ValueError('packing requires loose geometry files and an unused archive')
members = []
with archive_path.open('wb') as target:
    with gzip.GzipFile(fileobj=target,mode='wb',filename='',mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|') as archive:
            for path in paths:
                info = archive.gettarinfo(str(path),arcname=str(path.relative_to(root)))
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                with path.open('rb') as stream:
                    archive.addfile(info,stream)
with tarfile.open(archive_path,'r:gz') as archive:
    for path in paths:
        data = path.read_bytes()
        name = str(path.relative_to(root))
        if archive.extractfile(name).read() != data:
            raise ValueError('archived geometry changed bytes')
        members.append(dict(member=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
report = dict(archive='Documents.tar.gz',sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),verified_exact_original_bytes=True,members=members)
(root/'DocumentArchive.json').write_text(json.dumps(report,indent=2,sort_keys=True))
for path in paths:
    path.unlink()
print(json.dumps(dict(members=len(members),archive_sha256=report['sha256'],archive_bytes=archive_path.stat().st_size)))
