from pathlib import Path
from dataclasses import replace
from io import BytesIO
from zipfile import ZipFile
import hashlib,json,traceback,re
from RimSource import read_source
from RimState import shape_state,drop_tracker
from RimAttributes import attributes
from RimSnapshot import snapshot_tags
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CanonicalBody import CanonicalBody
from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadSnapRoles import ReadSnapRoles
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from RimMath import rim_mass
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields,PointCoords
from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers

root=Path.cwd();folder=Path(__file__).parent;out=folder/'Counterexamples';out.mkdir(exist_ok=False)
source=root/'re/Fusion/RimFilletPack/Sources/discovery-01/Native.f3d';raw=source.read_bytes();original=ReadDocument(raw)

def corrupt(model,mode):
 graph=BuildGraph(model);feature=graph.OneClass('DcFilletEdgeFeature');history=model.Bodies[0].History;stateid=feature.Fields['endModelHS'];state=ReadDualLive(history,stateid)
 if mode=='chord_mode':return ChangeField(model,graph.OneClass('DcFilletEdgeData').ObjectId,'bChord',True)
 if mode=='history_end':return ChangeField(model,feature.ObjectId,'endModelHS',feature.Fields['startModelHS'])
 if mode=='radius_owner':
  radius=ResolveField(graph,graph.OneClass('DcFilletEdgeData'),'radiusValue','DcDoubleParameter');return ChangeField(model,radius.ObjectId,'rrOwnerFeature',None)
 if mode=='snapshot_height':
  part=model.Snapshots[0];snap=part.Snapshot;return replace(model,Snapshots=(replace(part,Snapshot=replace(snap,Model=replace(snap.Model,Height=snap.Model.Height*1.01))),))
 if mode=='selected_lower':
  recipe=graph.ResolveId(next(n.ObjectId for n in graph.ByClass('ASMRecipe') if getattr(getattr(n.Fields['m_Recipe'],'Value',None),'Payload',None).__class__.__name__=='EdgeRecipe'))
  value=recipe.Fields['m_Recipe'];encoded=value.Value;index=encoded.Payload.PrimaryTagIndex;tag,=encoded.Tags[index];lower=model.Snapshots[0].Snapshot.TagSet.BottomEdge
  tags=list(encoded.Tags);tags[index]=(replace(tag,PrimaryId=tuple(lower.PrimaryId.encode('ascii')),OperationIds=lower.OperationIds),)
  return ChangeField(model,recipe.ObjectId,'m_Recipe',replace(value,Value=replace(encoded,Tags=tuple(tags))))
 if mode=='mass_inertia':
  body=graph.OneClass('Body');cache=body.Fields['cache'];groups=tuple(replace(group,Fields=tuple(replace(field,Value=replace(field.Value,Fields=tuple(replace(axis,Value=axis.Value+1.) if axis.FieldName=='x' else axis for axis in field.Value.Fields))) if field.FieldName=='moi' else field for field in group.Fields)) for group in cache.Groups)
  return ChangeField(model,body.ObjectId,'cache',replace(cache,Groups=groups))
 prior=mode=='tracker_owner'
 if prior:stateid=feature.Fields['startModelHS'];state=ReadDualLive(history,stateid)
 target='TrackAttrib' if prior else 'TorusNode' if mode.startswith('torus') else 'EdgeNode' if mode=='seam_parameter' else 'CoedgeNode' if mode=='coedge_partner' else 'FaceNode'
 index=next(i for i,e in enumerate(state.Entities) if type(e).__name__==target)
 if mode=='top_winding':index=next(i for i,e in enumerate(state.Entities) if type(e).__name__=='FaceNode' and type(state.Entities[e.Surface]).__name__=='PlaneNode' and state.Entities[e.Surface].OriginCm[2]>0)
 table=MakeLiveTable(history,stateid);record=table.Records[sorted(table.LiveSlots)[index]];entity=history.Entities[record]
 if mode=='torus_major':changed=replace(entity,MajorRadiusCm=entity.MajorRadiusCm*1.01)
 elif mode=='torus_minor':changed=replace(entity,MinorRadiusCm=entity.MinorRadiusCm*1.1)
 elif mode=='torus_center':changed=replace(entity,CenterCm=(0.,0.,entity.CenterCm[2]+.01))
 elif mode=='tracker_owner':changed=replace(entity,TrackedId=entity.TrackedId+1)
 elif mode=='seam_parameter':changed=replace(entity,StartParam=entity.StartParam*.9)
 elif mode=='coedge_partner':changed=replace(entity,Partner=-1)
 elif mode=='top_winding':changed=replace(entity,Reversed=not entity.Reversed)
 else:raise ValueError(mode)
 entities=tuple(changed if i==record else e for i,e in enumerate(history.Entities));return replace(model,Bodies=(replace(model.Bodies[0],History=replace(history,Entities=entities)),))


def check(model,payload):
 graph=BuildGraph(model);feature=graph.OneClass('DcFilletEdgeFeature');prior=ReadDualLive(model.Bodies[0].History,feature.Fields['startModelHS']);current=ReadDualLive(model.Bodies[0].History,feature.Fields['endModelHS']);s=read_source(graph,model,prior);r,h,f=(s[k] for k in ('radius','height','fillet'))
 pr=shape_state(prior,r,h,0.);cr=shape_state(current,r,h,f);z=ZipFile(BytesIO(payload));snap=ReadGeometry(z.read(next(n for n in z.namelist() if n.endswith('/'+model.Snapshots[0].Name))));tags=snapshot_tags(snap)
 attributes(prior,pr,s,tags,graph,False);attributes(current,cr,s,tags,graph,True);clean,_=drop_tracker(prior,s['selected_edge'],s['operand']);root=next(i for i,role in ReadSnapRoles(snap) if role=='solid');assert CanonicalBody(clean,pr['root'])==CanonicalBody(snap,root)
 mass=rim_mass(r,h,f);cache=ObjectFields(s['body'].Fields['cache']);CacheNumbers(PointCoords(cache['moi']),mass['moi'])

rows=[]
for mode in ('chord_mode','history_end','radius_owner','snapshot_height','selected_lower','mass_inertia','torus_major','torus_minor','torus_center','tracker_owner','seam_parameter','coedge_partner','top_winding'):
 row=dict(mode=mode,source_sha256=hashlib.sha256(raw).hexdigest())
 try:
  payload=EmitParsed(corrupt(original,mode));path=out/(mode+'.f3d');path.write_bytes(payload);row.update(emitted=True,sha256=hashlib.sha256(payload).hexdigest(),candidate=path.name)
  model=ReadDocument(payload);row['typed_reparsed']=True
  try:check(model,payload);row.update(passed=False,error='unexpected acceptance')
  except (ValueError,AssertionError,TypeError) as exc:row.update(passed=True,refusal=type(exc).__name__+': '+str(exc))
 except Exception:row.update(passed=False,error=re.sub(r'/Users/[^/\s]+','<home>',traceback.format_exc().replace(str(root),'<checkout>')))
 rows.append(row)
report=dict(models=False,native_calls=0,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,summary=dict(cases=len(rows),passed=sum(r['passed'] for r in rows),emitted=sum(r.get('emitted',False) for r in rows),typed_reparsed=sum(r.get('typed_reparsed',False) for r in rows)))
(out/'Receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report['summary']))
