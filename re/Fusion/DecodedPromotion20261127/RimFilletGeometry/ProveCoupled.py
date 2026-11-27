from pathlib import Path
from dataclasses import replace
import json,hashlib,traceback,re
from CoupledTensor import check_tensor
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields,PointCoords
from convert.Geometry.Extrude.Circular.DualSide.BuildDualSide import BuildDualSide
from convert.Geometry.Extrude.Circular.DualSide.MeasureDualMass import MeasureDualMass
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.ChangeDualMass import ChangeDualMass
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField

root=Path.cwd();folder=Path(__file__).parent;out=folder/'IndependentTensorProof';out.mkdir(exist_ok=False)
freeze=json.loads((folder/'CoupledFreeze.json').read_text());assert all(hashlib.sha256((folder/n).read_bytes()).hexdigest()==h for n,h in freeze['files'].items())
rows=[];negatives=[]
names=('baseline','baseline_edit_first','frame','frame_edit_second','holdout_a','holdout_b')
for name in names:
 sample=next(c for c in ReadDualCases() if c.Identity==name);row=dict(id=name,source=str(sample.Source.relative_to(root)),sha256=sample.Digest)
 try:
  raw=sample.Source.read_bytes();assert hashlib.sha256(raw).hexdigest()==sample.Digest;model=ReadDocument(raw);graph=BuildGraph(model);cache=ObjectFields(graph.OneClass('Body').Fields['cache'])
  _,volume,area,center,_=BuildDualSide(sample.Identity,sample.Frame,sample.Profile,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)
  diagonal,cross=MeasureDualMass(sample.Frame,sample.Profile,sample.FirstMm,sample.SecondMm,sample.FirstTaper,sample.SecondTaper)
  expected=(volume/1000,area/100,tuple(v/10 for v in (center.x,center.y,center.z)),tuple(v/100000 for v in (diagonal.x,diagonal.y,diagonal.z)),tuple(v/100000 for v in (cross.x,cross.y,cross.z)))
  row.update(passed=True,result=check_tensor(cache,*expected),actual_origin_cross=PointCoords(cache['moiOffDiag']),expected_origin_cross=expected[-1])
  if name=='baseline':baseline=(sample,model,graph,expected)
 except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
 rows.append(row)
sample,model,graph,expected=baseline;body=graph.OneClass('Body');cache=body.Fields['cache']
for field,axis in [('volume',''),('area',''),('cog','x'),('cog','y'),('cog','z'),('moi','x'),('moi','y'),('moi','z'),('moiOffDiag','x'),('moiOffDiag','y'),('moiOffDiag','z'),('wrong_sign',''),('missing_translation','')]:
 row=dict(field=field,axis=axis)
 try:
  if field in ('wrong_sign','missing_translation'):
   groups=tuple(replace(g,Fields=tuple(replace(f,Value=replace(f.Value,Fields=tuple(replace(a,Value=-a.Value if field=='wrong_sign' else 0.) for a in f.Value.Fields))) if f.FieldName=='moiOffDiag' else f for f in g.Fields)) for g in cache.Groups);changed_cache=replace(cache,Groups=groups)
  else:changed_cache=ChangeDualMass(cache,field,axis)
  changed=ChangeField(model,body.ObjectId,'cache',changed_cache);payload=EmitParsed(changed);path=out/(field+'_'+axis+'.f3d');path.write_bytes(payload);row.update(emitted=True,sha256=hashlib.sha256(payload).hexdigest(),candidate=path.name)
  reread=ReadDocument(payload);actual=ObjectFields(BuildGraph(reread).OneClass('Body').Fields['cache']);row['typed_reparsed']=True
  try:check_tensor(actual,*expected);row.update(passed=False,error='unexpected acceptance')
  except ValueError as error:row.update(passed=True,refusal=str(error))
 except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
 negatives.append(row)
report=dict(models=False,native_calls=0,rule_freeze_sha256=hashlib.sha256((folder/'CoupledFreeze.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,negatives=negatives,summary=dict(independent_native_sources=len(rows),passed=sum(r['passed'] for r in rows),serialized_negatives=len(negatives),negatives_refused=sum(r['passed'] for r in negatives),max_central_cross_error=max(abs(v) for r in rows if r['passed'] for v in r['result']['central_cross_errors'])))
(out/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
