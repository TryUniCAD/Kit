import argparse
import ast
from copy import deepcopy
import json
import math
from pathlib import Path,PureWindowsPath
from shutil import copyfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))

from ConcentricNativeContract import ORACLE,ROLES,SCHEMA,checked,close_numbers,digest,geometric_prediction,require,validate_prediction,write_json


def windows_path(path):
    path=Path(path).resolve()
    relative=path.relative_to(Path.home())
    return str(PureWindowsPath('\\\\Mac\\Home').joinpath(*relative.parts))


def input_row(path,wanted):
    path=checked(path,wanted).resolve()
    return {'host_path':str(path),'guest_path':windows_path(path),'sha256':wanted,'bytes':path.stat().st_size}


def tuple_constant(path,name):
    tree=ast.parse(path.read_text())
    for statement in tree.body:
        if isinstance(statement,ast.Assign) and any(isinstance(target,ast.Name) and target.id==name for target in statement.targets):
            require(isinstance(statement.value,ast.Tuple),'existing tool closure is not a tuple')
            values=[]
            for value in statement.value.elts:
                if isinstance(value,ast.Constant) and type(value.value) is str:values.append(value.value)
                elif ast.dump(value) in (ast.dump(ast.parse('Path(__file__).name',mode='eval').body),ast.dump(ast.parse('SCRIPT.name',mode='eval').body)):values.append(path.name)
                else:raise ValueError('unsupported source tool declaration')
            return tuple(values)
    raise ValueError('required existing source constant is absent')


def names_tree(rows,replacements):
    return [[replacements.get(value['name'],value['name']),value['type'],replacements.get(value['parent'],value['parent'])] for value in rows]


def control_prediction(case,saved,transforms):
    row={'mate_name':case['mate_name'],'radius_m':case['radius_m'],'center_m':case['center_m'],'depth_m':case['depth_m'],
        'edited_depth_m':case['edited_depth_m'],'parent_configuration':case['configuration'],'child_configuration':case['configuration'],
        'radial_parameter':'D1@CurveSketch','radial_value_m':case['radius_m'],'depth_parameter':'D1@CurveBoss','fixed_index':0,
        'rotation_locked':case['lock_rotation'],'api_alignment':case['api_alignment'],
        'endpoint_indexes':[next(index for index,row in enumerate(saved['source']['occurrences']) if row['name']==endpoint['occurrence']) for endpoint in saved['source']['mate']['ordered_endpoints']],
        'api_selected_endpoint_order':case['endpoint_order'],
        'occurrences':[{'name':case['child_name']+'-'+str(index+1),'transform':value} for index,value in enumerate(transforms)],
        'tree':names_tree(saved['source']['tree'],{}),'child_tree':names_tree(saved['source']['child_tree'],{})}
    for field,depth in (('initial',row['depth_m']),('edited',row['edited_depth_m'])):
        row[field]=geometric_prediction(row['radius_m'],row['center_m'],depth,transforms)
    return validate_prediction(row)


