from pathlib import Path
from hashlib import sha256
from struct import unpack_from
import argparse
import importlib.util
import json


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(args):
    record_path = Path(args.record).resolve()
    record = json.loads(record_path.read_text())
    root = Path(args.root).resolve()
    helper_row = next(row for row in record['repository_inputs'] if row['path'] == 're/tooling/sw2026/materials/MaterialPe.py')
    helper = root / helper_row['path']
    if helper.stat().st_size != helper_row['bytes'] or digest(helper) != helper_row['sha256']:
        raise ValueError('PE metadata helper differs')
    spec = importlib.util.spec_from_file_location('LinkedEdgeOriginalPe', helper)
    if spec is None or spec.loader is None:
        raise ValueError('PE metadata helper unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    images = {}
    for row in record['modules']:
        image = module.PeImage(Path(args.bin_directory) / row['name'])
        if image.base != int(row['preferred_base'], 16) or len(image.data) != row['bytes'] or image.sha256 != row['sha256']:
            raise ValueError('original image differs: ' + row['name'])
        images[row['name']] = image
    fragment_count = 0
    for row in record['functions']:
        image = images[row['module']]
        for fragment in row['fragments']:
            start = int(fragment['start'], 16)
            end = int(fragment['end_exclusive'], 16)
            actual = image.pin(fragment['name'], start, end)
            if any(actual[key] != fragment[key] for key in ['file_offset', 'bytes', 'sha256']):
                raise ValueError('source range differs: ' + row['name'])
            fragment_count += 1
    for row in record['instruction_windows']:
        actual = images[row['module']].pin(row['name'], int(row['start'], 16), int(row['end_exclusive'], 16))
        if any(actual[key] != row[key] for key in ['file_offset', 'bytes', 'sha256']):
            raise ValueError('selected source window differs: ' + row['name'])
    for row in record['direct_calls']:
        image = images[row['module']]
        site = int(row['site'], 16)
        offset = image.offset(site)
        if image.data[offset] != 0xe8 or site + 5 + unpack_from('<i', image.data, offset + 1)[0] != int(row['target'], 16):
            raise ValueError('direct call differs: ' + row['site'])
    for row in record['virtual_cells']:
        image = images[row['module']]
        if image.u64(image.offset(int(row['address'], 16))) != int(row['target'], 16):
            raise ValueError('concrete virtual cell differs: ' + row['name'])
    inventories = {name: image.imports() for name, image in images.items()}
    for row in record['imports']:
        actual = inventories[row['module']].get(int(row['iat'], 16))
        if actual != {'module': row['target_module'], 'name': row['target_name']}:
            raise ValueError('import identity differs: ' + row['iat'])
    repository_inputs = []
    for row in record['repository_inputs']:
        path = root / row['path']
        same = path.is_file() and path.stat().st_size == row['bytes'] and digest(path) == row['sha256']
        repository_inputs.append({'path': row['path'], 'matches_observed_source': same})
    return {
        'schema': 1,
        'task_id': record['task_id'],
        'source_identity_passed': True,
        'evidence': 'original-PE metadata verification of manually reviewed conditional source rules',
        'record_sha256': digest(record_path),
        'verifier_sha256': digest(Path(__file__).resolve()),
        'metadata_helper_sha256': digest(helper),
        'counts': {
            'original_modules': len(images),
            'complete_functions_or_leaves': len(record['functions']),
            'function_fragments': fragment_count,
            'instruction_windows': len(record['instruction_windows']),
            'direct_calls': len(record['direct_calls']),
            'import_identities': len(record['imports']),
            'concrete_virtual_cells': len(record['virtual_cells']),
        },
        'repository_input_observation': repository_inputs,
        'native_route_executed': False,
        'generated_pair_accepted': False,
        'activity': record['activity'],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--bin-directory', required=True)
    parser.add_argument('--record', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = verify(args)
    output = Path(args.output)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'source_identity_passed': True, 'output_sha256': digest(output), 'counts': result['counts']}, sort_keys=True))


if __name__ == '__main__':
    main()
