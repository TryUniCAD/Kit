import argparse
from hashlib import sha256
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--code',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
rows=[]
for folder in ('src','Cli'):
    for path in sorted((a.code/folder).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':
            rows.append({'path':str(path.relative_to(a.code)),'sha256':sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
with a.output.open('x') as f:
    json.dump({'schema':'kit.sw2026.explicit-public-flow-source.v1','files':rows},f,indent=2)
print(sha256(a.output.read_bytes()).hexdigest())
