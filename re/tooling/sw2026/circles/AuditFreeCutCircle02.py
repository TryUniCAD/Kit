from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from json import dumps,loads
from math import isclose
from pathlib import Path
import sys


def require(value,message):
    if not value:
        raise ValueError(message)


def main():
    parser=ArgumentParser()
    parser.add_argument('--sdk',type=Path,required=True)
    args=parser.parse_args()
    request=loads(sys.stdin.read())
    row=request['input']
    source=Path(row['path'])
    data=source.read_bytes()
    require(sha256(data).hexdigest()==row['sha256'],'the exact disclosed source hash differs')
    sys.path.insert(0,str(args.sdk/'src'))
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import DecodeNativeModel
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
    from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import ReadLocalCirc
    from convert.adapters.solidworks.Core.TypedResolved.Circles.BindLocalCirc import BindLocalCirc
    from convert.adapters.solidworks.Core.TypedResolved.Circles.CircleSketch import CircleSketch
    from convert.adapters.solidworks.Core.TypedResolved.ReadCircleShape import ReadCircleShape
    from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    for name in ('ascii','utf-8','utf-16-le','utf-16-be','latin-1'):
        lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance','interchange.document.Behavior.DocumentIo',
                 'interchange.brep.Validation.BrepValidate','interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate','interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    state={'enabled':False,'attempts':[]}

    def audit(event,arguments):
        if state['enabled'] and (event=='open' or event.startswith(('subprocess.','socket.'))
            or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            state['attempts'].append({'event':event,'arguments':repr(arguments[:2])})
            raise RuntimeError('circle ownership audit attempted additional runtime access')

    sys.addaudithook(audit)
    state['enabled']=True
    try:
        archive=SldprtArchive.from_bytes(data)
        link=ReadNativeLink(archive,0)
        nodes=IndexFeatures(link)
        profiles=[node for node in nodes.values() if node.ClassValue.NameValue=='moProfileFeature_c'
                  and ReadNativeName(node)==row['cut_profile']]
        require(len(profiles)==1,'disclosed cut must have exactly one actual named profile root')
        profile,=profiles
        cuts=[node for node in nodes.values() if node.ClassValue.NameValue=='moICE_c'
              and node.FieldsValue['f810']==1 and profile in ReadParents(node)]
        require(len(cuts)==1,'the circle profile is not owned by one actual native cut')
        sketch=profile.FieldsValue['pd_f80']
        require(sketch.ClassValue.NameValue=='sgSketch','actual circle profile does not own its native sketch')
        fields=sketch.FieldsValue
        shape=ReadCircleShape(sketch)
        require(shape is not None,'the actual arc and point indices do not form one closed local circle')
        require(IsLineState(fields['dims']) and fields['f5d8'].FieldsValue=={'n':0,'items':[]},
                'the disclosed circle is not the exact unconstrained empty-region profile')
        default=ReadLocalCirc(sketch,link)
        result=ReadLocalCirc(sketch,link,AllowFree=True)
        require(default is None and result is not None,'the local circle free-state gate differs')
        circle,parameter=result
        require(parameter is None and circle.DriverName is None and circle.ModeValue is None,
                'an unconstrained geometric radius was turned into a driving parameter')
        require(circle.CenterMark==2 and circle.ArcMark==1,'the disclosed actual circle marks differ')
        legacy=DecodeNativeModel(archive.require('swXmlContents/KeyWords'),archive.require('Contents/Config-0-ResolvedFeatures'),
                                 resolved_stream='Contents/Config-0-ResolvedFeatures')
        old,=[value for value in legacy.sketches if value.object_id==profile.FieldsValue['f08']]
        require(len(old.constraints)==1 and old.constraints[0].kind=='radius'
                and old.constraints[0].parameter is None,'the legacy inferred radius lead differs')
        bound=BindLocalCirc(old,profile,link,AllowFree=True)
        require(bound is not None and bound.TypedCircle is not None and not bound.dimensions,
                'the existing local typed owner binder failed')
        projected=CircleSketch(bound,set())
        require(not projected.constraints and not projected.parameter_ids and len(projected.entities)==2
                and len(projected.closed_profile_entity_ids)==1,'typed free circle invented relations or lost its actual entities')
        expected=request['native_observation']
        for sample in expected['samples']:
            for actual,wanted in zip(circle.CenterValue,sample['center_m'],strict=True):
                require(isclose(actual*0.001,wanted,rel_tol=1e-12,abs_tol=1e-14),'native and typed circle centre differ')
            require(isclose(circle.RadiusValue*0.001,sample['radius_m'],rel_tol=1e-12,abs_tol=1e-14),
                    'native and typed geometric radius differ')
            require(sample['native_arc_id'][1]==circle.ArcMark and sample['native_center_id'][1]==circle.CenterMark,
                    'typed marks disagree with native actual entity creation identities')
        header=ReadHeaderGraph(archive.require('Contents/Config-0-ModelHeader'),19000)
        encoded,config=WriteConfigMut(link.ConfigValue.RootValue,19000,header)
        context=MakeLinkContext(config,ReadCmgrMut(archive.require('Contents/CMgr'),19000))
        resolved,unused=WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,19000,config.MapValue,context)
        require(encoded==archive.require('Contents/Config-0') and resolved==archive.require('Contents/Config-0-ResolvedFeatures'),
                'full typed archive streams do not preserve the complete native bytes')
        require(all(report['completed'] and not report['missing_schemas'] and not report['provisional_schemas']
                    for report in (link.ConfigValue.ReportValue,link.ResolvedValue.ReportValue)),
                'circle evidence reached incomplete or provisional native grammar')
        public=None
        if row['family']=='ordinary_blind_cut':
            document=open_document(data,source_format='solidworks.sldprt',include_brep=False,include_tessellation=False,strict=True)
            selected,=[value for value in document.sketches if value.name==row['cut_profile']]
            require(not selected.constraints and not selected.parameter_ids and len(selected.entities)==2,
                    'the current ordinary blind public path still exposes invented radius semantics')
            public={'circle_entity_count':len(selected.entities),'constraint_count':0,'parameter_count':0,'passed':True}
    finally:
        state['enabled']=False
    source_root=(args.sdk/'src').resolve()
    outside=[name for name,module in tuple(sys.modules.items()) if name.startswith(('convert','interchange','readers'))
             and getattr(module,'__file__',None) and not Path(module.__file__).resolve().is_relative_to(source_root)]
    research=[name for name,module in tuple(sys.modules.items()) if getattr(module,'__file__',None)
              and '/re/tooling/' in str(module.__file__)]
    require(not state['attempts'] and not outside and not research and sha256(source.read_bytes()).hexdigest()==row['sha256'],
            'source immutable module origin or runtime access evidence failed')
    result={'schema':'kit.sw2026.disclosed-free-cut-circle-audit.v1','passed':True,'name':row['name'],'state':row['state'],
        'family':row['family'],'source_sha256':row['sha256'],'profile_id':profile.FieldsValue['f08'],
        'circle_center_mm':circle.CenterValue,'geometric_radius_mm':circle.RadiusValue,'arc_mark':circle.ArcMark,
        'center_mark':circle.CenterMark,'region_fields':fields['f5d8'].FieldsValue,'all_solver_arrays_empty':True,
        'local_free_circle_passed':True,'default_nonfree_gate_rejected':True,'legacy_constraint_count':len(old.constraints),
        'legacy_radius_has_parameter':False,'typed_circle_constraints':0,'typed_circle_parameter_ids':0,
        'native_reopen_geometry_samples':len(expected['samples']),'native_observer_sha256':expected['native_observer_sha256'],
        'config_and_resolved_roundtrip_exact':True,'public_blind_circle':public,'whole_through_all_operation_audited':False,
        'runtime_access_attempts':state['attempts'],'unexpected_sdk_origins':outside,'research_runtime_imports':research,
        'source_immutable':True,'sdk_source_changed':False,'heldout_inputs_read':0,'native_processes_started':0}
    print(dumps(result,sort_keys=True,ensure_ascii=True))


if __name__=='__main__':
    main()
