import argparse
import codecs
from dataclasses import fields, replace
from hashlib import sha256
from io import BytesIO
import json
from math import cos, sin, radians
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--document-output',type=Path)
    args=parser.parse_args()
    request=json.loads(sys.stdin.read())
    sys.path[:0]=[str(Path(__file__).resolve().parent),str(args.root.resolve()/'src'),str(args.root.resolve()/'re/tooling/sw2026'),str(args.root.resolve()/'re/tooling/sw2026/serial')]
    from ConcentricNeutralAdmission import bind_cylinder, derive_brep, project_concentric
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
    from interchange.serialization.JsonCodec import DumpJson, LoadJson
    from interchange import MateAlignment, MateConstraint, MateEntity, MateEntityKind, MateGroup, frozen_mapping
    from interchange.geometry.Models.SupportPlane import SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
    from interchange.assembly.ComponentDefinition import ComponentDef
    from interchange.assembly.ComponentInstance import ComponentInst
    from interchange.assembly.TransformMatrix import TransformMatrix
    from interchange.document.Models.DocumentModel import AssemblyData, CadDocument, ComponentDoc
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordSource import CadSource
    from FreshCylinderInput import make_document
    from para.cylinder.CylinderAttachment import attach_cylinder_mut
    from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session, Update
    from para.rectangle.ArchiveAttachment import FeatureUpdate

    for encoding in ('utf-16-le','utf-16-be','cp1252'): codecs.lookup(encoding)
    shape=request['shape']
    spec={'name':'NeutralCylinder'+request['label'],'axis':'z','plane':'Front Plane','center_mm':shape['center_mm'],
          'radius_mm':shape['radius_mm'],'depth_mm':shape['depth_mm'],'driver':'diameter','reversed':False}
    child=make_document(spec)
    GetDocumentCaps(child)
    child.AssertValid()
    import importlib
    for name in ('DocumentComponentValidate','DocumentGraphValidate','DocumentMateEntityValidate','DocumentMateGroupValidate','DocumentMateValidate','DocumentMeshValidate'):
        importlib.import_module('interchange.document.Validation.'+name)
    active=False
    attempts=[]

    def guard(event,values):
        if active and event in {'open','subprocess.Popen','socket.connect','os.system','os.posix_spawn'}:
            attempts.append(event)
            raise RuntimeError('runtime operation during guarded neutral construction: '+event)
    sys.addaudithook(guard)

    def matrix_product(first,second):
        return tuple(tuple(sum(first[i][k]*second[k][j] for k in range(3)) for j in range(3)) for i in range(3))

    def apply(rotation,point):
        return tuple(sum(rotation[i][j]*point[j] for j in range(3)) for i in range(3))

    def rigid(rotation,translation):
        return TransformMatrix(tuple(value for i in range(3) for value in (*rotation[i],translation[i]))+(0.0,0.0,0.0,1.0))

    active=True
    try:
        stamp=1816300507+request['shape_index']*103
        candidate=PrepareNative(child,BytesIO(),stamp,WriteOptions(values={'final_destination':'C:\\KitConcentricNeutral\\'+spec['name']+'.SLDPRT'}))
        session=Session(3277+request['shape_index']*379,221+request['shape_index']*53,
            (DeltaEvent('activation'),MarkEvent('activation','activation',True),DeltaEvent('intervening'),
             MarkEvent('intervening','intervening',False),DeltaEvent('geometry'),MarkEvent('geometry','geometry',True)),
            (Update.ADVANCE,Update.ADVANCE,Update.ADVANCE,Update.ATTACH_BODY,Update.TESSELLATE),stamp,791+request['shape_index']*7)
        events=tuple(FeatureUpdate(index,stamp,index+1,True) for index in range(3))
        attached=attach_cylinder_mut(candidate,session,events,request['shape_index']*13)
        archive=SldprtArchive.from_bytes(attached.file_bytes)
        nodes=ReadCylNodes(archive)
        side,surface,body=PickCylFace(nodes)
        profile=request['profile']
        canonical_id='body/round-sweep-side-1-face'
        if profile=='authored_brep':
            shape_model=derive_brep(child,candidate.PlanValue)
            new_id='caller/lateral/'+request['label']
            child=replace(child,brep=replace(shape_model,
                faces=tuple(replace(value,id=new_id) if value.id==canonical_id else value for value in shape_model.faces),
                face_uses=tuple(replace(value,face_id=new_id) if value.face_id==canonical_id else value for value in shape_model.face_uses)))
            face_id=new_id
            if request.get('rekey_all'):
                shape_model=child.brep
                names=('curves','pcurves','surfaces','vertices','edges','coedges','loops','wires','faces','face_uses','shells','shell_uses','regions','bodies')
                ids={value.id:'caller/'+name+'/'+str(index) for name in names for index,value in enumerate(getattr(shape_model,name))}
                updated={}
                for name in names:
                    records=[]
                    for value in getattr(shape_model,name):
                        edits={}
                        for field in fields(value):
                            member=getattr(value,field.name)
                            if type(member) is str and member in ids: edits[field.name]=ids[member]
                            elif type(member) is tuple and member and all(type(item) is str and item in ids for item in member): edits[field.name]=tuple(ids[item] for item in member)
                        records.append(replace(value,**edits))
                    updated[name]=tuple(reversed(records))
                child=replace(child,brep=replace(shape_model,**updated))
                assert ids[new_id]==request['authored_face_id']
                face_id=request['authored_face_id']
        else: face_id=canonical_id
        model=bind_cylinder(child,candidate,nodes,profile=profile)
        x,y,z=tuple(radians(value) for value in (19.13,-27.47,33.71))
        rx=((1.0,0.0,0.0),(0.0,cos(x),-sin(x)),(0.0,sin(x),cos(x)))
        ry=((cos(y),0.0,sin(y)),(0.0,1.0,0.0),(-sin(y),0.0,cos(y)))
        rz=((cos(z),-sin(z),0.0),(sin(z),cos(z),0.0),(0.0,0.0,1.0))
        first=matrix_product(rz,matrix_product(ry,rx))
        twist=radians(41.29)
        spin=((cos(twist),-sin(twist),0.0),(sin(twist),cos(twist),0.0),(0.0,0.0,1.0))
        flip=((1.0,0.0,0.0),(0.0,-1.0,0.0),(0.0,0.0,-1.0))
        second=matrix_product(first,matrix_product(flip,spin) if request['alignment']=='anti_aligned' else spin)
        first_t=(-23.173,17.941,8.317)
        local=(*shape['center_mm'],0.0)
        origin=tuple(a+b for a,b in zip(apply(first,local),first_t,strict=True))
        axis=apply(first,(0.0,0.0,1.0))
        desired=tuple(a+53.719*b for a,b in zip(origin,axis,strict=True))
        second_t=tuple(a-b for a,b in zip(desired,apply(second,local),strict=True))
        placements=(rigid(first,first_t),rigid(second,second_t))
        configs=(Configuration('assembly/config','AssemblyActive',True),)
        root=ComponentDef('definition/root','ConcentricNeutral'+request['label'],'assembly',configuration_name='AssemblyActive',configuration_id='assembly/config')
        child_def=ComponentDef('definition/cylinder',child.metadata['name'],'part',document_id='document/cylinder',configuration_name='Default',configuration_id='config/default',body_ids=('body/round',))
        occurrences=tuple(ComponentInst('occurrence/'+str(index),'Cylinder-'+str(index+1),child_def.id,root.id,placements[index],index,
            configuration_name='Default',configuration_id='config/default',fixed=(index==request['fixed_index'])) for index in range(2))
        endpoints=tuple(MateEntity('endpoint/'+str(index),root.id,(occurrences[index].id,),MateEntityKind.CYLINDER,
            source_entity_id=face_id,radius=shape['radius_mm']) for index in range(2))
        order=(1,0) if request['reverse_selection'] else (0,1)
        mate=MateConstraint('mate/concentric','ConcentricAuthored','concentric',root.id,tuple(endpoints[index].id for index in order),
            alignment=MateAlignment(request['alignment']),attributes=frozen_mapping({'rotation_locked':request['rotation_locked']}))
        mutation=request.get('mutation','')
        if mutation=='missing_face': endpoints=(replace(endpoints[0],source_entity_id='caller/face/absent'),endpoints[1])
        elif mutation=='cap_face': endpoints=(replace(endpoints[0],source_entity_id='body/round-sweep-side-0-face'),endpoints[1])
        elif mutation=='native_index_face': endpoints=(replace(endpoints[0],source_entity_id='parasolid:face:99991'),endpoints[1])
        elif mutation=='same_occurrence': endpoints=(endpoints[0],replace(endpoints[1],instance_path=endpoints[0].instance_path))
        elif mutation=='nested_path': endpoints=(replace(endpoints[0],instance_path=(occurrences[0].id,occurrences[1].id)),endpoints[1])
        elif mutation=='both_fixed': occurrences=tuple(replace(value,fixed=True) for value in occurrences)
        elif mutation=='none_fixed': occurrences=tuple(replace(value,fixed=False) for value in occurrences)
        elif mutation=='wrong_radius': endpoints=(replace(endpoints[0],radius=shape['radius_mm']*1.01),endpoints[1])
        elif mutation=='radius_metres': endpoints=(replace(endpoints[0],radius=shape['radius_mm']*.001),endpoints[1])
        elif mutation=='missing_lock': mate=replace(mate,attributes=frozen_mapping({}))
        elif mutation=='integer_lock': mate=replace(mate,attributes=frozen_mapping({'rotation_locked':1}))
        elif mutation=='native_extensions': mate=replace(mate,attributes=frozen_mapping({'rotation_locked':False,'native_internal_alignment_code':1}))
        elif mutation=='unknown_alignment': mate=replace(mate,alignment=MateAlignment.UNKNOWN)
        elif mutation=='missing_radius': endpoints=(replace(endpoints[0],radius=None),endpoints[1])
        elif mutation=='different_config': occurrences=(occurrences[0],replace(occurrences[1],configuration_name='Other'))
        elif mutation=='reflected_pose':
            values=list(occurrences[1].transform.values)
            for index in (0,4,8): values[index]=-values[index]
            occurrences=(occurrences[0],replace(occurrences[1],transform=TransformMatrix(tuple(values))))
        elif mutation=='off_axis_pose':
            values=list(occurrences[1].transform.values);values[3]+=5.317
            occurrences=(occurrences[0],replace(occurrences[1],transform=TransformMatrix(tuple(values))))
        elif mutation=='wrong_axis_alignment': mate=replace(mate,alignment=MateAlignment.ANTI_ALIGNED if request['alignment']=='aligned' else MateAlignment.ALIGNED)
        elif mutation=='foreign_binding_document': model=replace(model,document=replace(child))
        elif mutation=='empty_face_id': endpoints=(replace(endpoints[0],source_entity_id=''),endpoints[1])
        elif mutation=='boolean_radius': endpoints=(replace(endpoints[0],radius=True),endpoints[1])
        elif mutation=='unknown_profile': model=replace(model,profile='unqualified')
        elif mutation=='neutral_surface_tag':
            shape_model=model.neutral_brep
            shape_model=replace(shape_model,surfaces=tuple(replace(value,attributes=frozen_mapping({'unrepresented':True})) if value.id==model.neutral_surface.id else value for value in shape_model.surfaces))
            child=replace(child,brep=shape_model)
            model=replace(model,document=child,profile='authored_brep')
        elif mutation in ('ring_radius','ring_parameter','edge_tolerance','body_transform','face_provenance','reordered_shell','extra_ring'):
            shape_model=model.neutral_brep
            if mutation=='ring_radius':
                first=shape_model.curves[0]
                shape_model=replace(shape_model,curves=(replace(first,radius=first.radius*1.001),*shape_model.curves[1:]))
            elif mutation=='ring_parameter':
                first=shape_model.edges[0]
                shape_model=replace(shape_model,edges=(replace(first,end_parameter=first.end_parameter-0.0137),*shape_model.edges[1:]))
            elif mutation=='edge_tolerance':
                first=shape_model.edges[0]
                shape_model=replace(shape_model,edges=(replace(first,tolerance=0.001),*shape_model.edges[1:]))
            elif mutation=='body_transform':
                first=shape_model.bodies[0]
                shape_model=replace(shape_model,bodies=(replace(first,transform=replace(first.transform,origin=SpaceVector(0.0,0.0,3.7))),))
            elif mutation=='face_provenance':
                from interchange.Records.RecordProvenance import Provenance
                first=shape_model.faces[0]
                shape_model=replace(shape_model,faces=(replace(first,provenance=Provenance(adapter='caller',native_id='owned/face')),*shape_model.faces[1:]))
            elif mutation=='reordered_shell':
                first=shape_model.shells[0]
                shape_model=replace(shape_model,shells=(replace(first,face_use_ids=tuple(reversed(first.face_use_ids))),))
            elif mutation=='extra_ring':
                first=shape_model.curves[0]
                shape_model=replace(shape_model,curves=(*shape_model.curves,replace(first,id='caller/extra-ring')))
            child=replace(child,brep=shape_model)
            model=replace(model,document=child,profile='authored_brep')
        elif mutation=='stale_kernel_identity':
            attribute=ReadCylAttr(nodes,side,'FACE_ID_2001'); lane=attribute.Indexes('fields')[2]
            node=nodes[lane];values=list(node.Indexes('values'));values[1]+=1
            changed=dict(nodes);changed[lane]=XmtNode(node.IndexValue,node.KindValue,{**node.FieldsValue,'values':tuple(values)})
            model=replace(model,nodes=changed)
        graph=AssemblyData(root.id,(root,child_def),occurrences,(ComponentDoc('document/cylinder',child),),endpoints,(mate,),
            (MateGroup('group/mates','Mates',root.id,(mate.id,)),))
        planes=[]
        for axis_name,caption in (('z','Front Plane'),('y','Top Plane'),('x','Right Plane')):
            frame=PrincipalFrame(axis_name)
            transform=Transform(SpaceVector(*(value*1000 for value in frame.OriginValue)),SpaceVector(*frame.AxisU),SpaceVector(*frame.AxisV),SpaceVector(*frame.NormalValue))
            planes.append(SupportPlane('assembly/datum/'+axis_name,caption,transform))
        document=CadDocument(CadSource('kit-neutral','<authored-concentric>',sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()),
            configs,(),tuple(planes),(),(),(),(),metadata={'name':root.name},assembly=graph)
        neutral_validation_errors=tuple(child.brep.GetErrors(frozenset(('body/round',)))) if child.brep is not None else ()
        try:
            intent=project_concentric(document,{child_def.id:model})
        except (ValueError,TypeError,KeyError) as exc:
            require_failure=bool(mutation)
            if not require_failure: raise
            result={'passed':True,'refused':True,'message':str(exc),'mutation':mutation}
        else:
            if mutation: raise AssertionError('malformed neutral owner unexpectedly accepted: '+mutation)
            assert intent.fixed_index==request['fixed_index']
            assert intent.alignment_code==(1 if request['alignment']=='aligned' else 2)
            assert intent.rotation_locked is request['rotation_locked']
            assert tuple(end.occurrence_index for end in intent.ends)==order
            assert all(end.binding.candidate is candidate and end.binding.child.FaceValue is side for end in intent.ends)
            assert all(end.entity is endpoints[index] and end.occurrence is occurrences[index] for end,index in zip(intent.ends,order,strict=True))
            feature=FieldInt(candidate.BossValue.FeatureValue.FieldsValue,'f08')
            marker=FieldInt(candidate.ProfileValue.GeometryValue.ArcValue.FieldsValue,'f08')
            assert ReadCylWords(nodes,side)==(74,feature,DatumTime(candidate.HeaderValue,feature),0,marker)
            expected_points=(origin,desired)
            for end,index in zip(intent.ends,order,strict=True):
                assert all(abs(a-b*.001)<1e-12 for a,b in zip(end.origin_m,expected_points[index],strict=True))
                assert abs(end.radius_m-shape['radius_mm']*.001)<1e-12
            try: PlanAsmWrite(document,'C:\\KitConcentricNeutral\\Assembly.SLDASM',stamp)
            except (ValueError,TypeError) as exc: public_refusal=str(exc)
            else: raise AssertionError('public assembly writer unexpectedly admitted a cylinder')
            result={'passed':True,'refused':False,'profile':profile,'neutral_face_id':face_id,
                'kernel_face_node_id':side.Integer('node_id'),'kernel_wire_face_index':side.IndexValue+1,
                'actual_body_atom_id':model.child.AtomValue,'actual_feature_id':feature,'actual_arc_marker':marker,
                'alignment_code':intent.alignment_code,'rotation_locked':intent.rotation_locked,
                'fixed_index':intent.fixed_index,'ordered_occurrence_indexes':list(order),
                'candidate_and_face_aliases':True,'neutral_document_retained':intent.document is document,
                'complete_neutral_identity_count':len(intent.ends[0].binding.neutral_id_map),
                'public_writer_refusal':public_refusal,'part_sha256':sha256(attached.file_bytes).hexdigest(),
                'ends':[{'entity':end.entity.id,'occurrence':end.occurrence.id,'origin_m':end.origin_m,'axis':end.axis,'radius_m':end.radius_m} for end in intent.ends]}
    finally: active=False
    assert not attempts
    if not mutation:
        restored=LoadJson(DumpJson(document))
        restored_child=restored.assembly.documents[0].document
        active=True
        try:
            restored_binding=bind_cylinder(restored_child,candidate,nodes,profile=profile)
            roundtrip=project_concentric(restored,{child_def.id:restored_binding})
            assert roundtrip.document is restored and all(value.binding.document is restored_child for value in roundtrip.ends)
            assert tuple(value.origin_m for value in roundtrip.ends)==tuple(value.origin_m for value in intent.ends)
            assert tuple(value.axis for value in roundtrip.ends)==tuple(value.axis for value in intent.ends)
            assert roundtrip.rotation_locked is intent.rotation_locked and roundtrip.alignment_code==intent.alignment_code
        finally: active=False
        result['normal_json_roundtrip_admitted']=True
    assert not attempts
    if args.document_output is not None:
        args.document_output.parent.mkdir(parents=True,exist_ok=True)
        assert not args.document_output.exists()
        args.document_output.write_text(DumpJson(document)+'\n')
    if mutation and child.brep is not None:
        result['neutral_validation_error_count']=len(neutral_validation_errors)
    result.update(pid=__import__('os').getpid(),runtime_io_attempts=len(attempts),hidden_inputs_read=0,native_processes=0,new_assembly_files=0)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    assert not args.output.exists()
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'result_sha256':sha256(args.output.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
