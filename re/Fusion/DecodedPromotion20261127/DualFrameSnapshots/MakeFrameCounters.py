from pathlib import Path
from dataclasses import replace
import json,hashlib,sys
root=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(root/'src'),str(root),str(Path(__file__).parent)]
from ProveFrameRule import validate,faces
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import TransformNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode

capture=json.loads((root/'re/Fusion/TwoSidedDraft20261127/Capture.json').read_text());case=next(c for c in capture['cases'] if c['id']=='frame');source=next(a for a in case['archives'] if a['file']=='frame.f3d');reading=next(o['value'] for o in case['observations'] if o['stage']=='baseline')
original=(root/'re/Fusion/TwoSidedDraft20261127/Native'/source['file']).read_bytes();assert hashlib.sha256(original).hexdigest()==source['sha256']
output=Path(sys.argv[1]);output.mkdir(exist_ok=False,parents=True);rows=[]
for mode in ('body_rotation','body_translation','body_reflection','shared_transform','profile_normal','world_sketch'):
    model=ReadDocument(original);state=model.Snapshots[0].Snapshot;entities=list(state.Entities)
    roles={('solid' if len(faces(state,e))>1 else 'profile' if faces(state,e)[0].DoubleSided else 'sketch'):i for i,e in enumerate(entities) if isinstance(e,BodyNode)}
    profile=entities[roles['profile']];transform=entities[profile.TransformRef];assert isinstance(transform,TransformNode)
    if mode=='body_rotation':entities[profile.TransformRef]=replace(transform,ColumnY=(0.,0.,-1.),ColumnZ=(0.,1.,0.),HasRotation=True)
    elif mode=='body_translation':entities[profile.TransformRef]=replace(transform,TranslationCm=(0.25,0.,0.))
    elif mode=='body_reflection':entities[profile.TransformRef]=replace(transform,ColumnX=(-1.,0.,0.),HasReflection=True)
    elif mode=='shared_transform':entities[roles['profile']]=replace(profile,TransformRef=entities[roles['solid']].TransformRef)
    elif mode=='profile_normal':
        face,=faces(state,profile);plane=entities[face.Surface];assert isinstance(plane,PlaneNode);entities[face.Surface]=replace(plane,Normal=(0.,0.,1.))
    else:
        profile_face,=faces(state,profile);world_plane=entities[profile_face.Surface];assert isinstance(world_plane,PlaneNode)
        face,=faces(state,entities[roles['sketch']]);plane=entities[face.Surface];assert isinstance(plane,PlaneNode);entities[face.Surface]=replace(plane,OriginCm=world_plane.OriginCm,Normal=world_plane.Normal)
    model=replace(model,Snapshots=(replace(model.Snapshots[0],Snapshot=replace(state,Entities=tuple(entities))),))
    row={'mode':mode}
    try:
        data=EmitParsed(model);path=output/(mode+'.f3d');path.write_bytes(data);decoded=ReadDocument(data)
        row.update(file=path.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),decoded_snapshot=type(decoded.Snapshots[0].Snapshot).__name__)
        validate(data,reading);row['status']='unexpected_accept'
    except Exception as error:row.update(status='refused',exception=type(error).__name__,message=str(error))
    rows.append(row)
report={'program_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source':'re/Fusion/TwoSidedDraft20261127/Native/frame.f3d','source_sha256':source['sha256'],'rule_seal_sha256':hashlib.sha256((Path(__file__).parent/'RuleSeal.json').read_bytes()).hexdigest(),'native_calls':0,'models':False,'counterexamples':rows}
(output/'Counterexamples.json').write_text(json.dumps(report,indent=2)+'\n');print({'counterexamples':len(rows),'refused':sum(r['status']=='refused' for r in rows),'encoded':sum('sha256'in r for r in rows)})
