import argparse
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

p=argparse.ArgumentParser()
p.add_argument('--code',type=Path,required=True)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--sha256',required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
sys.path.insert(0,str(a.code/'src'))
from convert.api import open_document,write_document
from convert.adapters import AdapterNotFoundError
from interchange.Core.Common import FreezeMapping
raw=a.source.read_bytes()
assert sha256(raw).hexdigest()==a.sha256
document=open_document(raw,source_format='solidworks.slddrw',strict=True)
attrs=deepcopy(dict(document.source.attributes))
attrs['solidworks.blank.intent']['DrawingValue']['sheets'][0]['notes']=[{'text':'outside canonical blank scope'}]
document=replace(document,source=replace(document.source,attributes=FreezeMapping(attrs)))
target=a.output.parent/'NoNoteOutput'/'RejectedNote.SLDDRW'
try:
    write_document(document,target,destination_format='solidworks.slddrw')
except AdapterNotFoundError:
    assert not target.exists()
else:
    raise AssertionError('nonempty note metadata unexpectedly admitted')
assert sha256(a.source.read_bytes()).hexdigest()==a.sha256
report={'schema':'kit.sw2026.canonical-blank-note-refusal.v1','passed':True,'input_sha256':a.sha256,'nonempty_note_witness_rejected':True,'output_absent':True,'source_immutable':True,'native_calls':0,'private_inputs':0,'fixture_scope':'structural source metadata negative; no native note validity claimed'}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':True,'report_sha256':sha256(a.output.read_bytes()).hexdigest()}))
