import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.root.resolve(strict=True);output=args.output.resolve()
    if output.exists():raise ValueError('combined proof output must be unused')
    output.mkdir(parents=True);records=[]
    for script,directory in [('RunSourceProof04.py','Source'),('RunFreshProof01.py','Fresh')]:
        completed=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve().parent/script),'--root',str(root),'--output',str(output/directory)],capture_output=True,text=True,timeout=900)
        (output/(directory+'.stdout')).write_text(completed.stdout);(output/(directory+'.stderr')).write_text(completed.stderr)
        path=output/directory/'Replay.json';report=json.loads(path.read_bytes()) if path.is_file() else {'passed':False}
        records.append({'script':script,'exit_code':completed.returncode,'report_sha256':sha256(path.read_bytes()).hexdigest() if path.is_file() else None,'passed':bool(report['passed']),'fresh_processes':report.get('fresh_processes',0)})
        if completed.returncode:break
    result={'schema':'kit.sw2026.ordinary-revolve-source-combined-replay.v1','passed':len(records)==2 and all(row['exit_code']==0 and row['passed'] for row in records),'reports':records,'fresh_processes':sum(row['fresh_processes'] for row in records),'heldout_inputs_read':0,'native_processes':0}
    (output/'Combined.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0 if result['passed'] else 3


if __name__=='__main__':raise SystemExit(main())
