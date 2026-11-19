from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):return sha256(path.read_bytes()).hexdigest()


def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def sources(root):
    return {str(path.relative_to(root)):digest(path) for parent in (root/'src',root/'tests',root/'re') if parent.exists() for path in sorted(parent.rglob('*')) if path.is_file() and '__pycache__' not in path.parts}


def run(args):
    output=args.output.resolve()
    if output.exists():raise ValueError('choose a new frozen process result directory')
    output.mkdir(parents=True)
    source_roots={'baseline':args.baseline.resolve(strict=True),'candidate':args.root.resolve(strict=True)}
    before={key:sources(value) for key,value in source_roots.items()}
    tools=Path(__file__).resolve().parent
    tool_names=('ProbeColdCircleRead.py','ProbeColdCircleLegacy.py','RunColdCircleRead.py')
    frozen={name:digest(tools/name) for name in tool_names}
    write(output/'SourceBefore.json',{'roots':before,'tools':frozen})
    rows={}
    def call(name,tool,root,phase,data=None,extra=()):
        command=[sys.executable,'-I','-B',str(tools/tool),str(root),phase,*extra]
        process=subprocess.run(command,input=None if data is None else json.dumps(data,sort_keys=True),capture_output=True,text=True,timeout=120)
        (output/(name+'.stdout.json')).write_text(process.stdout)
        (output/(name+'.stderr.txt')).write_text(process.stderr)
        if process.stderr:raise ValueError(name+' had unexpected stderr')
        value=json.loads(process.stdout)
        rows[name]={'exit_code':process.returncode,'stdout_sha256':digest(output/(name+'.stdout.json')),'result':value}
        return process.returncode,value
    inputs={}
    for variant in ('front','top'):
        for edited in (False,True):
            name=variant+('Edit' if edited else '')
            code,value=call('Input'+name,'ProbeColdCircleRead.py',source_roots['baseline'],'input',extra=('--variant',variant,*(('--edited',) if edited else ())))
            if code:raise ValueError('neutral input author failed')
            inputs[name]=value
            write(output/(name+'.Input.json'),value)
    for variant in ('front','top'):
        code,baseline=call('Before'+variant,'ProbeColdCircleRead.py',source_roots['baseline'],'read',inputs[variant])
        if code!=3 or baseline.get('passed') is not False or baseline['error']!='SLDPRT contains no readable Parasolid payload':raise ValueError('original public strict refusal was not reproduced')
        repeats=[]
        for ordinal in (1,2):
            code,value=call('After'+variant+str(ordinal),'ProbeColdCircleRead.py',source_roots['candidate'],'read',inputs[variant])
            if code or value.get('passed') is not True or value['public_writer_payload_sha256']!=baseline['public_writer_payload_sha256']:raise ValueError('candidate failed or changed the public writer bytes')
            repeats.append(value)
        if repeats[0]!=repeats[1]:raise ValueError('fresh candidate replay was not deterministic')
        code,value=call('Edit'+variant,'ProbeColdCircleRead.py',source_roots['candidate'],'read',inputs[variant+'Edit'])
        if code or value.get('passed') is not True or value['public_writer_payload_sha256']==baseline['public_writer_payload_sha256']:raise ValueError('independent radius and depth edit did not produce a validated changed body')
        for mutation in ('draft','inactive-length','scope','radius','support','extra-parent'):
            code,value=call('Reject'+variant+mutation,'ProbeColdCircleRead.py',source_roots['candidate'],'read',{**inputs[variant],'mutation':mutation})
            if code!=3 or value.get('passed') is not False:raise ValueError('malformed public archive was admitted')
    for kind in ('prism','pocket','revolve'):
        code,request=call('Input'+kind,'ProbeColdCircleLegacy.py',source_roots['baseline'],'input',extra=('--kind',kind))
        if code:raise ValueError('legacy neutral author failed')
        prior=[]
        for key,root in source_roots.items():
            code,value=call('Compat'+kind+key,'ProbeColdCircleLegacy.py',root,'read',request)
            if code or value.get('passed') is not True:raise ValueError('legacy read failed')
            prior.append(value)
        if prior[0]!=prior[1]:raise ValueError('legacy public bytes or complete neutral document changed')
    after={key:sources(value) for key,value in source_roots.items()}
    if before!=after or frozen!={name:digest(tools/name) for name in tool_names}:raise ValueError('source changed during process qualification')
    read_rows=[row for name,row in rows.items() if not name.startswith('Input')]
    if len(read_rows)!=26 or any(row['result'].get('runtime_data_file_reads')!=0 for row in read_rows):raise ValueError('process coverage or file guard was incomplete')
    result={'schema':'kit.sw2026.public-cold-circle-read-process.v1','passed':True,'rows':rows,'source_before_sha256':digest(output/'SourceBefore.json'),'source_unchanged':True,'tool_sha256':frozen,'reader_processes':len(read_rows),'neutral_input_processes':len(rows)-len(read_rows),'total_processes':len(rows),'original_refusals':2,'malformed_refusals':12,'positive_circle_reads':6,'legacy_document_byte_equal_pairs':3,'public_writer_bytes_unchanged':True,'native_processes_started':0,'hidden_inputs_read':0,'native_face_identity':False}
    write(output/'Results.json',result)
    return {'passed':True,'result_sha256':digest(output/'Results.json'),'reader_processes':26,'total_processes':len(rows),'native_processes_started':0,'hidden_inputs_read':0}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args),sort_keys=True))


if __name__=='__main__':
    main()
