import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from RunSourceProof04 import verify,require,ordinary


def digest(path):return sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.root.resolve(strict=True);output=args.output.resolve();require(not output.exists(),'fresh proof output must be unused')
    verify(root/'Source02.json',root/'Code02');verify(root/'BaselineSource02.json',root/'Baseline02');verify(root/'FreshTools01.json',root/'FreshTools01')
    inputs=json.loads((root/'Inputs02.json').read_bytes());output.mkdir(parents=True)
    report={'schema':'kit.sw2026.ordinary-revolve-fresh-read-regression.v1','passed':False,'source_manifest_sha256':digest(root/'Source02.json'),'base_manifest_sha256':digest(root/'BaselineSource02.json'),'tools_manifest_sha256':digest(root/'FreshTools01.json'),'inputs_sha256':digest(root/'Inputs02.json'),'runner_sha256':digest(Path(__file__)),'workers':[],'cases':[],'heldout_inputs_read':0,'native_processes':0}
    def save():(output/'Replay.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    try:
        for index,row in enumerate(inputs['generated_requests']):
            values=[]
            for sdk in ['Baseline02','Code02']:
                name=sdk+str(index);p=subprocess.run([sys.executable,'-I','-B',str(root/'FreshTools01/AuditFreshRevolve01.py'),'--sdk',str(root/sdk)],input=json.dumps(row),capture_output=True,text=True,timeout=90)
                (output/(name+'.stdout')).write_text(p.stdout);(output/(name+'.stderr')).write_text(p.stderr);report['workers'].append({'name':name,'exit_code':p.returncode,'stdout_sha256':sha256(p.stdout.encode()).hexdigest(),'stderr_sha256':sha256(p.stderr.encode()).hexdigest()});save();require(p.returncode==0,'fresh worker failed '+name+' '+p.stderr);value=json.loads(p.stdout);require(value['passed'] and not value['runtime_external_attempts'],'fresh worker did not pass its boundary')
                for path in value['sdk_modules']:require(Path(path).is_relative_to(root/sdk/'src'),'fresh SDK source escaped the freeze')
                value.pop('sdk_modules');values.append(value)
            before,after=values
            for mode in before['modes']:
                require(ordinary(before['modes'][mode]['source_document'])==ordinary(after['modes'][mode]['source_document']),'cache-free source body geometry or unrelated semantics changed')
            for value in after['modes'].values():value.pop('source_document')
            report['cases'].append(after);save()
        report['passed']=True
    except Exception as error:report['error']=repr(error)
    finally:report['fresh_processes']=len(report['workers']);report['paired_modes']=sum(len(case['modes']) for case in report['cases']);save()
    print(json.dumps({'passed':report['passed'],'processes':report['fresh_processes'],'report_sha256':digest(output/'Replay.json')}));return 0 if report['passed'] else 3


if __name__=='__main__':raise SystemExit(main())
