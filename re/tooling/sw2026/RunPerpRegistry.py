from codecs import lookup
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import sys


ROOT=Path(sys.argv[1]).resolve(strict=True)
sys.path[:0]=[str(ROOT/'src'),str(ROOT),str(ROOT/'re/tooling/sw2026')]

from convert import write_document
from convert.api.ApiContext import GetRegistry
from interchange.document.Models.DocumentProvenance import HasProvenance
from interchange.serialization.Deserialize import FromData
from SdkNativeRoundTrips import roundtrips
from convert.adapters.solidworks.Container.Container import SldprtArchive


def require(value,message):
    if not value:raise ValueError(message)


def main():
    request=json.load(sys.stdin)
    document=FromData(request['document']);document.assert_valid()
    directory=Path(request['output']);directory.mkdir(parents=True,exist_ok=False)
    target=directory/(document.metadata['name']+'.SLDASM')
    native=request['native_parent'];epoch=request['saved_at']
    module=import_module('convert.adapters.solidworks.Core.AssemblyWriting.EmitAsmMut')
    module.ReadTime=lambda:epoch
    adapter=GetRegistry().writer('solidworks.sldasm')
    admitted=adapter.supports(document,target)
    codecs=tuple(lookup(name) for name in ('utf-8','utf-16-le','latin-1','utf-8-sig'))
    audit={'active':False,'runtime_reads':[],'processes':[]}
    access_mode_mask=getattr(os,'O_ACCMODE',os.O_WRONLY|os.O_RDWR)
    def observe(event,args):
        if not audit['active']:return
        if event=='open':
            path,mode,flags=args
            if isinstance(path,(str,bytes,os.PathLike)) and Path(os.fsdecode(path)).is_dir():return
            if isinstance(mode,str) and 'r' in mode or isinstance(flags,int) and flags&access_mode_mask!=os.O_WRONLY:
                audit['runtime_reads'].append(str(path));raise PermissionError('registry construction read a runtime file')
        if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn','os.fork'):
            audit['processes'].append(event);raise PermissionError('registry construction invoked a runtime')
    sys.addaudithook(observe)
    error,result=None,None
    audit['active']=True
    try:
        result=write_document(document,target,destination_format=request.get('format_id'),overwrite=request.get('overwrite',False),
                              allow_carrier=request.get('allow_unqualified',False),values={'native_destination':native})
    except Exception as caught:error={'type':type(caught).__name__,'message':str(caught)}
    finally:audit['active']=False
    require(not audit['runtime_reads'] and not audit['processes'],'the registry crossed its source-only boundary: '+repr(audit)+'; '+repr(error))
    expected=request.get('expected_reject',False)
    if request.get('expected_policy_reject',False):
        require(admitted and error is not None and result is None and not list(directory.iterdir()),'strict policy published unqualified native output')
        return {'passed':True,'policy_rejected':True,'admitted':True,'error':error,'writer_output_count':0,
                'runtime_input_file_reads':0,'native_processes_started':0,'worker_pid':os.getpid()}
    if expected:
        require(not admitted and error is not None and result is None and not list(directory.iterdir()),'unsupported intent did not reject before selection/output')
        return {'passed':True,'rejected':True,'admitted':admitted,'error':error,'writer_output_count':0,'runtime_input_file_reads':0,
                'native_processes_started':0,'worker_pid':os.getpid()}
    require(admitted and error is None and result is not None,'normal registry did not publish: '+repr(error))
    child_name=document.assembly.documents[0].document.metadata['name']+'.SLDPRT'
    require({p.name for p in directory.iterdir()}=={target.name,child_name},'the registry published an incomplete or extra bundle')
    artifacts={};count=0
    for role,path in (('parent',target),('child',directory/child_name)):
        blob=path.read_bytes();archive=SldprtArchive.from_bytes(blob)
        _,_,_,_,proof=roundtrips(archive,role=='parent')
        count+=len(proof)
        artifacts[role]={'sha256':sha256(blob).hexdigest(),'bytes':len(blob),'stream_round_trips':proof,
                         'logical_streams':{name:{'sha256':sha256(data).hexdigest(),'bytes':len(data)} for name,data in archive.streams.items()}}
    require(result.vendor_loadable is False and result.application_usable is False,'the unmeasured public recipe claimed native qualification')
    require(not result.carrier_capabilities and not result.dropped and not result.requirements,'the research opt-in introduced carrier or unrepresented data')
    return {'passed':True,'admitted':True,'registry_format':adapter.info.format_id,'artifacts':artifacts,'round_trips':count,
            'runtime_input_file_reads':0,'native_processes_started':0,'writer_output_count':2,'worker_pid':os.getpid(),
            'vendor_loadable':result.vendor_loadable,'application_usable':result.application_usable,'result_metadata':dict(result.metadata)}


print(json.dumps(main(),sort_keys=True,allow_nan=False))
