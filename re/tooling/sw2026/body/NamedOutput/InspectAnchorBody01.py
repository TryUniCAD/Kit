from argparse import ArgumentParser
from json import dumps,loads
import os
from pathlib import Path,PureWindowsPath
from shutil import copyfile

import AuthorCurves as curves
from AuthorRectangleAnchors import CONTROL,ORACLE,control
import InspectSdkBlindPart as part
from InspectCornerPointOwners import point_info
from AnchorBodyGraph01 import check_relations,roles
from PredictAnchoredPart01 import prediction


SCHEMA='kit.sw2026.sdk-anchored-named-body-native.v1'
TOOLS={'AuthorCurves.py','AuthorRectangleAnchors.py','InspectFresh.py','InspectSdkBlindPart.py',
       'OracleIdentity.py','Swapp.py','InspectCornerPointOwners.py','PredictNamedOutput01.py',
       'PredictAnchoredPart01.py','AnchorBodyGraph01.py','InspectAnchorBody01.py'}
BASE_SNAPSHOT,BASE_VERIFY=part.snapshot,part.verify_state


def dimension(author,value):
    full=str(author.get(value,'FullName'))
    pieces=full.split('@')
    curves.require(len(pieces)>=3 and all(pieces[:2]),'actual dimension has no complete native feature ownership')
    return {'name':str(author.get(value,'Name')),'full_name':full,'reference':'@'.join(pieces[:2]),
            'value_m':float(author.get(value,'SystemValue')),
            'driving':int(author.get(value,'DrivenState'))==2 and not bool(author.get(value,'ReadOnly'))}


def snapshot(author,case):
    state=BASE_SNAPSHOT(author,case)
    bodies=tuple(author.get(author.typed(author.model,'PartDoc'),'GetBodies2',0,False) or ())
    curves.require(len(bodies)==1,'anchored named output requires exactly one actual solid')
    body,=bodies
    state.update(native_body_name=str(author.get(body,'Name')),native_body_type=int(author.get(body,'GetType')),
        complete_solid_count=len(bodies),topology={name:int(author.get(body,method)) for name,method in
            (('faces','GetFaceCount'),('edges','GetEdgeCount'),('vertices','GetVertexCount'))})
    state['actual_drivers']=[dimension(author,author.get(author.model,'Parameter',driver['reference']))|{'role':driver['role']}
                             for driver in case['intent']['drivers']]
    author.get(author.model,'ClearSelection2',True)
    extension=author.get(author.model,'Extension')
    curves.require(author.get(extension,'SelectByID2','Point1@'+case['intent']['origin_name'],'EXTSKETCHPOINT',
        0.0,0.0,0.0,False,0,author.sw.nothing(),0),'the actual model origin could not be selected')
    selection=author.get(author.model,'SelectionManager')
    origin=author.typed(author.get(selection,'GetSelectedObject6',1,-1),'SketchPoint')
    origin_owner=author.get(origin,'GetSketch')
    state['selected_origin']=point_info(author,origin,origin,origin_owner)
    manager=author.get(author.sketch,'RelationManager')
    relations=[]
    for relation in author.get(manager,'GetRelations',0) or ():
        entities=list(author.get(relation,'GetEntities') or ())
        kinds=list(author.get(relation,'GetEntitiesType') or ())
        curves.require(len(entities)==len(kinds)==int(author.get(relation,'GetEntitiesCount'))
            and all(kind in (2,3) for kind in kinds),'native relation entity domains are incomplete or unsupported')
        bindings=[author.entity_binding(entity,'point' if kind==2 else 'segment') for entity,kind in zip(entities,kinds,strict=True)]
        display=author.get(relation,'GetDisplayDimension')
        parameter=None if display is None else author.get(display,'GetDimension2',0)
        relations.append({'kind':int(author.get(relation,'GetRelationType')),
            'suppressed':bool(author.get(relation,'Suppressed')),'entity_types':kinds,
            'entity_ids':[binding['id'] for binding in bindings],
            'dimension':None if parameter is None else dimension(author,parameter),
            'point_owners':[point_info(author,entity,origin,origin_owner) for entity,kind in zip(entities,kinds,strict=True) if kind==2]})
    curves.require(int(author.get(manager,'GetRelationsCount',0))==len(relations),'native anchor relation walk is incomplete')
    state['relations']=relations
    state['constraint_status']=int(author.get(author.sketch,'GetConstrainedStatus'))
    author.get(author.model,'ClearSelection2',True)
    return state


