from pathlib import Path
import json,hashlib,traceback,re
from CoupledTensor import check_tensor
from RimMath import rim_mass
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields

root=Path.cwd();folder=Path(__file__).parent;rows=[]
for group in ('DiscoveryFinal','ReservedReplay'):
 for original in json.loads((folder/group/'Receipt.json').read_text())['rows']:
  row=dict(id=original['id'],source=original['source'],sha256=original['sha256'],original_all_fields_passed=original['passed'])
  try:
   raw=(root/row['source']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];model=ReadDocument(raw);graph=BuildGraph(model);cache=ObjectFields(graph.OneClass('Body').Fields['cache']);metrics=rim_mass(*original['dimensions_cm'])
   row.update(passed=True,result=check_tensor(cache,metrics['volume'],metrics['area'],metrics['centroid'],metrics['moi'],metrics['cross']))
  except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
  rows.append(row)
report=dict(disposition='post-exposure replay; original11refusals retained; independent cohort proof separate',models=False,native_calls=0,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rule_freeze_sha256=hashlib.sha256((folder/'CoupledFreeze.json').read_bytes()).hexdigest(),rows=rows,summary=dict(sources=len(rows),passed=sum(r['passed'] for r in rows),original_mass_refusals=sum(not r['original_all_fields_passed'] for r in rows),max_central_cross_error=max(abs(v) for r in rows if r['passed'] for v in r['result']['central_cross_errors'])))
(folder/'CoupledRimReplay.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
