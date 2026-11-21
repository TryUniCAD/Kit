from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from MaterialPe import PeImage

MODULES = {
    'sldmodu.dll': '569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e',
    'sldmfcu.dll': 'af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735',
    'sldmatu.dll': '8a07d6b5d8d7d4f9f064b28e1d60f853fd754caa6d507db28b06031f287e051e',
    'slduiu.dll': '025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7',
    'sldappu.dll': '50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf',
}
FUNCTIONS = (
    ('sldmodu.dll', 'moPart_c::getMaterial', 0x4b2879e0, 0x4b2879e8),
    ('sldmodu.dll', 'moMaterial_c::getDensity', 0x4b285140, 0x4b285145),
    ('sldmodu.dll', 'moMaterial_c::Serialize', 0x4c224c60, None),
    ('sldmodu.dll', 'moDensityParameter_c::Serialize', 0x4c177fe0, None),
    ('sldmodu.dll', 'moDensityParameter_c pointer store', 0x4c1773b0, None),
    ('sldmodu.dll', 'moDensityParameter_c pointer load', 0x4c176d80, None),
    ('sldmodu.dll', 'moModel_c::getMaterialName', 0x4c022be0, None),
    ('sldmodu.dll', 'moPartConfiguration_c viz getter', 0x4b289be0, 0x4b289be5),
    ('sldmodu.dll', 'moPartConfiguration_c density setter', 0x4b5a0160, 0x4b5a0169),
    ('sldmodu.dll', 'moAtom_c::getMaterialNode', 0x4b2879f0, 0x4b2879f8),
    ('sldmodu.dll', 'moAtom_c::getMaterialId', 0x4bcf7900, 0x4bcf793a),
    ('sldmodu.dll', 'moAtom_c::getFullMaterialName', 0x4bcf5f20, None),
    ('sldmodu.dll', 'moAtom_c::getDensityValue', 0x4bcf5670, None),
    ('sldmodu.dll', 'moBaseConfiguration_c::getMatIdFromAtomId', 0x4bdd9270, None),
    ('sldmodu.dll', 'moConfigurationMgr_c::getCustomDefinedMatDensity', 0x4b894790, 0x4b8947e0),
    ('sldmodu.dll', 'moCustomDefinedMaterialProperty_c constructor', 0x4b881600, None),
    ('sldmodu.dll', 'moCustomDefinedMaterialProperty_c::Serialize', 0x4b88a910, None),
    ('sldmodu.dll', 'moConfigurationMgr_c::setCustomDefinedMatPropMap', 0x4b89f370, None),
    ('sldmodu.dll', 'moBaseConfiguration_c::setMaterialApplied', 0x4bdf20a0, None),
    ('sldmfcu.dll', 'moVisualProperties_c::getMatProps', 0x3c922000, None),
    ('sldmfcu.dll', 'uoMaterialProperties::getIdName', 0x3c7de630, 0x3c7de635),
    ('sldmfcu.dll', 'uoMaterialProperties::parseIDNameForMaterialInfo', 0x3c850ea0, None),
    ('sldmatu.dll', 'dlgMaterialEditor_c::ApplyDensity2Config', 0x3c3c7960, None),
    ('sldmatu.dll', 'dlgMaterialEditor_c::ApplyMatToConfigs', 0x3c3c7a10, None),
    ('sldmatu.dll', 'sldMatDef_c::getDensity', 0x3c2c7fd0, 0x3c2c7fd9),
    ('sldmatu.dll', 'sldMatDef_c::addDensity', 0x3c2c7820, 0x3c2c7829),
    ('sldmatu.dll', 'ApplyMaterialByAPI', 0x3c3e97d0, None),
    ('sldmatu.dll', 'dlgMaterialEditor_c::LoadPHYMATFiles', 0x3c3ce940, None),
    ('sldmatu.dll', 'materialsEditorDlg_c::xmlParseDatabase', 0x3c4045d0, None),
    ('sldmatu.dll', 'materialsEditorDlg_c::xmlValidateDOC', 0x3c4051d0, None),
    ('sldmatu.dll', 'materialsEditorDlg_c::apiGetMaterialSchemaPathName', 0x3c3fa690, None),
    ('sldmatu.dll', 'dlgMaterialEditor_c::iDumpMaterialStream', 0x3c3e16a0, None),
    ('slduiu.dll', 'uiModelDoc::ApplyMaterialByName', 0x4996c550, None),
    ('sldappu.dll', 'auPartDocWrapper_c::SetMaterialPropertyName2', 0x456d8780, None),
    ('sldappu.dll', 'auPartDocWrapper_c::GetMaterialPropertyName2', 0x456d2900, None),
)
LITERALS = (
    ('sldmfcu.dll', 0x3cc724bc, '|'),
    ('sldmfcu.dll', 0x3cc724c0, 'steel'),
    ('sldmfcu.dll', 0x3cb2df54, '%d'),
    ('sldmatu.dll', 0x3c5818a0, '%s|%s|%d'),
    ('sldmatu.dll', 0x3c5818b8, '%s|%s'),
    ('sldmatu.dll', 0x3c576818, '\\xmlschema\\sldmaterials.xsd'),
    ('sldmatu.dll', 0x3c581ac0, 'swXmlContents'),
    ('sldmatu.dll', 0x3c581ae0, 'MATERIALTREE'),
)
SLOTS = (
    ('sldmodu.dll', 0x4ce2d008, 0x1040, 0x4b289be0),
    ('sldmodu.dll', 0x4ce2d008, 0x1db8, 0x4b5a0160),
    ('sldmodu.dll', 0x4cfe9890, 0x28, 0x4c224c60),
    ('sldmodu.dll', 0x4d124660, 0x28, 0x4c177fd0),
    ('sldmodu.dll', 0x4cec88d8, 0x28, 0x4b88a910),
)
IMPORTS = (
    ('sldmodu.dll', 0x4cd338c0, 'SLDMFCU.dll', '?getMatProps@moVisualProperties_c@@QEAAPEAVuoMaterialProperties@@XZ'),
    ('sldmatu.dll', 0x3c524948, 'SLDMODU.dll', '?getDensity@moMaterial_c@@QEBAPEAVmoDensityParameter_c@@XZ'),
    ('sldmatu.dll', 0x3c524950, 'SLDMODU.dll', '?setValue@moDoubleParameter_c@@QEAAXNH@Z'),
)


