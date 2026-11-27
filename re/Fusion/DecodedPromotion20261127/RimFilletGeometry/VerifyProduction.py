from pathlib import Path
import json,hashlib,sys,subprocess,re,traceback
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import ReadRimContext
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import CheckRimPolicy
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimLive import CheckRimLive
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimSnaps import CheckRimSnaps
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimMass import CheckRimMass
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimSnapshot import ReadRimSnapshot
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.State.EncodeState import EncodeState

root=Path.cwd();folder=Path(__file__).parent;out=folder/'ProductionProof';out.mkdir(exist_ok=False);(out/'Documents').mkdir()
cases=json.loads((root/'re/Fusion/RimFilletPack/Qualification/Cases.json').read_text());rows=[]
for case in cases:
 name=case['id'];source=root/'re/Fusion/RimFilletPack/Sources'/case['case']['id']/'Native.f3d' if name.startswith('source-') else root/'re/Fusion/RimFilletPack/Qualification/Archives'/name/'Native.f3d';row=dict(id=name,source=str(source.relative_to(root)),sha256=case['source_sha256'])
 try:
  raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==case['source_sha256'];model=ReadDocument(raw);graph=BuildGraph(model);context=ReadRimContext(graph);CheckRimPolicy(model,graph,context);shape=ReadCircle(graph,context.Extrusion)
  prior,current=CheckRimLive(model,graph,context,shape);CheckRimSnaps(model,graph,context,shape,prior);CheckRimMass(context,shape.Geometry.radius,NumberValue(context.Extrusion.Along.Fields['value'])*10,NumberValue(context.Radius.Fields['value'])*10)
  assert model==ReadDocument(raw);row.update(passed=True,all_original_model_fields_retained=True,prior_entities=len(prior.Entities),current_entities=len(current.Entities),documents={})
  for role,value in [('Prior',prior),('Current',current),('Snapshot',ReadRimSnapshot(model))]:
   path=out/'Documents'/(name+'_'+role+'.json');path.write_text(json.dumps(EncodeState(value),indent=2,sort_keys=True)+'\n');row['documents'][str(path.relative_to(out))]=hashlib.sha256(path.read_bytes()).hexdigest()
 except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
 rows.append(row)
build={}
for module in tuple(sys.modules.values()):
 name=getattr(module,'__file__',None)
 if not name:continue
 path=Path(name).resolve()
 if path.is_file() and path.is_relative_to(root/'src'):build[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
executable=Path(sys.executable).resolve()
report=dict(base_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),models=False,native_calls=0,native_acceptance=False,scope='component source qualification only; public dispatch and output acceptance separate',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),python_version=sys.version,python_executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),runtime_source_sha256=build,rows=rows,summary=dict(files=len(rows),passed=sum(r['passed'] for r in rows),failed=sum(not r['passed'] for r in rows)))
(out/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
