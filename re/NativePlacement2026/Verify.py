import argparse,pathlib,json,gzip,hashlib,math,collections
root=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args()
if args.output.exists():raise ValueError('choose an unused output report')
manifest=json.loads((root/'Manifest.json').read_text())
for item in manifest['artifacts']:
 path=(root/item['path']).resolve()
 if not path.is_relative_to(root):raise ValueError('artifact escapes package')
 raw=path.read_bytes();assert len(raw)==item['size_bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],item['path']
assert len(manifest['cases'])==48 and manifest['native_files_retained']==143 and manifest['planned_native_files']==144
assert collections.Counter(c['native_status'] for c in manifest['cases'])=={'completed':47,'failed':1}
assert manifest['known_missing_files']==['solidworks-020/control-after.SLDPRT']
report=json.loads((root/'Comparisons.json').read_text());actual=[];outcomes=collections.Counter()
for case in manifest['cases']:
 program=(root/case['capture_program']).read_bytes();assert hashlib.sha256(program).hexdigest()==case['case']['script_sha256']
 native={r['case']:r for r in json.loads((root/case['ground_truth']).read_text())['cases']} if case['native_status']=='completed' else {}
 assert len(case['files'])==(3 if native else 2)
 for item in case['files']:
  path=root/item['native_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['source_sha256'];outcomes[item['outcome']]+=1
  if native:
   observed=native[path.stem];assert item['source_sha256']==observed['sha256'];volume=observed.get('volume_m3',observed.get('volume_cm3',0))*(1e9 if case['case']['application']=='solidworks' else 1000)
   assert math.isclose(volume,math.prod(observed['parameters_mm'].values()),rel_tol=1e-8,abs_tol=1e-6)
  if 'neutral_report' not in item:assert item['outcome']=='strict_rejected_or_failed';continue
  envelope=json.loads(gzip.decompress((root/item['neutral_report']['path']).read_bytes()));assert envelope['partial'] is False and envelope['layer']=='neutral'
  if not native:assert item['native_batch_qualified'] is False;continue
  body,=envelope['document']['bodies']['$tuple'];bounds=body['topology']['bounding_box'];low=[bounds['minimum'][a] for a in 'xyz'];high=[bounds['maximum'][a] for a in 'xyz'];scale=1000 if case['case']['application']=='solidworks' else 10
  assert math.isclose(math.prod(b-a for a,b in zip(low,high)),volume,rel_tol=1e-8,abs_tol=1e-6)
  centroid=observed['centroid_m' if scale==1000 else 'centroid_cm'];match=all(math.isclose((a+b)/2,c*scale,rel_tol=1e-8,abs_tol=1e-6) for a,b,c in zip(low,high,centroid,strict=True));actual.append((case['case']['application'],match))
assert outcomes=={'strict_decoded':107,'strict_rejected_or_failed':36}
assert collections.Counter(actual)=={('solidworks',True):24,('solidworks',False):45,('fusion',True):36}
assert report['all_planned_jobs_settled'] is True and report['native_capture_complete'] is False
offline=json.loads((root/'OfflineOutcomes.json').read_text());assert len(offline)==255
for row in offline:
 source=root.parents[1]/row['asset'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256']
 for receipt in row['reader_receipts']:json.loads(gzip.decompress((root/receipt['path']).read_bytes()))
 assert bool(row['documents'])==(row['outcome']=='strict_decoded')
assert collections.Counter(r['outcome'] for r in offline)=={'strict_decoded':183,'strict_rejected_or_failed':72}
candidate=json.loads((root/'Candidate270Qualification.json').read_text());assert candidate['native_files']==69 and candidate['reader_comparisons']==138 and candidate['passed']==138 and candidate['failed']==0
assert manifest['full_semantics_verified'] is False and manifest['native_conversion_acceptance'] is False
result={'status':'passed','artifacts':len(manifest['artifacts']),'complete_native_batches':47,'retained_native_failures':1,'native_files':143,'missing_native_files':1,'offline_files':255,'baseline_centroid_mismatches_retained':45,'candidate270_comparisons':138,'full_semantics_verified':False,'native_conversion_acceptance':False}
args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
