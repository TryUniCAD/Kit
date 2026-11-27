import argparse,hashlib,json,math,pathlib,sys
parser=argparse.ArgumentParser();parser.add_argument('--sdk-root',type=pathlib.Path,required=True);parser.add_argument('--revision',required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args()
if args.output.exists():raise ValueError('choose an unused output report')
sys.path.insert(0,str(args.sdk_root/'src'))
from convert import open_document
package=pathlib.Path(__file__).resolve().parent;manifest=json.loads((package/'Manifest.json').read_text());rows=[];failures=[]
for case in manifest['cases']:
 if case['case']['application']!='solidworks' or case['native_status']!='completed':continue
 truth=json.loads((package/case['ground_truth']).read_text());native={v['case']:v for v in truth['cases']}
 for item in case['files']:
  source=package/item['native_path'];raw=source.read_bytes();observed=native[source.stem]
  if hashlib.sha256(raw).hexdigest()!=item['source_sha256'] or item['source_sha256']!=observed['sha256']:raise ValueError('native control hash mismatch')
  for include_brep in [True,False]:
   row={'case':case['case']['id'],'source':item['native_path'],'source_sha256':item['source_sha256'],'include_brep':include_brep,'split':case['case']['split']}
   try:
    doc=open_document(raw,source_format='solidworks.sldprt',strict=True,include_brep=include_brep);body,=doc.bodies;box=body.topology.bounding_box
    if box is None:raise ValueError('no decoded bounds')
    low=[getattr(box.minimum,a) for a in 'xyz'];high=[getattr(box.maximum,a) for a in 'xyz'];lengths=[b-a for a,b in zip(low,high)];centroid=[(a+b)/2 for a,b in zip(low,high)]
    volume=math.prod(lengths);area=2*sum(lengths[a]*lengths[b] for a,b in [(0,1),(0,2),(1,2)]);native_center=[v*1000 for v in observed['centroid_m']]
    checks={'body_count':body.topology.solid_count==1,'volume':math.isclose(volume,observed['volume_m3']*1e9,rel_tol=1e-8,abs_tol=1e-6),'area':math.isclose(area,observed['area_m2']*1e6,rel_tol=1e-8,abs_tol=1e-6),'centroid':all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-6) for a,b in zip(centroid,native_center)),'dimensions':all(math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-6) for a,b in zip(sorted(lengths),sorted(observed['parameters_mm'].values())))}
    sketch,=doc.sketches;plane_id={'front':2,'top':3,'right':4}[case['case']['plane']];checks['support_plane']=sketch.support_plane_id==f'sldprt:plane:{plane_id}';checks['owned_reference']=sketch.attributes.get('support_plane_source') in ['plane-reference','typed-archive-reference'];checks['direction']=doc.feature_timeline[-1].definition.reversed==case['case']['reverse'];row.update(checks=checks,neutral_centroid_mm=centroid,native_centroid_mm=native_center,passed=all(checks.values()))
   except Exception as error:row.update(passed=False,error={'type':type(error).__name__,'message':str(error)})
   if not row['passed']:failures.append(row)
   rows.append(row)
sources={}
for relative in ['src/convert/adapters/solidworks/Core/Native.py','src/convert/adapters/solidworks/Core/Records/ReadLocalOwner.py','src/convert/adapters/solidworks/Core/Records/ReadPlaneOwner.py','src/convert/adapters/solidworks/Core/Records/ReadPlanePose.py']:
 sources[relative]=hashlib.sha256((args.sdk_root/relative).read_bytes()).hexdigest()
result={'candidate_revision':args.revision,'native_source_revision':manifest['source_revision'],'candidate_pr':270,'native_files':len(rows)//2,'reader_comparisons':len(rows),'passed':len(rows)-len(failures),'failed':len(failures),'cases':rows,'sdk_source_sha256':sources,'native_execution':'fresh source authoring and numerical measurements retained; candidate evaluated offline without native replay','comparison_limit':'ordinary cuboid bounds-derived mass and midpoint only; source plane and direction references also checked','heldout_limit':'parameter holdouts share one generator family; not independent-lineage qualification','full_semantics_verified':False,'native_conversion_acceptance':False}
args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['cases','sdk_source_sha256']}));raise SystemExit(bool(failures))
