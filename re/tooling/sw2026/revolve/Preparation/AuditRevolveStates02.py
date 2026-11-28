import argparse
import codecs
from hashlib import sha256
from importlib import import_module
import json
from math import isclose
from pathlib import Path
import sys


def require(condition,message):
    if not condition:
        raise ValueError(message)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sdk',type=Path,required=True)
    args=parser.parse_args()
    row=json.loads(sys.stdin.read())
    data=Path(row['path']).read_bytes()
    require(sha256(data).hexdigest()==row['sha256'],'exact disclosed state input differs')
    sys.path[:0]=[str(args.sdk/'src'),str(Path(__file__).resolve().parent)]
    from RevolveStreamAudit02 import stream_audit
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from interchange.document.Behavior.DocumentIo import ToJson,FromJson
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Features.FeatureAngleRev import AngularRevolve
    for encoding in ('ascii','utf-8','utf-8-sig','utf-16-le','utf-16-be','latin-1'):
        codecs.lookup(encoding)
    for name in ('interchange.brep.Validation.BrepValidate','interchange.document.Models.DocumentProvenance',
        'interchange.document.Validation.AngleRevValidate','interchange.document.Validation.DocumentAssemblyValidate',
        'interchange.document.Validation.DocumentFeatureValidate','interchange.document.Validation.DocumentReferenceValidate',
        'interchange.document.Validation.PlaneRevValidate','interchange.document.Validation.DistExtValidate'):
        import_module(name)
    state={'enabled':False,'attempts':[]}
    def audit(event,arguments):
        if state['enabled'] and (event=='open' or event.startswith(('subprocess.','socket.'))
            or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            state['attempts'].append(event)
            raise RuntimeError('strict native state reader attempted extra external access')
    sys.addaudithook(audit)
    state['enabled']=True
    result={'passed':False,'heldout_inputs_read':0,'native_processes':0}
    try:
        archive=SldprtArchive.from_bytes(data)
        link=ReadNativeLink(archive,0)
        owner,=ReadRevOwners(link)
        streams,metadata=stream_audit(archive,link)
        require(len(streams)==8 and (row['has_native_payload'] or all(value['qualified'] for value in metadata.values())),
            'generated fresh metadata or complete model stream boundary differs')
        expected=row['expected']
        require(isclose(owner.AngleValue.RadiansValue,expected['angle_rad'],rel_tol=1e-12,abs_tol=1e-14)
            and owner.IsReverse==expected['reverse'] and owner.AngleValue.NameValue=='D1',
            'typed angular driver or reversal differs from the frozen native state')
        require(ReadNativeName(owner.NodeValue)=='OrdinaryBossRevolve' and ReadNativeName(owner.ProfileValue)=='RevolveSketch',
            'typed feature or consumed sketch label differs')
        for endpoint,wanted in zip((owner.FrameValue.StartValue,owner.FrameValue.EndValue),expected['axis_points_m'],strict=True):
            require(all(isclose(actual*.001,planned,rel_tol=1e-12,abs_tol=1e-14)
                for actual,planned in zip((endpoint.x,endpoint.y,endpoint.z),wanted,strict=True)),
                'actual selected-axis endpoints differ from measured native selection')
        require(len(owner.ProfileGraph.AxisRules)==4 and {value.CodeValue for value in owner.ProfileGraph.AxisRules}=={4,5},
            'native contour relations differ')
        modes=(('no_geometry',{'include_brep':False,'include_tessellation':False}),
            ('brep_only',{'include_brep':True,'include_tessellation':False}),
            ('tessellation_only',{'include_brep':False,'include_tessellation':True}),
            ('both',{'include_brep':True,'include_tessellation':True}),('defaults',{}))
        results={}
        for name,options in modes:
            try:
                document=open_document(data,source_format='solidworks.sldprt',strict=True,**options)
            except ValueError as error:
                require(not row['has_native_payload'] and name in ('brep_only','both','defaults')
                    and str(error)=='SLDPRT contains no readable Parasolid payload',
                    'a strict source read failed beyond the preserved cacheless geometry boundary')
                results[name]={'error_class':type(error).__name__,'error_message':str(error)}
                continue
            document.assert_valid()
            encoded=ToJson(document)
            require(ToJson(FromJson(CadDocument,encoded))==encoded,'strict public native document JSON identity differs')
            feature,=(value for value in document.feature_timeline if value.name=='OrdinaryBossRevolve')
            sketch,=(value for value in document.sketches if value.name=='RevolveSketch')
            require(type(feature.definition) is AngularRevolve and len(sketch.entities)==5 and len(sketch.constraints)==4,
                'public native state lost its real revolve profile')
            parameter,=(value for value in document.parameters if value.id==feature.definition.AlongParameterId)
            require(parameter.name=='D1' and parameter.value.unit=='rad' and parameter.owner_id==feature.id
                and isclose(parameter.value.value,expected['angle_rad'],rel_tol=1e-12,abs_tol=1e-14),
                'public native D1 label units or angle differs')
            wants_brep=options.get('include_brep',True)
            if row['has_native_payload'] and wants_brep:
                require(document.brep is not None and len(document.brep.bodies)==1 and not document.brep.validate(frozenset(body.id for body in document.bodies)),
                    'native saved state lacks its complete validated B-rep body')
            results[name]={'document_sha256':sha256(encoded.encode()).hexdigest(),
                'brep_bodies':len(document.brep.bodies) if document.brep else 0,'payloads':len(document.brep_payloads),
                'feature_label':feature.name,'sketch_label':sketch.name,'parameter_label':parameter.name,
                'body_projection_labels':[body.name for body in document.bodies],
                'planar_relations':sorted(rule.kind for rule in sketch.constraints)}
        result.update(passed=True,streams=streams,metadata_attempts=metadata,
            all_metadata_qualified=all(value['qualified'] for value in metadata.values()),modes=results,
            angle_rad=owner.AngleValue.RadiansValue,reverse=owner.IsReverse,
            selected_axis_index=owner.AxisValue.IndexValue,selected_axis_mark=owner.AxisValue.MarkValue,
            contour_relations=len(owner.ProfileGraph.AxisRules),
            unexamined_streams=sorted(set(archive.streams)-set(streams)))
    finally:
        state['enabled']=False
    result['runtime_external_attempts']=state['attempts']
    result['sdk_modules']=sorted({module.__file__ for name,module in sys.modules.items()
        if (name=='convert' or name.startswith(('convert.','interchange.'))) and getattr(module,'__file__',None)})
    print(json.dumps(result,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
