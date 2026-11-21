from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sys


def digest(value):
    return sha256(value.encode('utf-8')).hexdigest()


def normalized(document, freeze):
    bodies = tuple(replace(body, name='', provenance=None,
                           attributes=freeze({key:value for key,value in body.attributes.items()
                                              if key != 'solidworks.native_body'}))
                   for body in document.bodies)
    brep = document.brep
    if brep is not None:
        brep = replace(brep, bodies=tuple(replace(body, design_body_id='', provenance=None,
                          attributes=freeze({key:value for key,value in body.attributes.items()
                                             if key != 'solidworks.native_body'}))
                          for body in brep.bodies))
    metadata = freeze({key:value for key,value in document.metadata.items()
                       if key not in ('solidworks.native_body_names','solidworks_source_semantic_sha256')})
    return replace(document,bodies=bodies,brep=brep,metadata=metadata)


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--expected-label',required=True)
    parser.add_argument('--candidate',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    data = args.source.read_bytes()
    if sha256(data).hexdigest() != args.source_sha256:
        raise ValueError('locked disclosed input hash differs')
    sys.path.insert(0,str(args.sdk/'src'))
    from convert import open_document
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange.Core.Common import FreezeMapping
    from interchange.serialization.JsonCodec import DumpJson
    if not SldprtAdapter:
        raise RuntimeError('reader import failed')
    from codecs import lookup
    from importlib import import_module
    for name in ('ascii','utf-8','utf-8-sig','utf-16-le','utf-16-be','latin-1'):
        lookup(name)
    import_module('interchange.document.Models.DocumentProvenance')
    import_module('interchange.document.Behavior.DocumentIo')
    import_module('interchange.brep.Validation.BrepValidate')
    import_module('interchange.document.Validation.DocumentAssemblyValidate')
    import_module('interchange.document.Validation.DocumentFeatureValidate')
    import_module('interchange.document.Validation.DocumentReferenceValidate')
    import_module('interchange.document.Validation.AngleRevValidate')
    import_module('interchange.document.Validation.PlaneRevValidate')
    import_module('interchange.document.Validation.DistExtValidate')
    state = {'enabled':False,'opens':[]}

    def audit(event,arguments):
        if state['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.')) or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            state['opens'].append(repr(arguments[:2]))
            raise RuntimeError('additional file access during public body read')

    sys.addaudithook(audit)
    observations=[]
    settings=(('Default',{}),('Repeat',{}),('NoTess',{'include_tessellation':False}),
              ('History',{'include_brep':False}),('Lenient',{'strict':False}))
    for name,options in settings:
        state['enabled']=True
        try:
            document=open_document(data,source_format='solidworks.sldprt',**options)
        except Exception as error:
            observations.append({'mode':name,'passed':False,'error':{'class':type(error).__name__,'message':str(error)}})
            continue
        finally:
            state['enabled']=False
        document.assert_valid()
        expected_geometry=name!='History'
        bindings=tuple(body.design_body_id for body in document.brep.bodies) if document.brep is not None else ()
        proof=document.metadata.get('solidworks.native_body_names')
        labels=tuple(body.name for body in document.bodies)
        passed=len(document.bodies)==1 and (not expected_geometry or document.brep is not None and not document.brep.validate(frozenset(body.id for body in document.bodies)))
        if args.candidate and expected_geometry:
            passed=passed and labels==(args.expected_label,) and bindings==(document.bodies[0].id,) and proof is not None
        diagnostic=None
        if args.candidate and expected_geometry and proof is None:
            from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevolveBody import ReadRevolveBody
            from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BindBodyName import BindBodyName
            try:
                archive=SldprtArchive.from_bytes(data,args.source)
                graph=ReadRevolveBody(document,archive,0)
                BindBodyName(document,graph)
            except Exception as error:
                diagnostic={'class':type(error).__name__,'message':str(error)}
        observations.append({'mode':name,'passed':bool(passed),'labels':labels,'bindings':bindings,
                             'body_ids':tuple(body.id for body in document.bodies),
                             'body_names_metadata':dict(proof) if proof is not None else None,
                             'brep_present':document.brep is not None,
                             'full_document_sha256':digest(DumpJson(document,IndentSize=None)),
                             'unrelated_semantics_sha256':digest(DumpJson(normalized(document,FreezeMapping),IndentSize=None)),
                             'payloads':[(payload.source_stream,payload.kind,payload.sha256) for payload in document.brep_payloads],
                             'body_proof_failure':diagnostic})
    source_root=(args.sdk/'src').resolve()
    outside=[]
    research=[]
    for name,module in sys.modules.items():
        path=getattr(module,'__file__',None)
        if name.startswith(('convert','interchange')) and path and not Path(path).resolve().is_relative_to(source_root):outside.append(name)
        if path and '/re/tooling/' in str(path):research.append(name)
    immutable=sha256(args.source.read_bytes()).hexdigest()==args.source_sha256
    result={'schema':'kit.sw2026.named-body-reader-public-probe.v1','candidate':args.candidate,
            'source_sha256':args.source_sha256,'observations':observations,'file_access_attempts':state['opens'],
            'unexpected_sdk_module_origins':outside,'research_imports':research,'source_immutable':immutable,
            'passed':all(row['passed'] for row in observations) and not state['opens'] and not outside and not research and immutable}
    with args.output.open('x',encoding='utf-8',newline='\n') as output:
        output.write(dumps(result,indent=2,sort_keys=True)+'\n')
    raise SystemExit(0 if result['passed'] else 3)


if __name__=='__main__':
    main()
