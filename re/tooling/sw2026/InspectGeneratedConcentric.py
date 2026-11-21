import argparse
import json
import sys
import os
from pathlib import Path
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))

from ConcentricNativeContract import ORACLE,ROLES,SCHEMA,checked,digest,require,signature,state_matches,summarize,validate_prediction,write_json


def input_path(row):
    return Path(row['guest_path'] if os.name=='nt' else row['host_path'])


def verify(packet,expected):
    packet=checked(packet,expected).resolve()
    root=packet.parent
    job=json.loads(packet.read_bytes())
    require(job['schema']==SCHEMA and job['oracle_sha256']==ORACLE and job['heldout_inputs_read']==0 and set(job['cases'])=={'Feature','Brep'},'expected the frozen disclosed generated concentric packet')
    require(Path(__file__).resolve().parent==root/'Tools','run the frozen observer closure')
    for name,value in job['tools_sha256'].items():checked(root/'Tools'/name,value)
    checked(root/'OriginalProtocol.json',job['protocol_sha256'])
    if job.get('guest_runtime'):checked(root/job['guest_runtime']['receipt_path'],job['guest_runtime']['receipt_sha256'])
    for case in job['cases'].values():
        for row in case['inputs'].values():checked(input_path(row),row['sha256'])
        for row in case['evidence'].values():checked(root/row['path'],row['sha256'])
        prediction=json.loads(checked(root/case['prediction_path'],case['prediction_sha256']).read_bytes())
        validate_prediction(prediction['generated']);validate_prediction(prediction['control'])
    return job


def same_file(value,expected):
    from ConcentricMateEvidence import same_file as match
    return match(value,expected)


def components(author,assembly,child_path,prediction):
    objects={}
    raw=author.get(assembly,'GetComponents',True) or ()
    require(len(raw)==int(author.get(assembly,'GetComponentCount',False))==2,'expected exactly two resolved direct components')
    wanted={value['name'] for value in prediction['occurrences']}
    for value in raw:
        component=author.typed(value,'Component2');name=str(author.get(component,'Name2'))
        require(name in wanted and name not in objects and same_file(author.get(component,'GetPathName'),child_path),'component name path or uniqueness differs')
        require(not author.get(component,'IsSuppressed') and not author.get(component,'IsHidden',False),'component is suppressed or hidden')
        objects[name]=component
    return [objects[value['name']] for value in prediction['occurrences']]


def capture(author,model,assembly,child_path,prediction,edited=False):
    import Swapp
    from AuthorAssemblySources import feature_tree
    from ConcentricMateEvidence import configuration,mate_state
    objects=components(author,assembly,child_path,prediction)
    child=author.get(objects[0],'GetModelDoc2')
    require(child is not None and same_file(author.get(child,'GetPathName'),child_path),'actual resolved child is unavailable')
    configs=[configuration(author,model,prediction['parent_configuration']),configuration(author,child,prediction['child_configuration'])]
    rows=[]
    for component in objects:
        loaded=author.get(component,'GetModelDoc2')
        require(loaded is not None and same_file(author.get(loaded,'GetPathName'),child_path),'component resolved a foreign child')
        count=len(author.get(author.typed(loaded,'PartDoc'),'GetBodies2',0,True) or ())
        require(count==1,'component has no actual one-solid child')
        rows.append({'name':str(author.get(component,'Name2')),'native_id':int(author.get(component,'GetID')),
            'configuration':str(author.get(component,'ReferencedConfiguration')),'fixed':bool(author.get(component,'IsFixed')),
            'visible_child_bodies':count,'transform':[float(value) for value in author.get(author.typed(author.get(component,'Transform2'),'MathTransform'),'ArrayData')]})
    geometry=prediction['edited' if edited else 'initial'];metrics={};diagnostics={}
    for role,target in (('child',child),('assembly',model)):
        diagnostics[role]=int(author.get(author.get(target,'Extension'),'GetWhatsWrongCount'))
        require(diagnostics[role]==0,'native document has errors or warnings')
        measured=author.rec.call('measure actual '+role+' geometry',Swapp.mass,target)
        require(measured is not None,'native mass properties are unavailable')
        for field in ('volume','area'):author.rec.close_number(role+' '+field,measured[field],geometry[role][field],absolute=1e-15)
        for index in range(3):author.rec.close_number(role+' centroid '+str(index),measured['com'][index],geometry[role]['com'][index],absolute=1e-12)
        metrics[role]=measured
    parameters={prediction['radial_parameter']:prediction['radial_value_m'],prediction['depth_parameter']:prediction['edited_depth_m'] if edited else prediction['depth_m']}
    dimensions={}
    for name,wanted in parameters.items():
        dimension=author.get(child,'Parameter',name)
        require(dimension is not None and int(author.get(dimension,'DrivenState'))==2 and not author.get(dimension,'ReadOnly'),'actual child dimension is not editable')
        dimensions[name]=float(author.get(dimension,'SystemValue'))
        author.rec.close_number(name,dimensions[name],wanted)
    mate_case={'mate_name':prediction['mate_name'],'radius_m':prediction['radius_m'],'center_m':prediction['center_m'],
               'lock_rotation':prediction['rotation_locked'],'api_alignment':prediction['api_alignment']}
    state={'occurrences':rows,'body_count':sum(row['visible_child_bodies'] for row in rows),'mass':metrics,
        'dimensions_m':dimensions,'configurations':configs,'diagnostic_counts':diagnostics,
        'tree':feature_tree(author,model),'child_tree':feature_tree(author,child),
        'mate':mate_state(author,model,assembly,child,objects,rows,mate_case)}
    state_matches(state,prediction,edited)
    return state,child


