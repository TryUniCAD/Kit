import argparse,gzip,hashlib,json,math
from pathlib import Path
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
if args.output.exists():raise ValueError('choose an unused output report')
manifest=json.loads((root/'Manifest.json').read_text())
for row in manifest['artifacts']:
 path=(root/row['path']).resolve()
 if not path.is_relative_to(root):raise ValueError('artifact escapes package')
 raw=path.read_bytes();assert len(raw)==row['size_bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
matches=[]
for case in manifest['cases']:
 assert hashlib.sha256((root/case['capture_program']).read_bytes()).hexdigest()==case['capture_program_sha256']
 assert len(case['files'])==3
 truth=json.loads((root/'Cases'/case['case']/'GroundTruth.json').read_text())
 native={r['case']:r for r in truth['cases']}
 for row in case['files']:
  path=root/row['native_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['source_sha256']==native[path.stem]['sha256']
  document=json.loads(gzip.decompress((root/row['neutral_report']).read_bytes()))
  assert document['partial'] is False and document['layer']=='neutral' and row['exit_code']==0
  body,=document['document']['bodies']['$tuple']
  bounds=body['topology']['bounding_box']
  low=[bounds['minimum'][a] for a in ('x','y','z')];high=[bounds['maximum'][a] for a in ('x','y','z')]
  observed=native[path.stem]
  measured=observed['volume_m3']*1e9
  assert math.isclose(math.prod(b-a for a,b in zip(low,high)),measured,rel_tol=1e-8,abs_tol=1e-6)
  assert math.isclose(math.prod(observed['parameters_mm'].values()),measured,rel_tol=1e-8,abs_tol=1e-6)
  matches.append(all(math.isclose((a+b)/2,c*1000,rel_tol=1e-8,abs_tol=1e-6) for a,b,c in zip(low,high,observed['centroid_m'],strict=True)))
assert len(manifest['cases'])==37 and sum(len(c['files']) for c in manifest['cases'])==111
assert sum(matches)==15 and len(matches)-sum(matches)==96
assert manifest['neutral_cuboid_centroid_comparisons']=={'matched':sum(matches),'mismatched':len(matches)-sum(matches)}
assert manifest['full_semantics_verified'] is False and manifest['native_conversion_acceptance'] is False
result={'status':'passed','artifacts':len(manifest['artifacts']),'complete_cases':37,'strict_success_files':111,'centroid_mismatches_retained':len(matches)-sum(matches),'full_semantics_verified':False,'native_conversion_acceptance':False}
args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
