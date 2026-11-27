from pathlib import Path
import json,hashlib,traceback,re
from RimSource import read_source
from RimState import shape_state
from RimRecipe import recipe_witness
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive

root=Path.cwd();folder=Path(__file__).parent;cases=json.loads((root/'re/Fusion/RimFilletPack/Qualification/Cases.json').read_text());rows=[]
originals=[r for group in ('DiscoveryFinal','ReservedReplay') for r in json.loads((folder/group/'Receipt.json').read_text())['rows']]
for original in originals:
 row=dict(id=original['id'],source=original['source'],sha256=original['sha256'])
 try:
  raw=(root/row['source']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];model=ReadDocument(raw);graph=BuildGraph(model);f=graph.OneClass('DcFilletEdgeFeature');prior=ReadDualLive(model.Bodies[0].History,f.Fields['startModelHS']);s=read_source(graph,model,prior);r,h,amount=(s[n] for n in ('radius','height','fillet'));roles=shape_state(prior,r,h,0.)
  row['witness']=recipe_witness(prior,roles,s);case=next(c for c in cases if c['id']==row['id']);expected=case['case']
  assert all(abs(actual*10-expected[key])<1e-9 for actual,key in ((r,'radius_mm'),(h,'height_mm'),(amount,'fillet_mm')))
  observations=case['measurements'];assert observations['version']=='2706.1.17'
  for key in ('control_before','control_after'):
   control=observations[key];assert len(control['bodies'])==1 and control['bodies'][0]['solid'] and control['bodies'][0]['volume_cm3']>0 and all(t['health']==0 for t in control['timeline'])
  assert all(t['health']==0 for t in observations['initial']['timeline'])
  row.update(passed=True,dimensions_match_requested=True,healthy_source_controls=True,api_build=observations['version'])
 except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
 rows.append(row)
report=dict(disposition='additive post-exposure completeness checks; no new holdout claim',models=False,native_calls=0,sources={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ('RimRecipe.py','CheckBindings.py')},rows=rows,summary=dict(sources=len(rows),passed=sum(r['passed'] for r in rows)))
(folder/'Bindings.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
