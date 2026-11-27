from dataclasses import replace
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

from convert import open_document
from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from tests.Convert.Integration.Fusion.DualSide.Admission.ChangeDualAux import ChangeDualAux
from tests.Convert.Integration.Fusion.DualSide.Admission.ChangeDualParam import ChangeDualParam

root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();output.mkdir(exist_ok=False)
source=root/'re/Fusion/TwoSidedDraft20261127/Native/baseline.f3d';data=source.read_bytes();model=ReadDocument(data)
paths=[]
for name in ('role','unit','expression','reciprocal','owner','allocation','operation'):
    path=output/('parameter_'+name+'.f3d');path.write_bytes(EmitParsed(ChangeDualParam(model,name)));paths.append(path)
for name in ('appearance','material','visual'):
    changed=ChangeDualAux(model,name);container=replace(ReadContainer(data),Streams=tuple(EmitDocSegment(segment) for segment in changed.Segments))
    path=output/('auxiliary_'+name+'.f3d');path.write_bytes(EmitContainer(container));paths.append(path)
for directory in ('DualDraft/MassInitial/Counterexamples','DualAdmissionSnapshots/Counterexamples','DualAdmissionTags/Proof/Counterexamples'):
    paths.extend(sorted((root/'re/Fusion/DecodedPromotion20261127'/directory).glob('*.f3d')))
rows=[]
for path in paths:
    raw=path.read_bytes();row=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    try:
        ReadDocument(raw);row['typed_document']='parsed'
    except ValueError as error:row.update(typed_document='refused',codec_reason=str(error))
    try:
        open_document(BytesIO(raw),source_format='fusion.f3d',strict=True);row['public_outcome']='unexpected_accept'
    except ValueError as error:row.update(public_outcome='refused',reason=str(error))
    rows.append(row)
summary=dict(cases=len(rows),refused=sum(row['public_outcome']=='refused' for row in rows),models=False,native_calls=0)
(output/'Receipt.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(data).hexdigest(),summary=summary,rows=rows),indent=2)+'\n')
print(json.dumps(summary));assert summary['cases']==summary['refused']==42
