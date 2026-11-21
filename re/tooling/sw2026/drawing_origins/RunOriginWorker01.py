from pathlib import Path, PureWindowsPath
from dataclasses import asdict, replace
from hashlib import sha256
import argparse
import codecs
import json
import os
import sys
import sysconfig


def digest(data):
    return sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--code',type=Path,required=True)
    parser.add_argument('--drawing',type=Path,required=True)
    parser.add_argument('--drawing-sha256',required=True)
    parser.add_argument('--child',type=Path,required=True)
    parser.add_argument('--child-sha256',required=True)
    parser.add_argument('--orientation',required=True)
    parser.add_argument('--mutation',default='none')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    drawing=args.drawing.read_bytes();child=args.child.read_bytes()
    if digest(drawing)!=args.drawing_sha256 or digest(child)!=args.child_sha256 or args.output.exists():
        raise ValueError('explicit disclosed input or output custody differs')
    sys.path[:0]=[str(args.root/'src'),str(args.root)]
    import convert.adapters.solidworks.Drawing.Definition.Profiles as package
    package.__path__=[str(args.code/'src/convert/adapters/solidworks/Drawing/Definition/Profiles'),*package.__path__]
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import WalkDrawNodes
    from convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex import ReadViewIndex
    from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.ReadOriginChild import ReadOriginChild
    from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.ReadOriginJoin import ReadOriginJoin
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
    for name in ('utf-16-le','utf-16-be','utf-8','cp1252'):
        codecs.lookup(name)
    allowed=[args.root.absolute(),args.code.absolute(),Path(__file__).parent.absolute(),
             Path(sys.base_prefix).absolute(),Path(sys.prefix).absolute(),Path(sysconfig.get_path('stdlib')).absolute()]
    unexpected=[];trusted=[]
    writing_report=False
    def is_model(value):
        return isinstance(value,(str,bytes,Path)) and str(value).casefold().endswith(('.sldprt','.sldasm','.slddrw'))
    def audit(event,values):
        if event!='open':return
        name=values[0]
        if is_model(name):
            unexpected.append({'event':event,'path':str(name)})
            raise ValueError('unexpected native model file read')
        if not isinstance(name,(str,bytes)):return
        path=Path(os.fsdecode(name)).absolute()
        if writing_report and path == args.output.absolute():return
        if any(path.is_relative_to(root) for root in allowed):trusted.append(str(path));return
        unexpected.append({'event':event,'path':str(name)})
        raise ValueError('undeclared runtime file access')
    sys.addaudithook(audit)
    for name in ('stat','lstat'):
        original=getattr(os,name)
        def checked_stat(path,*values,_original=original,_name=name,**options):
            if is_model(path):
                unexpected.append({'event':_name,'path':str(path)})
                raise ValueError('unexpected native model metadata read')
            return _original(path,*values,**options)
        setattr(os,name,checked_stat)
    archive=SldprtArchive.from_bytes(drawing)
    data=archive.require('Contents/Definition')
    parsed=ReadNamedDef(data,19000,args.orientation)
    item,=[value for group in parsed.ProfileDisplays for value in group.ItemsValue]
    index=ReadViewIndex(item.ViewValue)
    child_archive=SldprtArchive.from_bytes(child)
    resolved=ReadOriginChild(child,index.PathValue,args.child_sha256)
    original_resolved=resolved
    original_roots=resolved.LinkValue.ResolvedValue.RootsValue
    origin,=[value for value in original_roots if value and value.ClassValue.NameValue=='moOriginProfileFeature_c']
    ordinary,=[value for value in original_roots if value and value.ClassValue.NameValue=='moProfileFeature_c']
    reference=item.ViewValue.FieldsValue['f5d8']
    component=item.ReferenceValue.FieldsValue['f58']
    chain=component.FieldsValue['f20']
    entries=chain.FieldsValue['f08']
    external=entries.FieldsValue['f08'][0]['o']
    properties,=[value for value in WalkDrawNodes(parsed.GraphValue.DocumentValue) if value.ClassValue.NameValue=='moReferenceModel_c']
    header=resolved.LinkValue.ConfigValue.HeaderValue
    self_file=header.FieldsValue['f38']
    self_title=self_file.FieldsValue['shared']['h10'].FieldsValue['value']
    if isinstance(self_title,CStringValue):self_title=self_title.TextValue
    target=resolved.LinkValue.ResolvedValue
    def check_raw():
        configuration=resolved.LinkValue.ConfigValue
        config_bytes,emitted=WriteConfigMut(configuration.RootValue,19000,configuration.HeaderValue)
        body_bytes,_=WriteResolMut(target.RootsValue,target.ExtraFields,19000,emitted.MapValue,target.ContextValue)
        streams={'Contents/Definition':WriteNamedDef(parsed.GraphValue).OutputValue,
                 'Contents/Config-0-ModelHeader':WriteHeadGraph(configuration.HeaderValue,19000),
                 'Contents/CMgr':WriteCmgrMut(resolved.ManagerValue.RootValue,19000),
                 'Contents/Config-0':config_bytes,
                 'Contents/Config-0-ResolvedFeatures':body_bytes}
        expected={'Contents/Definition':data,**{name:child_archive.require(name) for name in streams if name!='Contents/Definition'}}
        if streams!=expected:raise ValueError('complete typed stream identity differs')
        return {name:digest(value) for name,value in streams.items()}
    before=check_raw()
    public_before=open_document(drawing,source_format='solidworks.slddrw',strict=False)
    public_hash=digest(json.dumps(asdict(public_before.DrawingValue),sort_keys=True).encode())
    child_document=open_document(child,source_format='solidworks.sldprt',strict=True,include_brep=False,include_tessellation=False)
    saved=[]
    def set_value(fields,key,value):
        saved.append((fields,key,fields[key]));fields[key]=value
    def config_value(key,value):
        set_value(reference.FieldsValue['f3c0'],key,value)
        if properties.FieldsValue['f3c0'] is not reference.FieldsValue['f3c0']:
            set_value(properties.FieldsValue['f3c0'],key,value)
    def duplicate_chain():
        set_value(entries.FieldsValue,'n',2)
        set_value(entries.FieldsValue,'f08',entries.FieldsValue['f08']*2)
    other_folder,=[value for group in parsed.ProfileDisplays if not group.ItemsValue for value in (group.FolderValue,)]
    modifications={
        'configuration_name':lambda:config_value('f08','incorrect configuration'),
        'configuration_id':lambda:config_value('f10',1),
        'ordinary_sketch_id':lambda:set_value(item.ReferenceValue.FieldsValue['ff0'],'f00',ordinary.FieldsValue['f08']),
        'negative_feature_id':lambda:set_value(item.ReferenceValue.FieldsValue['ff0'],'f00',-1),
        'creation_epoch':lambda:set_value(item.ReferenceValue.FieldsValue['ff0'],'f08',item.ReferenceValue.FieldsValue['ff0']['f08']+1),
        'chain_mode':lambda:set_value(chain.FieldsValue,'f24',1),
        'chain_entries':duplicate_chain,
        'chain_owner':lambda:set_value(component.FieldsValue,'owner',resolved.LinkValue.ConfigValue.RootValue),
        'chain_target':lambda:set_value(external.FieldsValue,'f50',properties),
        'display_folder':lambda:set_value(item.DisplayValue.FieldsValue,'f30',other_folder),
        'display_view':lambda:set_value(item.DisplayValue.FieldsValue,'f40',item.ViewValue.FieldsValue['owner']),
        'display_auxflag':lambda:set_value(item.DisplayValue.FieldsValue,'f200',2),
        'component_transform':lambda:set_value(item.ReferenceValue.FieldsValue,'f68',1),
        'manager_alias':lambda:set_value(resolved.ManagerValue.RootValue.FieldsValue,'f368',None),
        'self_selector':lambda:set_value(self_file.FieldsValue['refcfg'],'f08','incorrect configuration'),
        'acquisition_counter':lambda:set_value(chain.FieldsValue,'f20',chain.FieldsValue['f20']+1),
    }
    result={'passed':False,'mutation':args.mutation,'drawing_sha256':args.drawing_sha256,'child_sha256':args.child_sha256,
            'profile_role':'origin','source_full_admission':False,'public_strict_admission':False,'unexpected_runtime_file_attempts':unexpected,
            'still_sealed_inputs_read':0,'native_runs':0,'generated_cad_files':0}
    expected_rejection=args.mutation not in ('none','acquisition_counter')
    try:
        if args.mutation in modifications:modifications[args.mutation]()
        elif args.mutation=='resolver_wrong_path':resolved=replace(resolved,PathValue=index.PathValue.parent/'unmatched.SLDPRT')
        elif args.mutation=='resolver_relative':resolved=ReadOriginChild(child,PureWindowsPath('child.SLDPRT'),args.child_sha256)
        elif args.mutation=='resolver_suffix':resolved=ReadOriginChild(child,index.PathValue.with_suffix('.SLDASM'),args.child_sha256)
        elif args.mutation=='resolver_hash':resolved=ReadOriginChild(child,index.PathValue,'0'*64)
        elif args.mutation=='substituted_payload':resolved=ReadOriginChild(child[:-1]+bytes([child[-1]^1]),index.PathValue,args.child_sha256)
        elif args.mutation=='missing_origin':resolved=replace(resolved,LinkValue=replace(resolved.LinkValue,ResolvedValue=replace(target,RootsValue=tuple(value for value in original_roots if value is not origin))))
        elif args.mutation=='duplicate_origin':resolved=replace(resolved,LinkValue=replace(resolved.LinkValue,ResolvedValue=replace(target,RootsValue=original_roots+(origin,))))
        elif args.mutation!='none':raise ValueError('unknown fixture mutation')
        joined=ReadOriginJoin(item,resolved)
        if expected_rejection:raise RuntimeError('unqualified reference was admitted')
        if joined.ProfileValue is not origin or joined.SketchValue is not origin.FieldsValue['pd_f80']:
            raise RuntimeError('actual origin owners were replaced')
        if joined.NativeId!=origin.FieldsValue['f08'] or joined.CreatedAt!=DatumTime(header,joined.NativeId):
            raise RuntimeError('actual origin identity was changed')
        result['join']={'native_id':joined.NativeId,'created_at':joined.CreatedAt,'concrete_class':joined.ProfileValue.ClassValue.NameValue,
                        'same_actual_origin':True,'same_actual_sketch':True,'actual_sketch_index':joined.SketchValue.IndexValue,
                        'configuration_name':index.ConfigName,'configuration_id':index.ConfigId,
                        'resolver_path_matches':True,'child_self_title_matches_directory':self_title.casefold()==index.PathValue.stem.casefold(),
                        'can_hide_suppressed':joined.DisplayValue.CanHideSuppressed}
    except ValueError as error:
        if not expected_rejection:raise
        result['rejection']=str(error)
    finally:
        for fields,key,value in reversed(saved):fields[key]=value
        resolved=original_resolved
    result['complete_streams_before_after']=before==check_raw()
    result['typed_unprojected_retained']=list(parsed.Unprojected)
    public_after=open_document(drawing,source_format='solidworks.slddrw',strict=False)
    result['public_partial_unchanged']=digest(json.dumps(asdict(public_after.DrawingValue),sort_keys=True).encode())==public_hash
    result['public_partial_sha256']=public_hash
    result['public_diagnostic']=[value.code for value in public_after.diagnostics]
    result['public_sketch_count']=len(public_after.sketches)
    result['strict_child_read_completed']=True
    result['child_sketch_ids']=[value.id for value in child_document.sketches]
    try:open_document(drawing,source_format='solidworks.slddrw',strict=True)
    except Exception as error:result['public_strict_refusal']={'type':type(error).__name__,'message':str(error)}
    else:raise RuntimeError('public strict drawing reading was enabled')
    if unexpected or not result['complete_streams_before_after'] or not result['public_partial_unchanged']:
        raise RuntimeError('source graph or public read custody differs')
    result['passed']=True
    result['raw_stream_sha256']=before
    result['trusted_runtime_code_file_reads']=len(trusted)
    report=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    writing_report=True
    with args.output.open('xb') as output:
        output.write(report)
    print(json.dumps({'passed':True,'sha256':digest(report)}))


if __name__=='__main__':
    main()
