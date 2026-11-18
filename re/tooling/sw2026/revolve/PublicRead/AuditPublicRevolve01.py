from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps,loads
from math import cos,isclose,sin,tau
from pathlib import Path
import sys


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=ArgumentParser()
    parser.add_argument('--sdk',type=Path,required=True)
    parser.add_argument('--candidate',action='store_true')
    args=parser.parse_args()
    row=loads(sys.stdin.read())
    path=Path(row['path'])
    data=path.read_bytes()
    require(sha256(data).hexdigest()==row['sha256'],'exact reader fixture custody differs')
    sys.path.insert(0,str(args.sdk/'src'))
    from convert import open_document
    from interchange.Core.Common import FreezeMapping
    from interchange.document.Models.DocumentCaps import InferCaps
    from interchange.Enums.EnumDocument import Capability
    from interchange.document.Behavior.DocumentIo import ToJson,FromJson
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.document.Validation.AngleRevValidate import GetLinkedAngle
    from interchange.Enums.EnumValues import ValueKind
    from interchange.Features.FeatureAngleRev import AngularRevolve
    from interchange.Records.RecordParameter import ParameterValue
    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        lookup(encoding)
    for name in ('interchange.document.Models.DocumentProvenance',
        'interchange.brep.Validation.BrepValidate','interchange.document.Validation.DocumentAssemblyValidate',
        'interchange.document.Validation.DocumentFeatureValidate','interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    audit_state={'enabled':False,'attempts':[]}
    def audit(event,arguments):
        if audit_state['enabled'] and (event=='open' or event.startswith(('subprocess.','socket.'))
            or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            audit_state['attempts'].append(event)
            raise RuntimeError('normal public revolve reader attempted additional runtime external access')
    sys.addaudithook(audit)
    audit_state['enabled']=True
    modes=(('no_geometry',{'include_brep':False,'include_tessellation':False}),
        ('brep_only',{'include_brep':True,'include_tessellation':False}),
        ('tessellation_only',{'include_brep':False,'include_tessellation':True}),
        ('both',{'include_brep':True,'include_tessellation':True}),('defaults',{}))
    results={}
    try:
        for name,options in modes:
            try:
                document=open_document(data,source_format='solidworks.sldprt',strict=True,**options)
            except (ValueError,TypeError,KeyError) as error:
                results[name]={'read_error':{'class':type(error).__name__,'message':str(error)},'projected':False}
                require(row['kind'] in ('unsupported_revolve','non_revolve_control'),
                    'original or presentation-only disclosed revolve failed its normal public read')
                continue
            document.assert_valid()
            serialized=ToJson(document)
            copy=FromJson(CadDocument,serialized)
            require(ToJson(copy)==serialized,'ordinary public model json roundtrip differs')
            projected=document.metadata.get('solidworks.typed_revolve_semantics',{}).get('status')=='projected'
            expect=args.candidate and row['kind']=='revolve'
            require(projected==expect,'public reader promoted an unmeasured profile or missed a measured one')
            numeric=0
            facts=None
            ordinary_hash=None
            if row['kind']=='revolve':
                native=row['native_observation']
                step,=[feature for feature in document.feature_timeline if feature.name=='OrdinaryBossRevolve']
                sketch,=[value for value in document.sketches if value.name=='RevolveSketch']
                feature_id=step.id
                param_ids=set(step.parameter_ids)
                if projected:
                    definition=step.definition
                    require(isinstance(definition,AngularRevolve),'public definition still uses a native or heuristic fallback')
                    require(definition.SideMode=='one_sided' and definition.AgainstParameterId is None,
                        'the public revolve mode differs from the actual one-sided owner')
                    parameter,=[value for value in document.parameters if value.id==definition.AlongParameterId]
                    require(parameter.name=='D1' and parameter.owner_id==step.id and parameter.value.unit=='rad'
                        and parameter.value.kind==ValueKind.KAngle and parameter.role.value=='driving',
                        'public positive angle is not the actual owned radian driver')
                    require(parameter.provenance is not None and parameter.provenance.spans
                        and parameter.provenance.spans[0].record_kind=='typed-archive-object'
                        and parameter.attributes['typed_archive_owner']['value_field']=='f58',
                        'public angular parameter lacks genuine object provenance')
                    selection,=[value for value in document.selections if value.id==definition.AxisSelectionId]
                    require(selection.id in step.selection_ids and len(selection.path)==2
                        and selection.path[0].entity_kind=='sketch' and selection.path[0].entity_id==sketch.id
                        and selection.path[1].entity_kind=='sketch_entity', 'public axis is not a real linked sketch entity selection')
                    axis,=[entity for entity in sketch.entities if entity.id==selection.path[1].entity_id]
                    lines=[entity for entity in sketch.entities if not entity.construction]
                    require(axis.construction and not axis.fixed and len(lines)==4 and len(sketch.entities)==5
                        and len(sketch.constraints)==4 and not sketch.parameter_ids
                        and len(sketch.closed_profile_entity_ids)==1
                        and set(sketch.closed_profile_entity_ids[0])=={entity.id for entity in lines}
                        and all(rule.kind in ('horizontal','vertical') and rule.parameter_id is None
                            and len(rule.references)==1 and rule.references[0].entity_id!=axis.id
                            for rule in sketch.constraints), 'public profile invented an axis constraint or changed actual contour topology')
                    endpoints=[(axis.geometry.start.x*.001,axis.geometry.start.y*.001,0.0),
                        (axis.geometry.end.x*.001,axis.geometry.end.y*.001,0.0)]
                    require(all(isclose(a,b,rel_tol=1e-12,abs_tol=1e-14)
                        for first,second in zip(endpoints,native['states']['reopened']['axis']['points'],strict=True)
                        for a,b in zip(first,second,strict=True)), 'public axis endpoints disagree with actual native selection')
                    xy=[(point.x*.001,point.y*.001) for entity in lines for point in (entity.geometry.start,entity.geometry.end)]
                    axis_x=endpoints[0][0]
                    r0=min(point[0] for point in xy)-axis_x
                    r1=max(point[0] for point in xy)-axis_x
                    low=min(point[1] for point in xy);high=max(point[1] for point in xy)
                    delta=r1*r1-r0*r0
                    for label in ('reopened','edited'):
                        state=native['states'][label]
                        if label=='edited':
                            edited=replace(document,parameters=tuple(replace(value,value=ParameterValue(
                                native['edit']['after_radians'],ValueKind.KAngle,'rad'))
                                if value.id==parameter.id else value for value in document.parameters))
                            edited.assert_valid()
                        else:edited=document
                        theta=GetLinkedAngle(step,definition.AlongParameterId,{value.id:value for value in edited.parameters})
                        require(isclose(theta,state['angle_radians'],rel_tol=1e-12,abs_tol=1e-14),
                            'public live angle edit and actual native driver differ')
                        volume=(high-low)*theta*delta/2
                        area=(high-low)*theta*(r0+r1)+theta*delta
                        if not isclose(theta,tau,abs_tol=1e-12):area+=2*(high-low)*(r1-r0)
                        factor=2*(r1**3-r0**3)/(3*theta*delta)
                        center=(axis_x+factor*sin(theta),(low+high)/2,
                            -definition.AxisDirection.y*factor*(1-cos(theta)))
                        for actual,wanted in ((state['mass']['volume'],volume),(state['mass']['area'],area),
                            *zip(state['mass']['com'],center,strict=True)):
                            require(isclose(actual,wanted,rel_tol=2e-9,abs_tol=1e-12),
                                'public linked sweep and independent original native geometry differ')
                            numeric+=1
                    facts={'parameter_id':parameter.id,'parameter_radians':parameter.value.value,
                        'parameter_native_id':parameter.provenance.native_id,
                        'axis_id':axis.id,'axis_permanent_mark':axis.attributes['native_line_permanent_id'],
                        'axis_creation_id':axis.attributes['native_line_creation_id'],
                        'axis_direction':(definition.AxisDirection.x,definition.AxisDirection.y,definition.AxisDirection.z),
                        'entities':5,'relations':4,'axis_relations':0,'contour_edges':4,
                        'timeline_rows':len(document.feature_timeline),'step_name':step.name,'step_order':step.order,
                        'native_solver_status_measured':False}
                comparable=replace(document,
                    sketches=tuple(value for value in document.sketches if value.id!=sketch.id),
                    parameters=tuple(value for value in document.parameters if value.id not in param_ids),
                    feature_timeline=tuple(value for value in document.feature_timeline if value.id!=feature_id),
                    selections=tuple(value for value in document.selections if value.id not in step.selection_ids
                        and not (value.query.get('native_owner_id')==31 and value.query.get('topology_role')=='direction_axis')),
                    metadata=FreezeMapping({key:value for key,value in document.metadata.items()
                        if key not in ('solidworks.typed_revolve_semantics','solidworks_source_semantic_sha256')}))
                comparable=replace(comparable,capabilities=InferCaps(comparable,
                    RoundtripMeta=Capability.KRoundtripMeta in document.capabilities))
                ordinary_hash=sha256(ToJson(comparable).encode()).hexdigest()
            results[name]={'projected':projected,'document_sha256':sha256(serialized.encode()).hexdigest(),
                'unrelated_semantics_sha256':ordinary_hash,'json_roundtrip_exact':True,
                'brep_sha256':sha256(ToJson(document.brep).encode()).hexdigest(),
                'tessellation_sha256':sha256(ToJson(document.meshes).encode()).hexdigest(),
                'bodies_sha256':sha256(ToJson(document.bodies).encode()).hexdigest(),
                'numeric_checks':numeric,'facts':facts,'capabilities':sorted(value.value for value in document.capabilities)}
    finally:audit_state['enabled']=False
    require(not audit_state['attempts'],'public runtime external access occurred')
    require(sha256(path.read_bytes()).hexdigest()==row['sha256'],'input bytes changed during public decoding')
    origins=[name for name,module in tuple(sys.modules.items()) if name.startswith(('convert','interchange','readers'))
        and getattr(module,'__file__',None) and not Path(module.__file__).resolve().is_relative_to((args.sdk/'src').resolve())]
    require(not origins,'public reader imported mutable or foreign sdk source modules')
    research=[name for name,module in tuple(sys.modules.items()) if getattr(module,'__file__',None)
        and '/re/tooling/' in str(module.__file__)]
    require(not research,'production reader imported research tooling')
    print(dumps({'schema':'kit.sw2026.public-revolve-reader-worker.v1','passed':True,'name':row['name'],
        'kind':row['kind'],'source_sha256':row['sha256'],'candidate':args.candidate,'modes':results,
        'runtime_external_access_attempts':audit_state['attempts'],'unexpected_sdk_origins':origins,
        'research_runtime_imports':research,'input_immutable':True,'heldout_inputs_read':0,
        'native_processes_started':0},sort_keys=True))


if __name__=='__main__':main()