def verify_state(recorder,state,case,expected_tree,*,edited):
    intent=case['intent']
    lengths=case['edited_dimensions_m'] if edited else case['initial_dimensions_m']
    target=case['edit']['expected'] if edited else case['expected_initial']
    curves.require([[row['name'],row['type'],row['parent']] for row in state['tree']]==expected_tree
        and not any(row['error'] or row['warning'] or row['suppressed'] for row in state['tree']),
        'anchored native tree differs or contains diagnostics')
    curves.require(state['configuration']==intent['configuration_name'] and state['sketch_parents']==[intent['support']]
        and state['boss_parents']==[intent['profile'],intent['support']],
        'anchored native configuration or actual profile dependencies differ')
    curves.require(state['body_count']==state['complete_solid_count']==1 and state['native_body_type']==0
        and state['native_body_name']==case['body_label'] and state['topology']=={'faces':6,'edges':12,'vertices':8}
        and state['whats_wrong']==0,'anchored native output body label topology or diagnostics differ')
    curves.require(state['dimension_driving'] and state['sketch_has_display_dimensions']
        and state['sketch_relation_count']==intent['relation_count'],'anchored native solver or display inventory differs')
    initial=state is recorder.data['result']['states'].get('Initial')
    curves.require(state['constraint_status'] in (1,3) if initial else state['constraint_status']==3,
        'the rebuilt anchored sketch is not fully constrained')
    recorder.close_number('active independently edited dimension',state['dimension_m'],lengths[case['edit']['role']])
    for actual,driver in zip(state['actual_drivers'],intent['drivers'],strict=True):
        curves.require(actual['role']==driver['role'] and actual['reference']==driver['reference']
            and actual['name']==driver['name'] and actual['driving'],
            'actual named driver lost its authored name or real feature owner')
        recorder.close_number('actual named '+driver['role'],actual['value_m'],lengths[driver['role']])
    for key,wanted in (('volume','volume_m3'),('area','area_m2'),('mass','mass_kg')):
        recorder.close_number('independent anchored '+key,state['mass'][key],target[wanted],absolute=1e-16)
    for actual,expected in zip(state['mass']['com'],target['centre_of_mass_m'],strict=True):
        recorder.close_number('independent anchored centroid',actual,expected)
    selected=state['selected_origin']
    curves.require(selected['same_origin_raw']==selected['same_self_raw']==selected['owner_same_origin_raw']==selected['owner_same_self_raw']==1
        and selected['owner_same_profile_raw']==0 and not selected['owner_null']
        and all(abs(value)<1e-10 for value in selected['position_m']),
        'selected actual model origin collapsed with the user sketch')
    observed=roles(state['sketch_geometry'],lengths,intent['anchor_kind'],recorder)
    origin=check_relations(state['relations'],observed,intent['drivers'],lengths,intent['anchor_kind'],recorder)
    observed.update(origin)
    prior=recorder.data.setdefault('actual_anchor_identity',observed)
    curves.require(observed==prior,'native edit changed the actual owned anchor and contour identities')
    if 'expected_saved_identity' in case:
        curves.require(observed==case['expected_saved_identity'],'fresh reopening changed the saved actual anchor identities')
    state['actual_anchor_identity']=observed


def verify(packet,expected):
    root=packet.parent.resolve(strict=True)
    curves.require(curves.digest(packet)==expected,'anchored named native packet changed')
    job=loads(packet.read_bytes())
    curves.require(job['schema']==SCHEMA and job['oracle_sha256']==ORACLE and job['control_sha256']==CONTROL
        and job['heldout_inputs_read']==0 and not job['public_writer_enabled'] and not job['original_source_qualification'],
        'anchored named native scope or exact oracle differs')
    tools=root/'Tools'
    curves.require(Path(__file__).resolve().parent==tools and set(job['tools_sha256'])==TOOLS,
        'anchored named native tooling closure differs')
    for name,wanted in job['tools_sha256'].items():
        curves.require(curves.digest(tools/name)==wanted,'anchored named native tool changed: '+name)
    for name,wanted in job['inputs_sha256'].items():
        path=(root/name).resolve(strict=True)
        curves.require(path.is_relative_to(root) and path.is_file() and curves.digest(path)==wanted,
            'anchored named native input changed: '+name)
    proof=loads((root/'ProcessProof.json').read_bytes())
    curves.require(proof['passed'] and proof['process_count']==55 and proof['source_unchanged']
        and proof['heldout_inputs_read']==0 and not proof['public_writer_registration_changed'],
        'anchored named native packet lacks the complete guarded qualification')
    cases=loads((root/'NeutralCases01.json').read_bytes())['cases']
    curves.require([case['name'] for case in job['cases']]==['CornerAscii','CenterWide'] and job['expected_native_processes']==16,
        'anchored named native cohort differs')
    for case in job['cases']:
        source=next(row for row in cases if row['name']==case['name'])
        build,repeat,default,reference=[loads((root/case[key]).read_bytes()) for key in ('named_build','repeat_build','plain_build','reference_build')]
        curves.require(build==repeat and all(row['passed'] for row in (build,repeat,default,reference))
            and build['plain_artifact_sha256']==default['artifact_sha256']==reference['artifact_sha256']
            and default['streams']==reference['streams'] and build['logical_stream_difference']==['Contents/Config-0','Contents/Config-0-ResolvedFeatures']
            and build['typed_roundtrip_exact'] and build['cross_stream_alias_exact']
            and not build['runtime_access_attempts'] and not build['unexpected_sdk_origins'] and not build['research_runtime_imports'],
            'anchored named output lacks actual graph and frozen baseline parity')
        curves.require(job['inputs_sha256'][case['named_file']]==build['artifact_sha256']
            and job['inputs_sha256'][case['plain_file']]==default['artifact_sha256'],'actual generated native files differ')
        for role in ('width','height','depth'):
            curves.require(case['predictions'][role]==prediction(build,source,role),'independent anchored neutral predictor differs')
        path=PureWindowsPath(source['part']['self_path'])
        curves.require(path.parent==PureWindowsPath(r'C:\KitSdkCandidates') and path.stem.startswith('SdkAnchorName')
            and path.name==source['part']['model_name']+'.SLDPRT','anchored native path is outside its exact owned namespace')
    return job


