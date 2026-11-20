from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import check_model, model_state, read_part
from convert import open_document, write_document


def text_bags(document):
    configuration, = document.configurations
    return [document.metadata['document_summary'], document.metadata['custom_properties'],
            configuration.attributes['custom_properties']]


def inspect(source):
    original = read_part(source)
    target = BytesIO()
    write_document(original, target, destination_format='interchange.json', allow_carrier=False)
    restored = open_document(target.getvalue(), source_format='interchange.json',
                             strict=True, include_tessellation=False)
    check_model(original, restored)
    state, text = model_state(restored), text_bags(restored)
    if (model_state(original) != state or text_bags(original) != text
            or original.source != restored.source or original.configurations != restored.configurations
            or original.diagnostics != restored.diagnostics):
        raise ValueError('direct JSON write changed the qualified property or configuration owner')
    return {'source_sha256': sha256(source.read_bytes()).hexdigest(),
            'status': state['status'], 'text': text,
            'configuration': state['configuration'],
            'source_provenance_preserved': True}


if __name__ == '__main__':
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
