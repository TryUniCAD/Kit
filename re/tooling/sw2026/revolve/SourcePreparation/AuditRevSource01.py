import argparse
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


def require(condition,message):
    if not condition:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);parser.add_argument('--role',choices=('base','layer'),required=True)
    args=parser.parse_args();row=json.loads(sys.stdin.read())
    data=Path(row['path']).read_bytes();require(sha256(data).hexdigest()==row['sha256'],'disclosed source custody differs')
    native_bytes=Path(row['native_observation']['path']).read_bytes();require(sha256(native_bytes).hexdigest()==row['native_observation']['sha256'],'disclosed source native observer custody differs')
    native=json.loads(native_bytes)
    sys.path[:0]=[str(args.sdk/'src'),str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Core.Adapter import SemanticShaTwo
    from convert.adapters.solidworks.Container.Container import SldprtArchive,BuildSldprt
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from interchange.document.Behavior.DocumentIo import ToJson,FromJson
    from interchange.document.Models.DocumentModel import CadDocument
    from RevolveStreamAudit02 import stream_audit
    if args.role=='layer':
        from RevolveSourcePlan01 import source_plan,require_preparable
        from PredictSourceRevolve01 import compare
        from convert.adapters.solidworks.Archive.Construction.Units.MakeDualLength import MakeDualLength
        from RevolveSourcePlan01 import diff
        from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import KLengthCodes
    for encoding in ('ascii','utf-8','utf-8-sig','utf-16-le','utf-16-be','latin-1'):codecs.lookup(encoding)
    for name in ('interchange.brep.Validation.BrepValidate','interchange.document.Models.DocumentProvenance','interchange.document.Validation.AngleRevValidate','interchange.document.Validation.DocumentAssemblyValidate','interchange.document.Validation.DocumentFeatureValidate','interchange.document.Validation.DocumentReferenceValidate','interchange.document.Validation.PlaneRevValidate','interchange.document.Validation.DistExtValidate'):import_module(name)
    state={'enabled':False,'attempts':[]}
    def audit(event,arguments):
        if state['enabled'] and (event=='open' or event.startswith(('subprocess.','socket.')) or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            state['attempts'].append(event);raise RuntimeError('source preparation attempted external runtime access')
    sys.addaudithook(audit);state['enabled']=True
    output={'passed':False,'heldout_inputs_read':0,'native_processes':0}
    try:
        archive=SldprtArchive.from_bytes(data);link=ReadNativeLink(archive,0)
        variant=row.get('variant')
        if variant:
            if variant=='custom_note':
                cabinet=next(node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue=='moDetailCabinet_c')
                head=ReadChildren(cabinet)[0];head.FieldsValue['f18'].FieldsValue['f08']='Authored analysis notes'
            elif variant=='root_order':
                roots=link.ResolvedValue.RootsValue
                link=replace(link,ResolvedValue=replace(link.ResolvedValue,RootsValue=(roots[1],roots[0],*roots[2:])))
            elif variant=='extra_axis_relation':
                owner,=ReadRevOwners(link);dims=owner.SketchValue.FieldsValue['dims']
                dims['log_g1']=[*dims['log_g1'],dict(dims['log_g1'][0])];dims['nlog1']=len(dims['log_g1'])
            else:raise ValueError('unknown exact research variant')
            config_bytes,config=WriteConfigMut(link.ConfigValue.RootValue,19000,link.ConfigValue.HeaderValue)
            resolved_bytes,_=WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,19000,config.MapValue,link.ResolvedValue.ContextValue)
            streams=dict(archive.streams);streams[link.ConfigName]=config_bytes;streams[link.StreamName]=resolved_bytes
            data=BuildSldprt(streams,template=data,FormatVersion=4)
            archive=SldprtArchive.from_bytes(data);link=ReadNativeLink(archive,0)
        dual_proof=None
        if args.role=='layer' and not variant:
            length=link.ConfigValue.RootValue.FieldsValue['f9b8'].FieldsValue['items'][0]['o']
            primary=next(name for name,code in KLengthCodes.items() if code==length.FieldsValue['fb0'])
            old=length.FieldsValue['fb8'];generated=MakeDualLength(primary)
            require(not diff(old,generated),'generated dual-unit child differs from its complete actual source owner')
            require(generated is not old,'dual-unit builder reused a source owner')
            length.FieldsValue['fb8']=generated
            try:
                replaced_config,new_config=WriteConfigMut(link.ConfigValue.RootValue,19000,link.ConfigValue.HeaderValue)
                replaced_resolved,_=WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,19000,new_config.MapValue,link.ResolvedValue.ContextValue)
                require(replaced_config==archive.require(link.ConfigName) and replaced_resolved==archive.require(link.StreamName),'new dual owner changed source wire or reference allocation')
                dual_proof={'source_fields_identical':True,'fresh_object':True,'config_byte_identity':True,'resolved_byte_identity':True,'primary_unit':primary,'generated_secondary_unit':next(name for name,code in KLengthCodes.items() if code==generated.FieldsValue['fb0'])}
            finally:length.FieldsValue['fb8']=old
        streams,metadata=stream_audit(archive,link)
        require(all(value['qualified'] for value in metadata.values()),'actual typed Biography or History is incomplete')
        modes={};docs={}
        for name,options in [('no_geometry',{'include_brep':False,'include_tessellation':False}),('brep_only',{'include_brep':True,'include_tessellation':False}),('tessellation_only',{'include_brep':False,'include_tessellation':True}),('both',{'include_brep':True,'include_tessellation':True}),('defaults',{})]:
            try:
                doc=open_document(data,source_format='solidworks.sldprt',strict=True,**options);doc.assert_valid();encoded=ToJson(doc)
                require(ToJson(FromJson(CadDocument,encoded))==encoded,'strict source neutral JSON identity differs')
                require(doc.metadata['solidworks_source_semantic_sha256']==SemanticShaTwo(doc),'source semantic digest does not match the actual final document')
                tree=doc.metadata['solidworks.typed_resolved_semantics']['native_tree']
                if not variant and args.role=='layer':
                    expected=[(value['name'],value['type']) for value in native['reopened']['features']]
                    actual=[(value['name'],value['type']) for value in tree['rows'] if value['parent_id'] is None]
                    require(actual==expected,'actual original native top-level tree names/types/order differ')
                    require(len(tree['rows'])==25 and len(doc.feature_timeline)==19,'source ownership projection did not retain all root/member records')
                elif variant:
                    require(tree['status']=='unqualified','an unsupported source variant was accepted into ordinary presentation')
                docs[name]=json.loads(encoded)
                modes[name]={'document_sha256':sha256(encoded.encode()).hexdigest(),'timeline_count':len(doc.feature_timeline),'native_tree_status':tree['status'],'native_tree_rows':len(tree.get('rows',())),'brep_bodies':len(doc.brep.bodies) if doc.brep else 0,'payloads':len(doc.brep_payloads),'source_document':docs[name]}
            except ValueError as error:
                if not variant:raise
                modes[name]={'error_class':type(error).__name__,'error_message':str(error)}
        if not variant and args.role=='layer':
            owner,=ReadRevOwners(link)
            doc=open_document(data,source_format='solidworks.sldprt',strict=True,include_brep=False,include_tessellation=False)
            plan=source_plan(archive,link,owner,ReadModelDef(archive.require('Contents/Definition'),19000).GraphValue,ReadCmgrMut(archive.require('Contents/CMgr'),19000).RootValue,ReadHeaderGraph(archive.require('Header2'),19000),ReadHistMut(archive.require('_MO_VERSION_19000/History'),19000),ReadHistMut(archive.require('_MO_VERSION_19000/Biography'),19000),doc)
            try:require_preparable(plan)
            except ValueError as error:refusal={'refused':True,'diagnostic':str(error)}
            else:raise ValueError('original source escaped the still-unproven full constructor boundary')
            predicted=compare(plan['geometry'],{'reopened':native['reopened'],'edited':native['edited']})
            output.update(source_plan=plan,source_refusal=refusal,native_numeric_comparison=predicted)
        output.update(passed=True,dual_unit_construction=dual_proof,streams=streams,metadata=metadata,modes=modes,variant=variant,research_repack_sha256=sha256(data).hexdigest() if variant else None)
    finally:state['enabled']=False
    output['runtime_external_attempts']=state['attempts']
    output['sdk_modules']=sorted({module.__file__ for name,module in sys.modules.items() if (name=='convert' or name.startswith(('convert.','interchange.'))) and getattr(module,'__file__',None)})
    print(json.dumps(output,allow_nan=False));return 0


if __name__=='__main__':raise SystemExit(main())
