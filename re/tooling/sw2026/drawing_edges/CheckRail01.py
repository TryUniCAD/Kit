from pathlib import Path
from hashlib import sha256
from dataclasses import replace, asdict
import argparse
import codecs
import json
import os
import sys
import sysconfig


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','drawing','child','output'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('drawing-sha256','child-sha256','orientation'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--mutation',default='none')
    args=parser.parse_args()
    drawing=args.drawing.read_bytes();child=args.child.read_bytes()
    digest=lambda data:sha256(data).hexdigest()
    if digest(drawing)!=args.drawing_sha256 or digest(child)!=args.child_sha256 or args.output.exists():raise ValueError('input/output custody differs')
    sys.path[:0]=[str(args.root/'src'),str(args.root),str(Path(__file__).parent)]
    import convert.adapters.solidworks.Drawing.Definition.Profiles as package
    package.__path__=[str(args.root/'re/tooling/sw2026/drawing_origins/Code02/src/convert/adapters/solidworks/Drawing/Definition/Profiles'),*package.__path__]
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
    from convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex import ReadViewIndex
    from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.ReadOriginChild import ReadOriginChild
    from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.ReadOriginJoin import ReadOriginJoin
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import ReadPrismLoop
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from RailJoin01 import resolve_rail
    helper=Path(resolve_rail.__code__.co_filename).resolve()
    if helper!=Path(__file__).resolve().with_name('RailJoin01.py'):raise RuntimeError('research helper came from another source path')
    helper_sha256=digest(helper.read_bytes())
    for name in ('utf-16-le','utf-8','cp1252'):codecs.lookup(name)
    allowed=[args.root.absolute(),Path(__file__).parent.absolute(),Path(sys.base_prefix).absolute(),Path(sys.prefix).absolute(),Path(sysconfig.get_path('stdlib')).absolute()]
    attempted=[]
    observing=True
    def model_name(value):return isinstance(value,(str,bytes,Path)) and str(value).casefold().endswith(('.sldprt','.sldasm','.slddrw'))
    def audit(event,values):
        if not observing or event!='open' or not isinstance(values[0],(str,bytes)):return
        name=values[0];p=Path(os.fsdecode(name)).absolute()
        if model_name(name) or not any(p.is_relative_to(root) for root in allowed):
            attempted.append({'event':event,'path':str(name)});raise RuntimeError('unexpected runtime filesystem read')
    sys.addaudithook(audit)
    for name in ('stat','lstat'):
        old=getattr(os,name)
        def checked(path,*values,_old=old,_name=name,**options):
            if observing and model_name(path):attempted.append({'event':_name,'path':str(path)});raise RuntimeError('unexpected model metadata access')
            return _old(path,*values,**options)
        setattr(os,name,checked)
    da=SldprtArchive.from_bytes(drawing);ca=SldprtArchive.from_bytes(child)
    parsed=ReadNamedDef(da.require('Contents/Definition'),19000,args.orientation)
    item,=[value for group in parsed.ProfileDisplays for value in group.ItemsValue]
    index=ReadViewIndex(item.ViewValue)
    origin=ReadOriginJoin(item,ReadOriginChild(child,index.PathValue,args.child_sha256))
    group,=parsed.DetailingMap.GroupsValue
    eligible=[entry for entry in group.RowsValue if [row['f08'].ClassValue.NameValue for row in entry.RefValue.FieldsValue['f10']]==['moFromSktEntSurfIdRep_c']*2+['moEndFaceSurfIdRep_c']*2]
    if not eligible:raise RuntimeError('no actual ordinary rail')
    entry=eligible[0]
    document=open_document(child,source_format='solidworks.sldprt',strict=True,include_brep=False,include_tessellation=False)
    link=origin.ChildValue.LinkValue
    def wire():
        config=link.ConfigValue;resolved=link.ResolvedValue
        config_raw,emitted=WriteConfigMut(config.RootValue,19000,config.HeaderValue)
        resolved_raw,_=WriteResolMut(resolved.RootsValue,resolved.ExtraFields,19000,emitted.MapValue,resolved.ContextValue)
        streams={'drawing_definition':WriteNamedDef(parsed.GraphValue).OutputValue,'header':WriteHeadGraph(config.HeaderValue,19000),'manager':WriteCmgrMut(origin.ChildValue.ManagerValue.RootValue,19000),'configuration':config_raw,'resolved':resolved_raw}
        expected={'drawing_definition':da.require('Contents/Definition'),'header':ca.require('Contents/Config-0-ModelHeader'),'manager':ca.require('Contents/CMgr'),'configuration':ca.require('Contents/Config-0'),'resolved':ca.require('Contents/Config-0-ResolvedFeatures')}
        if streams!=expected:raise RuntimeError('complete source streams changed')
        return {key:digest(value) for key,value in streams.items()}
    before=wire()
    public_before=open_document(drawing,source_format='solidworks.slddrw',strict=False)
    public_hash=digest(json.dumps(asdict(public_before.DrawingValue),sort_keys=True).encode())
    baseline=resolve_rail(group,entry,origin,document)
    fields=entry.RefValue.FieldsValue;reps=[row['f08'] for row in fields['f10']]
    fr=reps[0].FieldsValue['f10']['f10'];frfile=fr.FieldsValue['f08']
    features={node.FieldsValue['f08']:node for node in link.ResolvedValue.RootsValue if node and type(node.FieldsValue.get('f08')) is int}
    boss,=[node for node in features.values() if node.ClassValue.NameValue=='moExtrusion_c']
    owner=ReadExtrude(link,boss,features);loop=ReadPrismLoop(owner.ProfileValue,link)
    left,=[line for line in loop.LinesValue if line.PermanentId==reps[0].FieldsValue['f38']]
    opposite,=[line for line in loop.LinesValue if not ({line.StartValue,line.EndValue}&{left.StartValue,left.EndValue})]
    saved=[]
    def set_value(mapping,key,value):saved.append((mapping,key,mapping[key]));mapping[key]=value
    mutations={
      'feature':lambda:set_value(fr.FieldsValue['f10'],'f00',origin.NativeId),
      'epoch':lambda:set_value(fr.FieldsValue['f10'],'f08',fr.FieldsValue['f10']['f08']+1),
      'file_handle':lambda:set_value(frfile.FieldsValue['shared'],'h10',ArchiveNode(frfile.FieldsValue['shared']['h10'].ClassValue,dict(frfile.FieldsValue['shared']['h10'].FieldsValue))),
      'configuration':lambda:set_value(frfile.FieldsValue['refcfg'],'f10',index.ConfigId+1),
      'role_count':lambda:set_value(fields,'f08',3),
      'missing_marker':lambda:set_value(reps[0].FieldsValue,'f38',max(line.PermanentId for line in loop.LinesValue)+1),
      'nonadjacent_sides':lambda:set_value(reps[1].FieldsValue,'f38',opposite.PermanentId),
      'cap_contour':lambda:set_value(reps[2].FieldsValue,'f3c',1),
      'same_caps':lambda:set_value(reps[3].FieldsValue,'f38',reps[2].FieldsValue['f38']),
      'finite_range':lambda:set_value(fields,'f28',0.),
      'swap_sides':lambda:set_value(fields,'f10',[fields['f10'][1],fields['f10'][0],*fields['f10'][2:]]),
      'swap_boundaries':lambda:set_value(fields,'f10',[*fields['f10'][:2],fields['f10'][3],fields['f10'][2]]),
    }
    passed=False;result=None;rejection=None
    try:
        if args.mutation in mutations:mutations[args.mutation]()
        elif args.mutation=='model_key':group=replace(group,ModelKey=group.ModelKey+'invalid')
        elif args.mutation=='body_owner':document=replace(document,bodies=(replace(document.bodies[0],final_feature_id='sldprt:feature:'+str(origin.NativeId)),))
        elif args.mutation!='none':raise RuntimeError('unknown probe')
        result=resolve_rail(group,entry,origin,document)
        if args.mutation not in ('none','swap_sides','swap_boundaries'):raise RuntimeError('unsupported mutation admitted')
        if result['endpoint_set_model_m']!=baseline['endpoint_set_model_m']:raise RuntimeError('benign surface orientation changed the unordered geometry')
        passed=True
    except ValueError as error:
        if args.mutation in ('none','swap_sides','swap_boundaries'):raise
        rejection=str(error);passed=True
    finally:
        for mapping,key,value in reversed(saved):mapping[key]=value
    if wire()!=before:raise RuntimeError('post observation streams differ')
    public_after=open_document(drawing,source_format='solidworks.slddrw',strict=False)
    if digest(json.dumps(asdict(public_after.DrawingValue),sort_keys=True).encode())!=public_hash:raise RuntimeError('public layout changed')
    try:open_document(child,source_format='solidworks.sldprt',strict=True,include_tessellation=False)
    except Exception as error:default_refusal={'type':type(error).__name__,'message':str(error)}
    else:raise RuntimeError('default geometry admission unexpectedly changed')
    if default_refusal['message']!='SLDPRT contains no readable Parasolid payload':raise RuntimeError('default child refusal differs')
    if attempted:raise RuntimeError('unexpected runtime model read')
    report={'passed':passed,'mutation':args.mutation,'source_sha256':args.drawing_sha256,'child_sha256':args.child_sha256,
            'reader_tool_sha256':helper_sha256,'baseline':baseline,'result':result,'rejection':rejection,'eligible_rail_count':len(eligible),
            'raw_streams_before_after_identical':True,'raw_stream_sha256':before,'public_layout_unchanged':True,
            'public_layout_sha256':public_hash,'unprojected_unchanged':list(parsed.Unprojected),'default_brep_refusal':default_refusal,
            'additional_runtime_model_file_attempts':attempted,'child_partition_present':'Contents/Config-0-Partition' in ca.streams,'native_runs':0,'generated_native_files':0,
            'still_sealed_inputs_read':0,'new_heldout_credit':0,'native_endpoint_measurements':0,'native_kernel_identity':False}
    observing=False
    data=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode()
    args.output.write_bytes(data)
    print(json.dumps({'passed':passed,'sha256':digest(data)}))


if __name__=='__main__':main()
