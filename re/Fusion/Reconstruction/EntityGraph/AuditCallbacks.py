import collections
import hashlib
import json
import re
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
BASE = DIRECTORY.parent
BINARY = runpy.run_path(str(BASE / 'ReadBinaryMembers.py'))['Binary']
ROOT = Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents').expanduser()


def main():
    classes = json.loads((BASE / 'BinaryClasses.json').read_bytes())
    schema = {item['identifier'].upper(): item for item in json.loads((BASE.parent / 'LocalOracle/Reflection/Versions.json').read_bytes())['metatypes']}
    inventory = json.loads((DIRECTORY / 'GraphInventory.json').read_bytes())
    by_id = {item['identifier'].upper(): item for item in classes['classes']}
    sources = {item['id']: item for item in classes['sources']}
    binaries = {}
    records = []
    for identity in inventory['classes']:
        metatype = schema[identity.upper()]
        if metatype['category'] != 'value':
            continue
        source = by_id[identity.upper()]
        library = source['source']
        if library not in binaries:
            binaries[library] = BINARY(ROOT / sources[library]['pathWithinContents'])
        binary = binaries[library]
        stem = source['class'].split('::')[-1].removesuffix('ValueMetaType')
        initializers = [(name, value) for name, value in binary.named.items() if (name.startswith(source['class'] + '::initializeMemberSet(') or name.startswith(source['class'].removesuffix('ValueMetaType') + '::initializeMemberSet('))]
        callbacks = [(name, value) for name, value in binary.named.items() if stem.lower() in name.lower() and 'DataModelCallback::onSave(' in name]
        if stem == 'sketch_tag_id':
            callbacks = [(name, value) for name, value in binary.named.items() if name.startswith('SketchTagIdDataModelCallback::onSave(')]
        lifecycle = [(name, value) for name, value in binary.named.items() if stem.lower() in name.lower() and 'Callback::' in name and any(hook in name for hook in ('::onSave(', '::onPreSave(', '::onPostLoad('))]
        examined = []
        for name, (address, symbol) in initializers:
            calls = []
            for instruction, (operation, operands, annotation) in binary.instructions(symbol).items():
                if operation in ('bl', 'b') and ('dataModelCallback' in str(operands) or 'dataModelCallback' in annotation):
                    calls.append({'address': hex(instruction), 'target': annotation or operands[0]})
            examined.append({'symbol': symbol, 'signature': name, 'address': hex(address), 'callbackRegistrationCalls': calls})
        records.append({'identifier': identity, 'metatype': metatype['name'], 'source': library, 'schemaVersion': inventory['classes'][identity]['version'], 'registeredMemberCount': len(inventory['classes'][identity]['members']), 'initializers': examined, 'lifecycleCallbacks': [{'signature': name, 'address': hex(value[0]), 'symbol': value[1]} for name, value in lifecycle], 'saveCallbacks': [{'signature': name, 'address': hex(value[0]), 'symbol': value[1]} for name, value in callbacks]})
    result = {'schema': 'FusionGraphValueCallbackAudit/1', 'build': '2706.1.17', 'architecture': 'arm64', 'scope': 'All 22 value classes declared in controlled extrusion Design metadata; direct initializer callback registration and named save override inventory, not proof against every indirect registration', 'sources': [{'id': name, 'pathWithinContents': sources[name]['pathWithinContents'], 'sha256': hashlib.sha256((ROOT / sources[name]['pathWithinContents']).read_bytes()).hexdigest()} for name in binaries], 'classes': records}
    (DIRECTORY / 'ValueCallbacks.json').write_text(json.dumps(result, indent=2) + '\n')
    for item in records:
        print(item['metatype'], len(item['initializers']), sum(len(i['callbackRegistrationCalls']) for i in item['initializers']), [i['signature'].split('::onSave')[0] for i in item['saveCallbacks']])


if __name__ == '__main__':
    main()
