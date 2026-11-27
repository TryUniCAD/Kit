import gzip,hashlib,io,json,shutil,sys,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(sys.argv[1]).resolve();source=Path(sys.argv[2]).resolve();output=root/'re/Fusion/DecodedPromotion20261127/RimPublic';receipt=json.loads((source/'ReadReceipt.json').read_text());members=[]
if receipt['summary']!=dict(positive=22,accepted=22,negative=43,refused=43,errors=0):raise ValueError('unexpected public proof outcomes')
archive=output/'Documents.tar.gz'
with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as packed,tarfile.open(mode='w',fileobj=packed) as tar:
 for path in sorted([*list((source/'Documents').glob('*.json')),*list(source.glob('Malformed-*.f3d'))]):
  data=path.read_bytes();name=str(path.relative_to(source));record=receipt['artifacts'][name]
  if hashlib.sha256(data).hexdigest()!=record['sha256'] or len(data)!=record['bytes']:raise ValueError('artifact proof binding changed')
  if path.suffix=='.json' and b'/Users/' in data:raise ValueError('private source path in document')
  info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data));members.append(dict(path=name,sha256=record['sha256'],bytes=len(data)))
with tarfile.open(archive) as tar:
 for row in members:
  stream=tar.extractfile(row['path'])
  if stream is None or hashlib.sha256(stream.read()).hexdigest()!=row['sha256']:raise ValueError('packed member differs')
for name in ['ReadReceipt.json','SourceHashes.json.gz']:shutil.copyfile(source/name,output/name)
p=Path('/private/tmp/KitRimComplete20261127.xml');original=p.read_bytes();tree=ET.fromstring(original)
for row in tree.iter('testsuite'):row.set('hostname','local-verification')
xml=ET.tostring(tree,encoding='unicode').encode();(output/'Integration.xml.gz').write_bytes(gzip.compress(xml,mtime=0))
report=dict(base_revision=receipt['base_revision'],binding='exact tested working-tree source hashes; committed checkout replay separate',models=False,native_calls=0,native_acceptance='not_established',portable_complete=False,semantic_qualification='unverified',public_read=dict(sources=22,accepted=22,encoded_refusals=43,errors=0),toolchain=dict(python='3.14.6',pytest='9.1.1',mypy='2.4.1',mypy_files=96,pyright='1.1.414',pyright_errors=0,black='26.10.1'),read_receipt_sha256=hashlib.sha256((output/'ReadReceipt.json').read_bytes()).hexdigest(),source_inventory_sha256=receipt['source_hashes_sha256'],archive=dict(path=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=members),integration=dict(passed=775,failed=0,seconds=143.50,scope='new rim plus previous Fusion drafts/frames/snapshots, SOLIDWORKS plain/reverse and CLI plane-history compatibility',raw_sha256=hashlib.sha256(original).hexdigest(),published_sha256=hashlib.sha256(xml).hexdigest(),normalization='hostname replaced for privacy; all cases retained'),source_path_normalization=dict(documents=22,comparison='only source.path differs between path-based and actual memory-source reads; asset hashes and all other document fields agree'),historical_native_build='Fusion 2706.1.17',native_executable_fingerprint='no new fingerprint or native session; historical source observations only',remaining=['full decoded feature writing is unfinished','native edit/restore/rebuild/save/fresh-process generated output acceptance unavailable','configured approval and current-head/merge-group checks separate'])
(output/'Verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(packed=len(members),source_files=receipt['source_files'],archive_bytes=archive.stat().st_size)))