def generated_prediction(document,control,protocol):
    require(str(document.units)=='mm' and document.assembly is not None,'expected an authored millimetre assembly')
    graph=document.assembly
    require(len(graph.documents)==1 and len(graph.mates)==len(graph.mate_groups)==1,'expected one owned child and one mate')
    child=graph.documents[0].document
    require(str(child.units)=='mm' and len(child.sketches)==len(child.feature_timeline)==1,'expected the authored ordinary circle child')
    sketch=child.sketches[0];boss=child.feature_timeline[0];circle=sketch.entities[0].geometry
    parameters={value.owner_id:value for value in child.parameters}
    require(set(parameters)=={sketch.id,boss.id},'the actual radial/depth parameter ownership differs')
    radial=parameters[sketch.id];depth=parameters[boss.id]
    require(radial.value.unit==depth.value.unit=='mm','expected declared millimetre drivers')
    occurrences=sorted(graph.instances,key=lambda value:value.order)
    require([value.order for value in occurrences]==[0,1],'authored direct occurrence order differs')
    transforms=[]
    for occurrence in occurrences:
        matrix=occurrence.transform.values
        transforms.append([matrix[row+4*column] for row in range(3) for column in range(3)]+[matrix[3]*.001,matrix[7]*.001,matrix[11]*.001,1.0,0.0,0.0,0.0])
    entities={value.id:value for value in graph.mate_entities};indexes={value.id:index for index,value in enumerate(occurrences)}
    mate=graph.mates[0]
    fixed=[index for index,value in enumerate(occurrences) if value.fixed]
    require(len(fixed)==1 and str(mate.kind)=='concentric' and str(mate.alignment) in ('aligned','anti_aligned'),'authored mate intent differs')
    require(set(mate.attributes)=={'rotation_locked'} and type(mate.attributes['rotation_locked']) is bool,'authored rotation lock is incomplete')
    endpoint_indexes=[indexes[entities[identity].instance_path[0]] for identity in mate.entity_ids]
    expected=protocol['expected_readback']
    require([occurrences[index].name for index in endpoint_indexes]==expected['occurrence_order']
            and [value.fixed for value in occurrences]==expected['fixed_flags'],'protocol endpoint order or anchor differs from authored ownership')
    row={'mate_name':mate.name,'radius_m':circle.radius*.001,'center_m':[circle.center.x*.001,circle.center.y*.001],
        'depth_m':float(depth.value.value)*.001,'edited_depth_m':protocol['depth_edit']['target_m'],
        'radial_parameter':radial.name+'@'+sketch.name,'radial_value_m':float(radial.value.value)*.001,'depth_parameter':depth.name+'@'+boss.name,
        'parent_configuration':next(value.name for value in document.configurations if value.active),
        'child_configuration':next(value.name for value in child.configurations if value.active),
        'rotation_locked':mate.attributes['rotation_locked'],'api_alignment':0 if str(mate.alignment)=='aligned' else 1,
        'endpoint_indexes':endpoint_indexes,'fixed_index':fixed[0],
        'occurrences':[{'name':value.name,'transform':matrix} for value,matrix in zip(occurrences,transforms,strict=True)]}
    require(row['mate_name']==expected['mate_name'] and row['api_alignment']==expected['com_mate_alignment'] and row['rotation_locked'] is expected['rotation_locked'],'protocol mate semantics differ from the actual authored document')
    require(close_numbers([row['depth_m'],row['radius_m']],[expected['depth_m'],expected['radius_m']],relative=1e-12),'protocol dimensions differ')
    for field,depth_value in (('initial',row['depth_m']),('edited',row['edited_depth_m'])):
        row[field]=geometric_prediction(row['radius_m'],row['center_m'],depth_value,transforms)
        declared=expected['expected_geometry'] if field=='initial' else protocol['depth_edit']['expected_geometry']
        for role in ('child','assembly'):
            require(declared[role]['bodies']==(1 if role=='child' else 2)
                and close_numbers([row[field][role]['volume'],row[field][role]['area'],*row[field][role]['com']],
                    [declared[role]['volume_m3'],declared[role]['area_m2'],*declared[role]['center_m']],relative=1e-12,absolute=1e-15),'protocol geometry differs from the independent neutral prediction')
    control_names=[value['name'] for value in control['occurrences']]
    replacements={control_names[index]:occurrences[index].name for index in range(2)}
    replacements.update({control['mate_name']:mate.name,'CurveSketch':sketch.name,'CurveBoss':boss.name})
    def project(rows):
        return [[replacements.get(name,name),kind,replacements.get(parent,parent)] for name,kind,parent in rows]
    row['tree']=project(control['tree']);row['child_tree']=project(control['child_tree'])
    row['tree_expectation_source']='disclosed same-family native role tree with only actual authored feature/occurrence names replaced'
    return validate_prediction(row)


