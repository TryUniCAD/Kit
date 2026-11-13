import json
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
TOOLS = runpy.run_path(str(BASE.parent / 'ReadBinaryMembers.py'))
CONTENTS = Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents').expanduser()


def calls(binary, symbol):
    result = []
    for address, (operation, operands, annotation) in binary.instructions(symbol).items():
        if operation not in ('b', 'bl'):
            continue
        target = annotation.removeprefix('symbol stub for: ') if annotation.startswith('symbol stub for: ') else operands[0]
        if target.startswith('__Z'):
            name = TOOLS['demangle'](target)
            if any(piece in name for piece in ('::make(', '::findOrMake(', '::onPostCreation(', '::create', '::initialize', '::latestVersion(', '::installOwner(', '::system_clock::now(', '::addRoot(', '::designComponent(', '::parent(')):
                result.append({'callAddress': hex(address), 'callee': name})
    return result


def main():
    specifications = {
        'NsCommonData10': ('Libraries/Neutron/NsCommonData10.dylib', [
            '__ZN2Ns4Comp13ComponentBase14onPostCreationENS_10DataChange9ETransactE',
            '__ZN2Ns10CommonData14MassPropertiesC2Ev',
            '__ZN2Ns11Expressions9Interface13latestVersionEv',
            '__ZN2Ns4Comp18BaseOccurrencePathC2ERKNS_9StrongRefINS0_13ComponentBaseEEE',
        ]),
        'NsComponent10': ('Libraries/Neutron/NsComponent10.dylib', [
            '__ZN2Ns4Comp25ComponentAssetAdapterImpl18initializeNewAssetEv',
            '__ZN2Ns4Comp9Component14onPostCreationENS_10DataChange9ETransactE',
        ]),
        'NaFusion10': ('Libraries/Applications/Fusion/NaFusion10.dylib', [
            '__ZN2Na15FusionComponentC2EPN2Ns7SegmentERKNSt3__112basic_stringIwNS4_11char_traitsIwEENS4_9allocatorIwEEEE',
            '__ZN2Na15FusionComponent14onPostCreationEN2Ns10DataChange9ETransactE',
            '__ZN2Na15FusionComponent15createPMObjectsEb',
            '__ZN2Na15FusionComponent24createOriginWorkGeometryEv',
            '__ZN2Na13DesignCapture16DcDesignFragment14onPostCreationEN2Ns10DataChange9ETransactE',
            '__ZN2Na8FeaturesC2ERKN2Ns10PassiveRefINS1_6EntityEEE',
            '__ZN2Na22FusionAssetAdapterImpl18initializeNewAssetEv',
            '__ZN2Na13DesignCapture12DcOccurrenceC2ERKN2Ns4Comp14OccurrencePathE',
        ]),
        'NsTypes10': ('Libraries/Neutron/NsTypes10.dylib', ['__ZN2Ns16PhysicalMaterialC2Ev']),
    }
    result = {'schema': 'FusionAuthoringConstructorEvidence/1', 'build': '2706.1.17', 'architecture': 'arm64', 'sources': [], 'functions': [], 'literalEvidence': [], 'scope': 'Selected constructor roles and literals, not a proof that every authored policy value is the vendor default or that the reduced graph is loadable'}
    binaries = {}
    for source, (relative, symbols) in specifications.items():
        binary = TOOLS['Binary'](CONTENTS / relative)
        binaries[source] = binary
        result['sources'].append({'source': source, 'pathWithinContents': relative, 'sha256': binary.sha256})
        for symbol in symbols:
            instruction = binary.instructions(symbol)
            result['functions'].append({'source': source, 'symbol': symbol, 'name': TOOLS['demangle'](symbol), 'functionAddress': hex(min(instruction)) if instruction else None, 'calls': calls(binary, symbol), 'status': 'located' if instruction else 'not_located'})
    checks = [
        ('NaFusion10', specifications['NaFusion10'][1][0], 'FusionComponent.operationSeedId', '0x7d8', [(0x1103384, 'mov', ['w8', '#0x12c']), (0x1103388, 'str', ['x8', '[x19, #0x7d8]'])], 300),
        ('NaFusion10', specifications['NaFusion10'][1][0], 'FusionComponent.isAsBuiltPositions', '0x750', [(0x110336c, 'mov', ['w8', '#0x1']), (0x1103370, 'strb', ['w8', '[x19, #0x750]'])], True),
        ('NaFusion10', specifications['NaFusion10'][1][0], 'FusionComponent.m_opacity', '0x7d0', [(0x110337c, 'mov', ['w8', '#0x3f800000']), (0x1103380, 'str', ['w8', '[x19, #0x7d0]'])], 1.0),
        ('NaFusion10', specifications['NaFusion10'][1][0], 'FusionComponent.subType', '0x840', [(0x11033c0, 'str', ['wzr', '[x19, #0x840]'])], 0),
        ('NaFusion10', specifications['NaFusion10'][1][5], 'Features.m_curFeatureId', '0x178', [(0xc787e0, 'mov', ['w8', '#0x1']), (0xc787e8, 'str', ['w8', '[x0, #0x178]'])], 1),
        ('NsCommonData10', specifications['NsCommonData10'][1][1], 'MassProperties overrides', '0x20..0x3f', [(0x114828, 'fmov.2d', ['v0', '#-1.00000000']), (0x11482c, 'stp', ['q0', 'q0', '[x0, #0x20]'])], -1.0),
        ('NsCommonData10', specifications['NsCommonData10'][1][2], 'Parameter.birthday expression version', None, [(0xdfc08, 'mov', ['w0', '#0x6'])], 6),
        ('NsCommonData10', specifications['NsCommonData10'][1][3], 'BaseOccurrencePath.creationState', '0x78', [(0x42e5c, 'mov', ['w9', '#0x3']), (0x42e60, 'strb', ['w9', '[x0, #0x78]'])], 3),
        ('NaFusion10', specifications['NaFusion10'][1][7], 'DcOccurrence.stateIdx', '0x1a0', [(0x321eac, 'mov', ['w8', '#-0x1']), (0x321eb0, 'str', ['w8', '[x19, #0x1a0]'])], -1),
    ]
    for source, symbol, field, offset, expected, value in checks:
        instructions = binaries[source].instructions(symbol)
        matched = all(instructions.get(address, (None, None, None))[:2] == (operation, operands) for address, operation, operands in expected)
        result['literalEvidence'].append({'source': source, 'field': field, 'objectOffset': offset, 'value': value, 'instructionAddresses': [hex(item[0]) for item in expected], 'instructionsMatch': matched})
    value_binary = binaries['NsTypes10']
    material = TOOLS['Trace'](value_binary, value_binary.instructions('__ZN2Ns16PhysicalMaterial19initializeMemberSetEjPNS_9MemberSetE'), 3).run()
    material_names = {'name', 'proteinMaterialID', 'libraryID', 'assetReference', 'ProteinAssetManager'}
    result['materialDefault'] = {'source': 'NsTypes10', 'constructorAddress': '0x5e514', 'zeroVectorAddress': '0x5e544', 'zeroStoreAddresses': ['0x5e548', '0x5e550', '0x5e554', '0x5e558', '0x5e55c'], 'zeroedByteRange': '[0x10,0xb0)', 'registeredFields': [{key: entry[key] for key in ['name', 'registrationAddress', 'memberAddress', 'cppType']} for entry in material['membersInRegistrationOrder'] if entry['name'] in material_names], 'conclusion': 'The default constructor starts the four persisted string members empty and the material-manager reference null. It does not prove that a fully initialized Fusion document may omit a material package.'}
    (BASE / 'ConstructorEvidence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'functions': len(result['functions']), 'literalMatches': sum(item['instructionsMatch'] for item in result['literalEvidence']), 'literalCount': len(result['literalEvidence'])}))


if __name__ == '__main__':
    main()
