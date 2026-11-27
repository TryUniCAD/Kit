import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

source=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();output.mkdir(exist_ok=False)
receipt=json.loads((source/'Receipt.json').read_text());assert receipt['summary']==dict(decoded=56,rejected=12,eligible_rejected=0)
paths=sorted((source/'Documents').glob('*.json'));assert len(paths)==56
archive=output/'Documents.tar.gz';members=[]
with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed,tarfile.open(mode='w',fileobj=compressed) as tar:
    for path in paths:
        data=path.read_bytes();info=tarfile.TarInfo(path.name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data));members.append(dict(path=path.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
with tarfile.open(archive) as tar:
    for row in members:
        stream=tar.extractfile(row['path']);assert stream is not None
        assert hashlib.sha256(stream.read()).hexdigest()==row['sha256']
(output/'ReadReceipt.json').write_bytes((source/'Receipt.json').read_bytes())
(output/'DocumentArchive.json').write_text(json.dumps(dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=members,verified_exact_bytes=True),indent=2)+'\n')
print(json.dumps(dict(documents=56,archive_bytes=archive.stat().st_size)))
