from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from io import BytesIO
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 're/automation')]

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from EncoderRoundTrip.Artifacts import canonical_json, read_record, write_artifact
from EncoderRoundTrip.Source import encode_writer_input
from interchange.document.Models.DocumentModel import CadDocument

SCHEMA = 'kit.sw2026.document-construction-plane-visibility.v1'
DEFINITION = 'Contents/Definition'
PLANE_VISIBILITY_BIT = 17


def adopt(request):
    value = read_record(request)
    if set(value) != {'schema', 'document', 'show_construction_planes'} or value['schema'] != SCHEMA:
        raise ValueError('expected one document-global construction-plane setting')
    flag = value['show_construction_planes']
    if type(flag) is not bool:
        raise TypeError('construction-plane visibility must be a JSON boolean')
    document = CadDocument.from_dict(value['document'])
    if encode_writer_input(document) != canonical_json(value['document']):
        raise ValueError('expected a complete authored neutral part')
    return document, flag


def compose(document, flag, locator, epoch):
    if type(flag) is not bool:
        raise TypeError('construction-plane visibility must be a boolean')
    plan = PlanPartWrite(document)
    recipe = MakePartRecipe(plan, epoch)
    if recipe.DefinitionValue.DisplayBits:
        raise ValueError('plane probe requires the plain generated Definition')
    definition = replace(recipe.DefinitionValue, DisplayBits=(PLANE_VISIBILITY_BIT,) if flag else ())
    return RunPartPrep(document, BytesIO(), plan, replace(recipe, DefinitionValue=definition),
                       WriteOptions(values={'final_destination': str(locator)}))


def checked_generation(document, flag, locator, epoch):
    for encoding in ('ascii', 'latin-1', 'cp1252', 'utf-8', 'utf-16-le', 'utf-16-be'):
        lookup(encoding)
    active = True
    attempts = []

    def no_external_input(event, _):
        if active and (event in ('open', 'os.listdir', 'os.scandir', 'os.exec', 'os.fork',
                                 'os.posix_spawn', 'os.startfile', 'os.system') or
                       event.startswith(('subprocess.', 'socket.', 'ctypes.', 'winreg.'))):
            attempts.append(event)
            raise RuntimeError(f'unexpected external access during manufacture: {event}')

    sys.addaudithook(no_external_input)
    try:
        candidate = compose(document, flag, locator, epoch)
    finally:
        active = False
    if attempts:
        raise ValueError('generation requested external input')
    return candidate


def emit(request_path, output, locator, epoch):
    if not locator.is_absolute() or locator.suffix.casefold() != '.sldprt':
        raise ValueError('plane candidate requires its absolute native locator')
    if output.exists():
        raise ValueError('plane candidate requires a fresh output directory')
    request = request_path.read_bytes()
    document, visible = adopt(request)
    candidate = checked_generation(document, visible, locator, epoch)
    streams = SldprtArchive.from_bytes(candidate.BytesValue, str(locator)).Streams
    model = ReadModelDef(streams[DEFINITION], 19000).GraphValue.DocumentValue.FieldsValue
    expected_word = (1 << PLANE_VISIBILITY_BIT) if visible else 0
    if (model['fad8_0'], model['fad8_1']) != (expected_word, 0):
        raise ValueError('authored plane state does not match the typed generated Definition')
    output.mkdir(exist_ok=False)
    retained = write_artifact(output, 'Request.json', request)
    archive = write_artifact(output, locator.name, candidate.BytesValue)
    manifest = {
        'schema': SCHEMA,
        'stage': 'awaiting_native_measurement',
        'document_name': candidate.PlanValue.NameValue,
        'show_construction_planes': visible,
        'definition_words': [model['fad8_0'], model['fad8_1']],
        'native_locator': str(locator),
        'written_at': epoch,
        'external_manufacture_access_attempts': 0,
        'request': retained,
        'archive': archive,
    }
    return write_artifact(output, 'Candidate.json', canonical_json(manifest))


if __name__ == '__main__':
    parser = ArgumentParser(description='Compose a plain blind boss from typed authored input plus a document construction-plane preference')
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-locator', type=PureWindowsPath, required=True)
    parser.add_argument('--written-at', type=int, required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write(canonical_json(emit(args.request, args.output, args.native_locator, args.written_at)))