def prior_result(root,case,role,expected):
    path=root/'Inspection'/case/role/'Record.json'
    raw=json.loads(path.read_bytes());result=raw['result']
    require(raw['job']['packet_sha256']==expected and raw['job']['case']==case and raw['job']['phase']==role and result.get('passed') is True,'native prerequisite is missing or failed')
    return result


def phase(packet,expected,name,role):
    require(os.name=='nt','native observation requires the root-owned Windows guest')
    job=verify(packet,expected);root=packet.parent
    if job.get('guest_runtime'):
        import struct
        runtime=job['guest_runtime']
        require(tuple(sys.version_info[:3])==tuple(map(int,runtime['version'].split('.'))) and struct.calcsize('P')*8==runtime['pointer_bits'],'guest observer runtime differs from its verified receipt')
        require(Path(sys.executable).samefile(runtime['executable']),'guest observer used another interpreter')
    require(name in job['cases'] and role in ROLES,'unknown case or phase')
    case=job['cases'][name]
    prediction=json.loads((root/case['prediction_path']).read_bytes())
    control=role.startswith('Control')
    chosen=prediction['control' if control else 'generated']
    prefix='control_' if control else 'generated_'
    parent,child_path=(input_path(case['inputs'][prefix+key]) for key in ('parent','child'))
    generated_prior=None
    if role=='Generated':prior_result(root,name,'ControlBefore',expected)
    if role=='Reopen':
        generated_prior=prior_result(root,name,'Generated',expected)
        saved=generated_prior['saved']
        parent=Path(saved['parent_path']);child_path=Path(saved['child_path'])
        checked(parent,saved['parent']);checked(child_path,saved['child']['native_sha256'])
    target=root/'Inspection'/name/role
    target.mkdir(parents=True,exist_ok=False)
    from AuthorCurves import CurveAuthor,Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    import Swapp
    recorder=Recorder(target/'Record.json',{'case':name,'phase':role,'packet_sha256':expected})
    result={'passed':False,'case':name,'role':role,'started_at':time.time()};controller=None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call('verify idle generated concentric oracle',Swapp.sweep)
            controller=recorder.call('start fresh generated concentric oracle',Swapp.Sw)
            identity=recorder.call('verify pinned generated concentric oracle',application_identity,controller.app)
            require(identity['sha256']==ORACLE and identity['version_matches'] and identity['file_version']=='34.5.2.0604','unexpected native oracle build')
            result['oracle_identity']=identity
            author=CurveAuthor(controller.app,recorder,Swapp)
            result['document_count_before_open']=int(author.get(controller.app,'GetDocumentCount'))
            require(result['document_count_before_open']==0,'the cold assembly phase already has a loaded document')
            model,errors,warnings=recorder.call('cold open exact immutable concentric pair',controller.open,parent,read_only=True)
            result.update(open_errors=errors,open_warnings=warnings)
            require(model is not None and errors==warnings==0 and same_file(author.get(model,'GetPathName'),parent),'native load failed warned or selected another file')
            assembly=author.typed(model,'AssemblyDoc')
            edited=role=='Reopen'
            initial_child=author.get(components(author,assembly,child_path,chosen)[0],'GetModelDoc2')
            result['child_stamp_on_open']=int(author.get(initial_child,'GetUpdateStamp'))
            result['initial'],child=capture(author,model,assembly,child_path,chosen,edited)
            require(bool(author.get(model,'ForceRebuild3',False)),'native assembly rebuild failed')
            result['rebuilt'],child=capture(author,model,assembly,child_path,chosen,edited)
            result['child_stamp_after_rebuild']=int(author.get(child,'GetUpdateStamp'))
            require(signature(result['initial'])==signature(result['rebuilt']),'open/rebuild changed actual native identity')
            if role=='Generated':
                from ConcentricSourceRuntime import save_pair
                from InspectCombinedPlanarMates import native_save
                working=root/'Owned'/name
                owned_parent=working/parent.name;owned_child=working/child_path.name
                result['relocation_save']=save_pair(author,controller,model,assembly,child,owned_parent,owned_child)
                require(same_file(author.get(model,'GetPathName'),owned_parent) and same_file(author.get(child,'GetPathName'),owned_child),'SaveAs did not relocate the actual owned models')
                result['relocated'],child=capture(author,model,assembly,owned_child,chosen)
                require(signature(result['rebuilt'])==signature(result['relocated']),'relocation changed the native owners or tree')
                dimension=author.get(child,'Parameter',chosen['depth_parameter'])
                status=int(author.get(dimension,'SetSystemValue3',chosen['edited_depth_m'],1,Swapp.nothing()))
                result['depth_edit_status']=status
                require(status==0 and bool(author.get(child,'ForceRebuild3',False)) and bool(author.get(model,'ForceRebuild3',False)),'actual linked child depth edit or rebuild failed')
                result['edited'],child=capture(author,model,assembly,owned_child,chosen,True)
                saved=native_save(author,model,assembly,owned_parent,owned_child,2,recorder)
                saved.update(parent_path=str(owned_parent),child_path=str(owned_child))
                result['saved']=saved
                result['saved_state'],_=capture(author,model,assembly,owned_child,chosen,True)
                require(signature(result['edited'])==signature(result['saved_state']),'synchronized save changed the native identities')
            if role=='Reopen':
                require(result['child_stamp_on_open']==generated_prior['saved']['child']['update_stamp'],'fresh native child stamp differs from synchronized persistence')
                require(signature(result['rebuilt'])==signature(generated_prior['saved_state']),'fresh reopened native identities differ')
                checked(parent,generated_prior['saved']['parent']);checked(child_path,generated_prior['saved']['child']['native_sha256'])
            result['passed']=True
        except Exception as error:
            recorder.failure(error);result['error']=repr(error)
        finally:
            if controller is not None:
                try:controller.close();result['controller_diagnostics']=controller.diagnostics
                except Exception as error:recorder.failure(error,cleanup=True)
    result.update(dialogs=monitor.log,progress_windows=monitor.progress,finished_at=time.time())
    try:verify(packet,expected);result['immutable_inputs_unchanged']=True
    except Exception as error:recorder.failure(error);result['immutable_inputs_unchanged']=False
    result['passed']=bool(result['passed'] and result['immutable_inputs_unchanged'] and not result['dialogs'] and not result.get('controller_diagnostics')
                          and recorder.data['first_failure'] is None and not recorder.data['cleanup_errors'])
    result['numeric_checks']=len(recorder.data['checks'])
    recorder.data.update(result=result,passed=result['passed']);recorder.flush()
    return result


def summary(packet,expected):
    job=verify(packet,expected);records={}
    for name in job['cases']:
        records[name]={}
        for role in ROLES:
            path=packet.parent/'Inspection'/name/role/'Record.json'
            if path.exists():
                raw=json.loads(path.read_bytes())
                require(raw['job']['packet_sha256']==expected and raw['job']['case']==name and raw['job']['phase']==role,'stale native phase result')
                records[name][role]=raw.get('result',{'passed':False,'error':'partial phase record'})
    report=summarize(job,records)
    write_json(packet.parent/'Result.json',report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=('verify','phase','summary'))
    parser.add_argument('packet',type=Path)
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--case')
    parser.add_argument('--phase',choices=ROLES)
    args=parser.parse_args();packet=args.packet.resolve(strict=True)
    if args.command=='verify':verify(packet,args.packet_sha256);print('{"passed":true,"native_processes_started":0}');return 0
    if args.command=='summary':report=summary(packet,args.packet_sha256)
    else:report=phase(packet,args.packet_sha256,args.case,args.phase)
    print(json.dumps({'passed':report['passed']}));return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
