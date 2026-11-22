import argparse,gzip,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
if args.output.exists():raise ValueError('choose an unused output report')
manifest=json.loads((root/'Manifest.json').read_text())
for row in manifest['artifacts']:
 path=(root/row['path']).resolve()
 if not path.is_relative_to(root):raise ValueError('artifact escapes package')
 raw=path.read_bytes();assert len(raw)==row['size_bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for case in manifest['cases']:
 assert len(case['files'])==3
 truth=json.loads((root/'Cases'/case['case']/'GroundTruth.json').read_text())
 native={r['case']:r for r in truth['cases']}
 for row in case['files']:
  path=root/row['native_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['source_sha256']==native[path.stem]['sha256']
  document=json.loads(gzip.decompress((root/row['neutral_report']).read_bytes()))
  assert document['partial'] is False and document['layer']=='neutral' and row['exit_code']==0
assert len(manifest['cases'])==37 and sum(len(c['files']) for c in manifest['cases'])==111
assert manifest['neutral_cuboid_centroid_comparisons']=={'matched':15,'mismatched':96}
assert manifest['full_semantics_verified'] is False and manifest['native_conversion_acceptance'] is False
result={'status':'passed','artifacts':len(manifest['artifacts']),'complete_cases':37,'strict_success_files':111,'centroid_mismatches_retained':96,'full_semantics_verified':False,'native_conversion_acceptance':False}
args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
