import hashlib,json,sys,tarfile
from pathlib import Path
folder=Path(sys.argv[1]).resolve()/'re/Fusion/DecodedPromotion20261127/RimFilletPolicy';manifest=json.loads((folder/'Manifest.json').read_text());packing=json.loads((folder/'GraphArchive.json').read_text());seal=json.loads((folder/'Seal.json').read_text());archive=folder/packing['archive']['path']
if hashlib.sha256((folder/'Manifest.json').read_bytes()).hexdigest()!=seal['manifest_sha256'] or seal['manifest_sha256']!=packing['original_manifest_sha256']:raise ValueError('original sealed manifest changed')
if hashlib.sha256(archive.read_bytes()).hexdigest()!=packing['archive']['sha256']:raise ValueError('graph archive changed')
with tarfile.open(archive) as tar:
 for row in manifest['files']:
  path=folder/row['path']
  if path.exists():data=path.read_bytes()
  else:
   stream=tar.extractfile(row['path'])
   if stream is None:raise ValueError('sealed member missing')
   data=stream.read()
  if hashlib.sha256(data).hexdigest()!=row['sha256'] or len(data)!=row['bytes']:raise ValueError('sealed logical member changed')
print(json.dumps(dict(sealed_logical_members=len(manifest['files']),archived_graphs=6,original_seal_unchanged=True)))
