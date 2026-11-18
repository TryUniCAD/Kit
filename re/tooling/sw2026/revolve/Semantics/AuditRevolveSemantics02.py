from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from math import cos, isclose, sin, tau
from pathlib import Path
import sys


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    request=loads(sys.stdin.read())
    row=request['input']
    source=Path(row['path'])
    data=source.read_bytes()
    require(sha256(data).hexdigest()==row['sha256'],'disclosed source custody differs')
    native=loads(Path(row['native_record']).read_bytes())
    require(sha256(Path(row['native_record']).read_bytes()).hexdigest()==row['native_record_sha256'],'native readback custody differs')
    require(native['passed'] and native['source_immutable'] and native['first_failure'] is None
        and not native['cleanup_errors'] and native['edit']['passed'] and native['edit']['setter_status']==0,
        'native source lifecycle or live driving edit is unhealthy')
    sys.path[:0]=[str(args.root/'Baseline01/src'),str(args.root)]
    from ReadOrdinaryRevolve01 import read_revolve
    from convert.adapters.solidworks.Container.Container import SldprtArchive,BuildSldprt
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    for name in ('ascii','utf-8','utf-16-le','utf-16-be','latin-1'):lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance','interchange.document.Behavior.DocumentIo',
                 'interchange.brep.Validation.BrepValidate','interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate','interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    audit_state={'enabled':False,'attempts':[]}
    def audit(event,arguments):
        if audit_state['enabled'] and (event=='open' or event.startswith(('subprocess.','socket.'))
            or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            audit_state['attempts'].append(event)
            raise RuntimeError('typed revolve projection attempted runtime external access')
    sys.addaudithook(audit)
    audit_state['enabled']=True
    try:
        archive=SldprtArchive.from_bytes(data)
        link=ReadNativeLink(archive,0)
        feature,=[node for node in IndexFeatures(link).values() if node.ClassValue.NameValue=='moRevolution_c']
        before=read_revolve(link,feature)
        mode=request['mode']
        ff=feature.FieldsValue
        end=ff['f8d8'].FieldsValue
        sf=before.Profile.FieldsValue['pd_f80'].FieldsValue
        af=ff['f830'].FieldsValue['f58'].FieldsValue
        axis_handle=af['f0f8'].FieldsValue
        selected_index=before.SelectionValue.attributes['native_axis_array_index']
        axis=sf['lines'][selected_index]['line']
        if mode=='invalid_reverse':ff['f824']=2
        elif mode=='legacy_type':ff['f820']=2
        elif mode=='second_angle':end['f20']=end['f18']
        elif mode=='missing_forward':end['f18']=None
        elif mode=='negative_angle':before.NativeParameter.FieldsValue['f58']=-1.1
        elif mode=='nonfinite_angle':before.NativeParameter.FieldsValue['f58']=float('nan')
        elif mode=='over_full_turn':before.NativeParameter.FieldsValue['f58']=tau+0.2
        elif mode=='parameter_expression':before.NativeParameter.FieldsValue['f20']='2*D1'
        elif mode=='axis_profile_mismatch':af['ff0']['f00']+=1
        elif mode=='axis_mark_mismatch':af['f100']+=1
        elif mode=='axis_index_outside':axis_handle['idx']=len(sf['lines'])
        elif mode=='boundary_selected':axis_handle['idx']=1
        elif mode=='degenerate_axis':
            sf['points'][axis['fcc_s']]['point']['pos']=dict(sf['points'][axis['fc8_s']]['point']['pos'])
        elif mode=='axis_relation':
            sf['dims']['log_g1'].append(sf['dims']['log_g1'][0].copy())
            sf['dims']['nlog1']+=1
        elif mode=='wrong_relation_geometry':sf['dims']['log_g1'][0]['d']['f80']=4
        elif mode=='region_selects_axis':
            region=sf['f5d8'].FieldsValue['items'][0]['o']
            region.FieldsValue['f08'].FieldsValue['items'][0]['o']=af['f0f8']
        elif mode=='presentation_cache':before.Display.FieldsValue['fad0']=987.654
        elif mode!='truth':raise ValueError('unregistered research mode')
        header=ReadHeaderGraph(archive.require('Contents/Config-0-ModelHeader'),19000)
        config_bytes,config=WriteConfigMut(link.ConfigValue.RootValue,19000,header)
        context=MakeLinkContext(config,ReadCmgrMut(archive.require('Contents/CMgr'),19000))
        resolved_bytes,resolved=WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,
            19000,config.MapValue,context)
        require(all(report['completed'] and not report['missing_schemas'] and not report['provisional_schemas']
            for report in (config.ReportValue,resolved.ReportValue)), 'prototype reached incomplete native grammar')
        exact=(config_bytes==archive.require('Contents/Config-0')
            and resolved_bytes==archive.require('Contents/Config-0-ResolvedFeatures'))
        if mode=='truth':require(exact,'source graph re-emission changed native logical bytes')
        streams=dict(archive.streams)
        streams['Contents/Config-0']=config_bytes
        streams['Contents/Config-0-ResolvedFeatures']=resolved_bytes
        repacked=BuildSldprt(streams,Template=data)
        second=ReadNativeLink(SldprtArchive.from_bytes(repacked),0)
        second_feature,=[node for node in IndexFeatures(second).values() if node.ClassValue.NameValue=='moRevolution_c']
        rejected=None
        try:projected=read_revolve(second,second_feature)
        except ValueError as error:rejected=str(error)
        expects_rejection=mode not in ('truth','presentation_cache')
        require((rejected is not None)==expects_rejection,'typed semantic admission decision differs')
        numeric=0
        observed=None
        if not expects_rejection:
            selected=projected.SelectionValue
            geometry=projected.SketchValue
            ordinary=[entity for entity in geometry.entities if not entity.construction]
            construction=[entity for entity in geometry.entities if entity.construction]
            require(len(ordinary)==4 and len(construction)==1 and not construction[0].fixed
                and len(geometry.constraints)==4 and not geometry.parameter_ids
                and len(geometry.closed_profile_entity_ids)==1
                and len(geometry.closed_profile_entity_ids[0])==4
                and all(rule.kind in ('horizontal','vertical') and len(rule.references)==1
                    and rule.references[0].entity_id!=construction[0].id for rule in geometry.constraints),
                'ordinary or construction geometry and actual solver intent changed')
            require(projected.ParameterValue.name=='D1' and projected.ParameterValue.value.unit=='rad'
                and projected.ParameterValue.value.value==native['reopened']['angle_radians']
                and projected.ReverseValue==native['reopened']['reverse'], 'actual live angular owner differs')
            require(all(isclose(actual,wanted,rel_tol=1e-12,abs_tol=1e-14)
                for observed,wanted_points in ((projected.RawAxisStartMetres,native['reopened']['axis']['points'][0]),
                    (projected.RawAxisEndMetres,native['reopened']['axis']['points'][1]))
                for actual,wanted in zip(observed,wanted_points,strict=True))
                and selected.attributes['native_line_creation_id']==native['reopened']['axis']['id'][1],
                'selected native axis identity or ordered endpoints differ')
            axis_x=construction[0].geometry.start.x*.001
            xy=[(p.x*.001,p.y*.001) for entity in ordinary for p in (entity.geometry.start,entity.geometry.end)]
            r0=min(p[0] for p in xy)-axis_x
            r1=max(p[0] for p in xy)-axis_x
            low=min(p[1] for p in xy)
            high=max(p[1] for p in xy)
            delta=r1*r1-r0*r0
            direction=projected.Definition.AxisDirection
            for key in ('reopened','edited'):
                sample=native[key]
                theta=sample['angle_radians']
                volume=(high-low)*theta*delta/2
                area=(high-low)*theta*(r0+r1)+theta*delta
                if not isclose(theta,tau,abs_tol=1e-12):area+=2*(high-low)*(r1-r0)
                factor=2*(r1**3-r0**3)/(3*theta*delta)
                center=(axis_x+factor*sin(theta),(low+high)/2,-direction.y*factor*(1-cos(theta)))
                for actual,wanted in ((sample['mass']['volume'],volume),(sample['mass']['area'],area),
                    *zip(sample['mass']['com'],center,strict=True)):
                    require(isclose(actual,wanted,rel_tol=2e-9,abs_tol=1e-12),
                        'independent positive right-hand sweep disagrees with native geometry')
                    numeric+=1
            observed={'driver_name':projected.ParameterValue.name,'radians':projected.ParameterValue.value.value,
                'reverse':projected.ReverseValue,'dimension_id':projected.Dimension.FieldsValue['f50'],
                'native_axis_array_index':selected.attributes['native_axis_array_index'],
                'native_axis_creation_id':selected.attributes['native_line_creation_id'],
                'native_axis_permanent_mark':selected.attributes['native_permanent_mark'],
                'axis_selection_path':[(v.entity_kind,v.entity_id) for v in selected.path],
                'raw_axis_start_m':projected.RawAxisStartMetres,'raw_axis_end_m':projected.RawAxisEndMetres,
                'effective_axis':(direction.x,direction.y,direction.z),'entities':len(geometry.entities),
                'construction_entities':1,'constraints':len(geometry.constraints),'axis_constraints':0,
                'retired_points':len(projected.RetiredPoints),'retired_lines':len(projected.RetiredLines),
                'native_solver_status_not_measured':True}
    finally:audit_state['enabled']=False
    require(not audit_state['attempts'] and sha256(source.read_bytes()).hexdigest()==row['sha256'],
        'runtime access or source immutability failed')
    origins=[name for name,module in tuple(sys.modules.items()) if name.startswith(('convert','interchange','readers'))
        and getattr(module,'__file__',None) and not Path(module.__file__).resolve().is_relative_to((args.root/'Baseline01/src').resolve())]
    require(not origins,'sdk runtime imported mutable worktree sources')
    print(dumps({'schema':'kit.sw2026.revolve-semantic-process.v1','name':row['name'],'mode':mode,'passed':True,
        'source_sha256':row['sha256'],'native_record_sha256':row['native_record_sha256'],'wire_reparsed':True,
        'truth_roundtrip_exact':exact,'rejected':rejected,'projection':observed,'native_geometry_numeric_checks':numeric,
        'runtime_external_access_attempts':audit_state['attempts'],'unexpected_sdk_origins':origins,
        'prototype_only':True,'sdk_source_changed':False,'heldout_inputs_read':0,'native_processes_started':0},sort_keys=True))


if __name__=='__main__':main()
