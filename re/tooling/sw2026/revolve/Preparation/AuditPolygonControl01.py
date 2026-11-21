import argparse
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    sys.path[:0] = [str(args.sdk / 'src'), str(Path(__file__).resolve().parent)]
    from MakeRevolveRequest01 import make_request
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from interchange.Enums.EnumFeatures import FeatureKind
    from interchange.Enums.EnumValues import ValueKind
    from interchange.Features.FeatureExtrude import ExtrudeFeature, ExtrudeEnd
    from interchange.Records.RecordParameter import ParameterValue
    for encoding in ('ascii', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1'):
        codecs.lookup(encoding)
    for name in ('interchange.document.Behavior.DocumentIo', 'interchange.document.Models.DocumentProvenance',
        'interchange.document.Validation.DocumentAssemblyValidate',
        'interchange.document.Validation.DocumentFeatureValidate',
        'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    state = {'enabled': False, 'attempts': []}
    def audit(event, arguments):
        if state['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.'))
            or event in ('os.system', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen')):
            state['attempts'].append(event)
            raise RuntimeError('baseline polygon constructor attempted external access')
    sys.addaudithook(audit)
    state['enabled'] = True
    try:
        document, _ = make_request(row['spec'])
        sketch = replace(document.sketches[0], entities=document.sketches[0].entities[:4], constraints=())
        value = ParameterValue(row['depth_mm'], ValueKind.KLength, 'mm')
        parameter = replace(document.parameters[0], value=value)
        feature = replace(document.feature_timeline[0], kind=FeatureKind.KExtrusion,
            definition=ExtrudeFeature(value, ExtrudeEnd.KBlind), selection_ids=())
        document = replace(document, sketches=(sketch,), parameters=(parameter,), feature_timeline=(feature,), selections=())
        plan = ProjectPlain(document)
        candidate = MakeBlindPart(document, MakePartRecipe(plan, row['spec']['created_at']))
        public = open_document(candidate.BytesValue, source_format='solidworks.sldprt', strict=True,
            include_brep=False, include_tessellation=False)
        public.assert_valid()
        result = {'passed': True, 'sha256': sha256(candidate.BytesValue).hexdigest(),
            'bytes':len(candidate.BytesValue), 'lines':len(public.sketches[0].entities),
            'streams':{name:sha256(data).hexdigest() for name,data in candidate.StreamsValue.items()}}
    finally:
        state['enabled'] = False
    result['runtime_external_attempts'] = state['attempts']
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
