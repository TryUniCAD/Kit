import hashlib,json,sys,subprocess,traceback,re
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
from RimMath import rim_mass
from RimSource import read_source
from RimState import shape_state,drop_tracker,restore_tracker
from RimAttributes import attributes
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CanonicalBody import CanonicalBody
from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadSnapRoles import ReadSnapRoles
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import BodyClosure
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSheetBody import CheckSheetBody
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckSheetFrame import CheckSheetFrame
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from interchange.geometry.Models.Transform import KTransformIdentity
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields,PointCoords,NumberValue
from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import CircleCurve
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import ExtrudeSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import FilletSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import MeasurePart

root=Path.cwd();folder=Path(__file__).parent;out=folder/sys.argv[1];out.mkdir(exist_ok=False);(out/'Documents').mkdir()
mode=sys.argv[2];allcases=json.loads((root/'re/Fusion/RimFilletPack/Qualification/Cases.json').read_text())
cases=[c for c in allcases if c['id'].startswith('source-discovery-')==(mode=='discovery')]
report=dict(base_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),models=False,native_calls=0,mode=mode,rules_sha256=hashlib.sha256((folder/'Rules.md').read_bytes()).hexdigest(),scripts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.py')},rows=[])
for case in cases:
 name=case['id'];source=root/'re/Fusion/RimFilletPack/Sources'/case['case']['id']/'Native.f3d' if name.startswith('source-') else root/'re/Fusion/RimFilletPack/Qualification/Archives'/name/'Native.f3d'
 row=dict(id=name,source=str(source.relative_to(root)),sha256=case['source_sha256'],checks=[])
 try:
  raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==case['source_sha256'];model=ReadDocument(raw);graph=BuildGraph(model);feature=graph.OneClass('DcFilletEdgeFeature');prior=ReadDualLive(model.Bodies[0].History,feature.Fields['startModelHS']);current=ReadDualLive(model.Bodies[0].History,feature.Fields['endModelHS'])
  selected=read_source(graph,model,prior);r,h,f=(selected[n] for n in ('radius','height','fillet'));row.update(dimensions_cm=[r,h,f]);row['checks'].append('complete_source_radius_parameter_edge_body_state_binding')
  pr=shape_state(prior,r,h,0.);cr=shape_state(current,r,h,f);row['checks'].append('complete_prior_and_current_geometric_topology')
  snapshot=model.Snapshots[0].Snapshot
  row['attributes']={'prior':attributes(prior,pr,selected,snapshot,graph,False),'current':attributes(current,cr,selected,snapshot,graph,True)};row['checks'].append('all_live_attribute_chains_and_physical_tag_operations')
  archive=ZipFile(BytesIO(raw));snap=ReadGeometry(archive.read(next(n for n in archive.namelist() if n.endswith('/'+model.Snapshots[0].Name))));roles=ReadSnapRoles(snap);solid=next(i for i,role in roles if role=='solid')
  cleaned,removed=drop_tracker(prior,selected['selected_edge'],selected['operand']);assert restore_tracker(cleaned,removed)==prior;assert CanonicalBody(cleaned,pr['root'])==CanonicalBody(snap,solid);row['checks'].append('exact_predecessor_snapshot_canonical_body_after_owned_tracker_removal')
  closures=[BodyClosure(snap,solid)]
  for identity,role in roles:
   if role=='solid':continue
   closures.append(CheckSheetBody(snap,identity,CurveTag(selected['shape'].CurveNode)))
   for face in BodyFaces(snap,snap.Entities[identity]):CheckSheetFrame(snap,face,selected['shape'],KTransformIdentity)
  assert sum(map(len,closures))==len(snap.Entities)-1 and set().union(*map(set,closures))==set(range(1,len(snap.Entities)));row['checks'].append('all_saved_snapshot_sheets_and_disjoint_record_coverage')
  metrics=rim_mass(r,h,f);cache=ObjectFields(selected['body'].Fields['cache'])
  for label,actual,want in [('volume_area',(NumberValue(cache['volume']),NumberValue(cache['area'])),(metrics['volume'],metrics['area'])),('centroid',PointCoords(cache['cog']),metrics['centroid']),('inertia',PointCoords(cache['moi']),metrics['moi']),('cross',PointCoords(cache['moiOffDiag']),metrics['cross'])]:
   CacheNumbers(actual,want);row['checks'].append('saved_mass_'+label)
  native=case['measurements']['initial']['bodies'];assert len(native)==1 and native[0]['solid'];native=native[0]
  for label,actual,want in [('volume_area',(native['volume_cm3'],native['area_cm2']),(metrics['volume'],metrics['area'])),('centroid',native['centroid_cm'],metrics['centroid']),('lower',native['min_cm'],metrics['lower']),('upper',native['max_cm'],metrics['upper'])]:CacheNumbers(tuple(actual),tuple(want));row['checks'].append('actual_api_'+label)
  assert (native['faces'],native['edges'],native['vertices'])==(4,3,3);row['checks'].append('actual_api_topology')
  spec=DocumentSpec('Analytic cross-check','height',h*10,ProfileKind='part',Features=(ExtrudeSpec((CircleCurve((0.,0.),r*10),),h*10),FilletSpec((r*10,0.),f*10,LevelMm=h*10)))
  _,stages=SolvePart(spec);generated=MeasurePart(stages[-1].After);CacheNumbers((generated.VolumeCm,generated.AreaCm),(metrics['volume'],metrics['area']));row['checks'].append('existing_source_free_round_builder_independent_masses')
  row.update(passed=True,api_build=case['measurements']['version'],metrics=metrics,prior_entities=len(prior.Entities),current_entities=len(current.Entities),snapshot_entities=len(snap.Entities),cache_precision={k:cache[k] for k in ('volumePrec','areaPrec','inertiaPrec')},inertia_errors=[a-b for a,b in zip(PointCoords(cache['moi']),metrics['moi'],strict=True)],documents={})
  for label,value in [('Prior',prior),('Current',current),('Snapshot',snap),('CleanedPrior',cleaned),('RemovedTracker',removed)]:
   path=out/'Documents'/(name+'_'+label+'.json');path.write_text(json.dumps(EncodeState(value),indent=2,sort_keys=True));row['documents'][str(path.relative_to(out))]=hashlib.sha256(path.read_bytes()).hexdigest()
 except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
 report['rows'].append(row)
report['summary']=dict(files=len(cases),passed=sum(r['passed'] for r in report['rows']),failed=sum(not r['passed'] for r in report['rows']),checks=sum(len(r['checks']) for r in report['rows']))
(out/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