def prepare(args):
    repo=args.root.resolve(strict=True);source=repo/'re/tooling/sw2026'
    sys.path[:0]=[str(repo/'src'),str(source)]
    from interchange.serialization.Deserialize import FromData
    from ConcentricSourcePlan import disclosed_cases,expected_transforms
    protocol_path=args.protocol.resolve(strict=True)
    protocol=json.loads(protocol_path.read_bytes())
    require(protocol['schema']=='kit.sw2026.staged-concentric-native-deck.v1' and protocol['oracle_sha256']==ORACLE
        and protocol['native_processes_started']==protocol['heldout_inputs_opened']==0 and set(protocol['cases'])=={'Feature','Brep'},'expected the immutable disclosed scratch deck')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    tools=out/'Tools';tools.mkdir()
    shared=set(tuple_constant(source/'AuthorConcentricMateSources.py','TOOLS'))|set(tuple_constant(source/'InspectCombinedPlanarMates.py','TOOLS'))
    own=('ConcentricNativeContract.py','InspectGeneratedConcentric.py','PrepareGeneratedConcentric.py','CheckGeneratedConcentricContract.py')
    for name in sorted(shared):copyfile(source/name,tools/name)
    for name in own:copyfile(Path(__file__).with_name(name),tools/name)
    copyfile(protocol_path,out/'OriginalProtocol.json')
    data=out/'Evidence';data.mkdir()
    job={'schema':SCHEMA,'oracle_sha256':ORACLE,'heldout_inputs_read':0,'protocol_sha256':digest(protocol_path),'cases':{},
         'tools_sha256':{path.name:digest(path) for path in sorted(tools.iterdir())},'native_processes_started':0,
         'input_policy':'immutable cold readonly load, then native child-first relocation before edit',
         'unmeasured_paths':['generated cold native load and warning state','readonly child/parent SaveAs relocation','native child depth edit and synchronized persistence','fresh reopen and both anchors/order variants']}
    neutral_files={'Feature':args.feature_neutral,'Brep':args.brep_neutral}
    sources={value['id']:value for value in disclosed_cases()}
    for name,case in protocol['cases'].items():
        neutral=checked(neutral_files[name].resolve(),case['neutral_source_sha256'])
        document=FromData(json.loads(neutral.read_bytes()));document.AssertValid()
        control_parent=Path(case['source_control']['parent']['path']);control_child=Path(case['source_control']['child']['path'])
        control_root=control_parent.parents[2];source_id=control_root.name
        allowed=protocol_path.parent.parent/'ConcentricMateSourcePacket02'/'Disclosed'
        require(source_id in ('D01','D03') and control_root.resolve()==(allowed/source_id).resolve()
            and control_parent.parent==control_child.parent==control_root/'Native'/'Source','control custody is outside the declared disclosed cases')
        saved_path=control_root/'SavedAuthor.json';saved=json.loads(saved_path.read_bytes())
        require(saved['saved_files']['source']['parent']['sha256']==case['source_control']['parent']['sha256']
            and saved['saved_files']['source']['child']['sha256']==case['source_control']['child']['sha256'],'source control observation identity differs')
        source_case=sources[source_id]
        prediction_control=control_prediction(source_case,saved,expected_transforms(source_case))
        prediction_generated=generated_prediction(document,prediction_control,case)
        prediction={'generated':prediction_generated,'control':prediction_control,'heldout_inputs_read':0}
        prediction_path=data/(name+'Prediction.json');write_json(prediction_path,prediction)
        evidence={}
        for label,path in (('Neutral',neutral),('SourceAuthor',saved_path)):
            target=data/(name+label+'.json');copyfile(path,target)
            evidence[label]={'path':target.relative_to(out).as_posix(),'sha256':digest(target)}
        guarded=protocol_path.parent/(name+'GuardedBuild.json')
        checked(guarded,case['build_receipt_sha256'])
        target=data/(name+'GuardedBuild.json');copyfile(guarded,target)
        evidence['GuardedBuild']={'path':target.relative_to(out).as_posix(),'sha256':digest(target)}
        inputs={role:input_row(path,wanted) for role,path,wanted in (
            ('generated_parent',protocol_path.parent/case['parent']['path'],case['parent']['sha256']),
            ('generated_child',protocol_path.parent/case['child']['path'],case['child']['sha256']),
            ('control_parent',control_parent,case['source_control']['parent']['sha256']),
            ('control_child',control_child,case['source_control']['child']['sha256']))}
        job['cases'][name]={'inputs':inputs,'evidence':evidence,'prediction_path':prediction_path.relative_to(out).as_posix(),'prediction_sha256':digest(prediction_path)}
    runtime_source=protocol_path.parent/'GuestPython03.json'
    if runtime_source.exists():
        runtime=json.loads(runtime_source.read_bytes())
        require(runtime['pointer_bits']==64 and runtime['version'].startswith('3.12.'),'the declared guest runtime differs')
        if args.guest_python is not None:require(PureWindowsPath(runtime['executable'])==PureWindowsPath(args.guest_python),'guest interpreter override differs from its verified receipt')
        target=data/'GuestPython.json';copyfile(runtime_source,target)
        job['guest_runtime']={**runtime,'receipt_path':target.relative_to(out).as_posix(),'receipt_sha256':digest(target)}
    packet=out/'Trial.json';write_json(packet,job)
    packet_sha=digest(packet)
    host_prefix=['uv','run','--project',str(repo),'--isolated','--frozen','--extra','dev','--python','3.11','python','-I','-B',str(tools/'InspectGeneratedConcentric.py')]
    launcher_source=protocol_path.parent.parent/'ConcentricMateSourcePacket02'/'Recipe.json'
    prior_launcher=json.loads(launcher_source.read_bytes())['verify']
    script_index=next(index for index,value in enumerate(prior_launcher) if index>0 and str(value).lower().endswith('.py'))
    launcher=prior_launcher[:script_index]
    require(launcher and all(type(value) is str and value for value in launcher),'the disclosed source launcher is incomplete')
    if args.guest_python is not None:
        require(PureWindowsPath(args.guest_python).is_absolute() and PureWindowsPath(args.guest_python).suffix.lower()=='.exe','an interpreter override must be an absolute executable')
        launcher=[args.guest_python]
    guest_prefix=[*launcher,*([] if '-B' in launcher else ['-B']),windows_path(tools/'InspectGeneratedConcentric.py')]
    native_packet=windows_path(packet)
    recipe={'schema':SCHEMA,'phase_order':list(ROLES),'case_order':list(job['cases']),'packet_sha256':packet_sha,'verify_host':[*host_prefix,'verify',str(packet),'--packet-sha256',packet_sha],
        'verify_guest':[*guest_prefix,'verify',native_packet,'--packet-sha256',packet_sha] if guest_prefix else None,
        'cases':{name:{role:[*guest_prefix,'phase',native_packet,'--packet-sha256',packet_sha,'--case',name,'--phase',role] for role in ROLES} for name in job['cases']} if guest_prefix else None,
        'summary':[*guest_prefix,'summary',native_packet,'--packet-sha256',packet_sha] if guest_prefix else None,'native_recipe_ready':True,'launcher_source_sha256':digest(launcher_source),'guest_launcher_argv':launcher,
        'always_run_control_after_independently':True,'root_owns_native_transport':True,'native_processes_started':0}
    write_json(out/'Recipe.json',recipe)
    return {'packet_sha256':packet_sha,'recipe_sha256':digest(out/'Recipe.json'),'native_processes_started':0}


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','protocol','feature-neutral','brep-neutral','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--guest-python')
    args=parser.parse_args();print(json.dumps(prepare(args)))


if __name__=='__main__':main()