def stage(source,target,wanted,replace_hash):
    curves.require(curves.digest(source)==wanted,'anchored native staging source differs')
    target.parent.mkdir(exist_ok=True,parents=True)
    if target.exists():
        actual=curves.digest(target)
        if actual==wanted:
            return
        curves.require(actual==replace_hash,'anchored native slot contains unrelated bytes')
    copyfile(source,target)
    curves.require(curves.digest(target)==wanted,'anchored native staging changed bytes')


def run(packet,expected):
    curves.require(os.name=='nt','only root operates the exact licensed Windows oracle')
    job=verify(packet,expected)
    root=packet.parent
    output=root/'Inspection'
    output.mkdir()
    phases={}
    report={'schema':SCHEMA,'packet_sha256':expected,'phases':phases,'passed':False,
        'heldout_inputs_read':0,'public_writer_enabled':False,'original_source_qualification':False}
    part.snapshot,part.verify_state=snapshot,verify_state

    def checkpoint():
        curves.write_json(output/'Result.json',report)

    try:
        phases['ControlBefore']=control(output,'ControlBefore',root/'Control.SLDPRT')
        checkpoint()
        if phases['ControlBefore']['passed']:
            for case in job['cases']:
                name=case['name']
                path=Path(case['predictions']['depth']['intent']['self_path'])
                tree=part.tree_prediction(case['tree_request'],case['predictions']['depth'])
                plain_hash=job['inputs_sha256'][case['plain_file']]
                named_hash=job['inputs_sha256'][case['named_file']]
                stage(root/case['plain_file'],path,plain_hash,named_hash)
                plain_case=case['predictions']['depth']|{'body_label':case['predictions']['depth']['intent']['feature']}
                phases[name+'Plain']=part.phase(output,name+'Plain',path,plain_hash,plain_case,tree,measure_only=True)
                checkpoint()
                if not phases[name+'Plain']['passed']:
                    continue
                stage(root/case['named_file'],path,named_hash,plain_hash)
                for role in ('width','height','depth'):
                    stem=name+role.title()
                    predicted=case['predictions'][role]
                    phases[stem+'Edit']=part.phase(output,stem+'Edit',path,named_hash,predicted,tree)
                    checkpoint()
                    edited=phases[stem+'Edit']
                    if edited['passed']:
                        reopened=predicted|{'expected_saved_identity':edited['states']['Edited']['actual_anchor_identity']}
                        phases[stem+'Reopen']=part.phase(output,stem+'Reopen',output/(stem+'Edit')/'Edited.SLDPRT',
                            edited['derivative_sha256'],reopened,tree,edited_tree=edited['states']['Edited']['tree'])
                    checkpoint()
    except Exception as error:
        report['error']=repr(error)
    finally:
        try:
            phases['ControlAfter']=control(output,'ControlAfter',root/'Control.SLDPRT')
            verify(packet,expected)
            report['frozen_inputs_unchanged']=True
        except Exception as error:
            report['finalization_error']=repr(error)
        births={(row.get('oracle_identity',{}).get('process_id'),row.get('oracle_identity',{}).get('process_creation_filetime'))
                for row in phases.values() if row.get('oracle_identity')}
        report.update(controls_healthy=bool(phases.get('ControlBefore',{}).get('passed') and phases.get('ControlAfter',{}).get('passed')),
            distinct_processes=len(births))
        report['passed']=bool(len(phases)==len(births)==16 and report.get('frozen_inputs_unchanged') and all(row['passed'] for row in phases.values()))
        checkpoint()
        part.snapshot,part.verify_state=BASE_SNAPSHOT,BASE_VERIFY
    return report


def main():
    parser=ArgumentParser()
    parser.add_argument('command',choices=('verify','run'))
    parser.add_argument('packet',type=Path)
    parser.add_argument('--packet-sha256',required=True)
    args=parser.parse_args()
    packet=args.packet.resolve(strict=True)
    if args.command=='verify':
        verify(packet,args.packet_sha256)
        value={'passed':True,'processes_started':0}
    else:
        result=run(packet,args.packet_sha256)
        value={name:result[name] for name in ('passed','controls_healthy','distinct_processes')}
    print(dumps(value,sort_keys=True))
    raise SystemExit(0 if value['passed'] else 3)


if __name__=='__main__':
    main()
