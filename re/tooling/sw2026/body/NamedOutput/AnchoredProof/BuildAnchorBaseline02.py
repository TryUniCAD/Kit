from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps, load
from pathlib import Path
import sys


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    args = parser.parse_args()
    case = load(sys.stdin)
    sys.path[:0] = [str(args.sdk/'src'), str(Path(__file__).resolve().parent/'Harness01')]
    from MakeAnchoredRequest import request
    from MakeAnchorReference import make_reference
    from CheckAnchoredGraph import check_graph
    from interchange.serialization.JsonCodec import DumpJson
    for name in ('ascii', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1'):
        lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance', 'interchange.document.Behavior.DocumentIo',
                 'interchange.brep.Validation.BrepValidate', 'interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate', 'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    document, settings, dimensions = request(case)
    document = replace(document, bodies=(replace(document.bodies[0],name=document.feature_timeline[0].name),))
    before = sha256(DumpJson(document, IndentSize=None).encode()).hexdigest()
    state = {'enabled':False,'attempts':[]}

    def audit(event, arguments):
        if state['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.'))
            or event in ('os.system', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen')):
            state['attempts'].append({'event':event,'arguments':repr(arguments[:2])})
            raise RuntimeError('frozen baseline attempted external runtime access')

    sys.addaudithook(audit)
    state['enabled'] = True
    try:
        candidate = make_reference(document, settings, dimensions, case['anchor_kind'])
        graph = check_graph(candidate,case['anchor_kind'],document)
    finally:
        state['enabled'] = False
    after = sha256(DumpJson(document, IndentSize=None).encode()).hexdigest()
    if before != after or state['attempts']:
        raise ValueError('baseline source or runtime guard failed')
    forbidden = [name for name in sys.modules if name.rsplit('.',1)[-1] in
        ('AnchorPartInput','CheckAnchorSpec','MakeAnchorBase','MakeAnchorNamed')]
    if forbidden:
        raise ValueError('baseline imported the new SDK constructor')
    result = {'schema':'kit.sw2026.anchored-base-frozen-reference.v1','passed':True,
        'case':case['name'],'artifact_sha256':sha256(candidate.BytesValue).hexdigest(),
        'blob':b64encode(candidate.BytesValue).decode('ascii'),'anchor_graph':graph,
        'streams':{name:{'sha256':sha256(value).hexdigest(),'bytes':len(value)} for name,value in candidate.StreamsValue.items()},
        'source_document_unchanged':True,'runtime_access_attempts':state['attempts'],
        'new_constructor_imports':forbidden,'heldout_inputs_read':0}
    print(dumps(result,ensure_ascii=True,sort_keys=True))


if __name__ == '__main__':
    main()
