import argparse
import codecs
from hashlib import sha256
from importlib import import_module
import json
from math import isclose,tau,radians
from pathlib import Path
import sys


def require(value,message):
    if not value:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sdk',type=Path,required=True);args=parser.parse_args();row=json.loads(sys.stdin.read())
    sys.path[:0]=[str(args.sdk/'src'),str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import MakeRevPart
    from convert.adapters.solidworks.Core.Adapter import SemanticShaTwo
    from MakeRevolveRequest01 import make_request
    from PredictSourceRevolve01 import predict
    from interchange.document.Behavior.DocumentIo import ToJson,FromJson
    from interchange.document.Models.DocumentModel import CadDocument
    for encoding in ('ascii','utf-8','utf-8-sig','utf-16-le','utf-16-be','latin-1'):codecs.lookup(encoding)
    for name in ('interchange.brep.Validation.BrepValidate','interchange.document.Models.DocumentProvenance','interchange.document.Validation.AngleRevValidate','interchange.document.Validation.DocumentAssemblyValidate','interchange.document.Validation.DocumentFeatureValidate','interchange.document.Validation.DocumentReferenceValidate','interchange.document.Validation.PlaneRevValidate','interchange.document.Validation.DistExtValidate'):import_module(name)
    state={'enabled':False,'attempts':[]}
    def audit(event,arguments):
        if state['enabled'] and (event=='open' or event.startswith(('subprocess.','socket.')) or event in ('os.system','os.fork','os.posix_spawn','ctypes.dlopen')):
            state['attempts'].append(event);raise RuntimeError('fresh revolve read attempted external runtime access')
    sys.addaudithook(audit);state['enabled']=True
    result={'passed':False,'heldout_inputs_read':0,'native_processes':0}
    try:
        doc,settings=make_request(row['spec']);candidate=MakeRevPart(doc,settings)
        require(sha256(candidate.BytesValue).hexdigest()==row['sha256'],'fresh cache-free native-qualified bytes changed')
        require(not any('partition' in name.casefold() or 'delta' in name.casefold() for name in candidate.StreamsValue),'fresh candidate unexpectedly transmits geometry')
        spec=row['spec'];axis=spec['axis_x_mm'];inner,outer=spec['radial_mm'];low,high=spec['axial_mm']
        wanted=predict({'positive_angle_rad':radians(spec['angle_deg']),'reverse':spec['reverse'],'contour_points_mm':[[axis+inner,low],[axis+outer,low],[axis+outer,high],[axis+inner,high]],'axis_start_mm':[axis,spec['axis_span_mm'][0]]})
        modes={}
        for name,options in [('no_geometry',{'include_brep':False,'include_tessellation':False}),('brep_only',{'include_brep':True,'include_tessellation':False}),('tessellation_only',{'include_brep':False,'include_tessellation':True}),('both',{'include_brep':True,'include_tessellation':True}),('defaults',{})]:
            value=open_document(candidate.BytesValue,source_format='solidworks.sldprt',strict=True,**options);value.assert_valid();encoded=ToJson(value)
            require(ToJson(FromJson(CadDocument,encoded))==encoded,'fresh strict neutral JSON identity differs')
            require(value.metadata['solidworks_source_semantic_sha256']==SemanticShaTwo(value),'fresh source digest does not match the actual final document')
            require(len(value.bodies)==1 and not value.brep_payloads,'fresh read manufactured a native cache payload')
            topology=value.bodies[0].topology
            if options.get('include_brep',True):
                require(value.brep is not None and len(value.brep.bodies)==1 and not value.brep.validate(frozenset(body.id for body in value.bodies)),'fresh strict reader did not create complete validated B-rep')
                require(len(value.brep.faces)==(4 if candidate.PlanValue.AngleValue==tau else 6),'fresh default topology changed')
                require(topology is not None and topology.volume is not None and topology.surface_area is not None,'fresh default reader lacks complete analytic metrics')
                require(isclose(topology.volume*1e-9,wanted['volume_m3'],rel_tol=1e-12,abs_tol=1e-16) and isclose(topology.surface_area*1e-6,wanted['area_m2'],rel_tol=1e-12,abs_tol=1e-16),'fresh strict geometry differs from independent sector mathematics')
            else:require(value.brep is None,'tessellation policy changed in a no-B-rep mode')
            modes[name]={'source_document':json.loads(encoded),'body_name':value.bodies[0].name,'final_feature_id':value.bodies[0].final_feature_id,'brep_bodies':len(value.brep.bodies) if value.brep else 0,'payloads':len(value.brep_payloads),'faces':len(value.brep.faces) if value.brep else 0,'volume_mm3':topology.volume if topology else None,'area_mm2':topology.surface_area if topology else None,'document_sha256':sha256(encoded.encode()).hexdigest()}
        result.update(passed=True,sha256=sha256(candidate.BytesValue).hexdigest(),modes=modes,expected=wanted)
    finally:state['enabled']=False
    result['runtime_external_attempts']=state['attempts'];result['sdk_modules']=sorted({module.__file__ for name,module in sys.modules.items() if (name=='convert' or name.startswith(('convert.','interchange.'))) and getattr(module,'__file__',None)})
    print(json.dumps(result,allow_nan=False));return 0


if __name__=='__main__':raise SystemExit(main())