def inspect(directory):
    images = {name: PeImage(directory / name) for name in MODULES}
    for name, expected in MODULES.items():
        if images[name].sha256 != expected:
            raise ValueError('original module hash differs: ' + name)
    functions = []
    for name, label, start, end in FUNCTIONS:
        image = images[name]
        if end is None:
            bounds = image.range(start)
            if bounds is None or bounds[0] != start:
                raise ValueError('runtime function bounds differ: ' + label)
            end = bounds[1]
            scope = 'complete PE runtime-function range'
        else:
            scope = 'complete statically inspected leaf or getter range'
        functions.append(image.pin(label, start, end) | {'module': name, 'scope': scope})
    literals = []
    for name, address, expected in LITERALS:
        image = images[name]
        length = len(expected.encode('utf-16-le'))
        offset = image.offset(address)
        raw = image.data[offset:offset + length + 2]
        if raw.decode('utf-16-le') != expected + '\0':
            raise ValueError('declared native vocabulary differs')
        literals.append({'module': name, 'address': hex(address), 'value': expected,
                         'bytes_with_terminator': len(raw), 'sha256': sha256(raw).hexdigest()})
    slots = []
    for name, vtable, slot, expected in SLOTS:
        image = images[name]
        target = image.u64(image.offset(vtable + slot))
        if target != expected:
            raise ValueError('concrete native vtable slot differs')
        slots.append({'module': name, 'vtable': hex(vtable), 'slot': hex(slot),
                      'target': hex(target), 'sha256': image.pin('slot', vtable + slot, vtable + slot + 8)['sha256']})
    imports = []
    for name, address, module, symbol in IMPORTS:
        actual = images[name].imports().get(address)
        if actual is None or actual['module'].lower() != module.lower() or actual['name'] != symbol:
            raise ValueError('native imported signature differs')
        imports.append({'module': name, 'iat_address': hex(address), 'target': actual})
    return {'schema': 'kit.sw2026.assigned-material-static-pins.v1',
            'status': 'static mapping only; no new native material assignment measured',
            'build': '34.5.2.0604', 'effective_document_version': 19000,
            'modules': [{'name': name, 'sha256': image.sha256, 'bytes': len(image.data),
                         'preferred_base': hex(image.base)} for name, image in images.items()],
            'functions': functions, 'literal_vocabulary': literals, 'vtable_slots': slots,
            'import_bindings': imports, 'native_runs': 0, 'heldout_inputs_read': 0,
            'shared_target_sessions_opened': 0, 'writer_outputs': 0}


def main():
    parser = ArgumentParser()
    parser.add_argument('--bin', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output already exists')
    report = inspect(args.bin.resolve(strict=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'passed': True, 'output_sha256': sha256(args.output.read_bytes()).hexdigest(),
                      'functions': len(report['functions']), 'modules': len(report['modules'])}))


if __name__ == '__main__':
    main()
