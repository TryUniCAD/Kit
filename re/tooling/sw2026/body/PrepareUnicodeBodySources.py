from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from shutil import copyfile


ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
CONTROL = 'c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57'
CORNER = 'a441e79bc94219c4c0bb4390cc6d13643ca8c56cb0ff69abdb1fa694e82d2778'
CENTER = '9a619f233088d4c26d767642b02ec6dfbdfd25baad7686cd2265210da78f0f00'
TOOLS = ('AuthorUnicodeBodyNames.py', 'AuthorPartDriverNames.py', 'AuthorCurves.py',
    'AuthorRectangleAnchors.py', 'InspectFresh.py', 'InspectSdkBlindPart.py',
    'InspectSdkCornerOwners.py', 'InspectCornerPointOwners.py', 'SdkCornerOwnerGraph.py',
    'OracleIdentity.py', 'Swapp.py')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = ArgumentParser()
    parser.add_argument('--oracle-tools', type=Path, required=True)
    parser.add_argument('--disclosed-sources', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    owner = Path(__file__).resolve().parent
    sources = {'Control.SLDPRT': (args.disclosed_sources / 'Control.SLDPRT', CONTROL),
        'CornerBaseline.SLDPRT': (args.disclosed_sources / 'Inspection/NamedCorner/Author/Baseline.SLDPRT', CORNER),
        'CenterBaseline.SLDPRT': (args.disclosed_sources / 'Inspection/NamedCenter/Author/Baseline.SLDPRT', CENTER)}
    for name, (path, expected) in sources.items():
        if digest(path) != expected:
            raise ValueError('disclosed unicode source changed: ' + name)
    args.output.mkdir(parents=True, exist_ok=False)
    tools = args.output / 'Tools'
    tools.mkdir()
    for name in TOOLS:
        source = owner / name if name == 'AuthorUnicodeBodyNames.py' else args.oracle_tools / name
        copyfile(source, tools / name)
    for name, (source, _) in sources.items():
        copyfile(source, args.output / name)
    cases = []
    for name, label, source, checksum, dimensions in (
        ('Accent', 'Pièce Ångström', 'CornerBaseline.SLDPRT', CORNER, [0.03173, 0.01827, 0.00741]),
        ('Bmp', '梁_Δοκός', 'CenterBaseline.SLDPRT', CENTER, [0.04319, 0.02563, 0.00683]),
        ('Supplementary', '梁_𐐷_Δ', 'CornerBaseline.SLDPRT', CORNER, [0.03173, 0.01827, 0.00741])):
        encoded = label.encode('utf-16-le')
        cases.append({'name': name, 'body_name': label, 'source': source,
            'source_sha256': checksum, 'expected_source_dimensions_m': dimensions,
            'expected_utf16_units': [int.from_bytes(encoded[index:index + 2], 'little')
                                     for index in range(0, len(encoded), 2)],
            'drivers': [{'feature': feature, 'original_name': original, 'new_name': original}
                        for feature, original in (('AnchorSketch', 'D1'), ('AnchorSketch', 'D2'), ('AnchorBoss', 'D1'))]})
    job = {'schema': 'kit.sw2026.unicode-body-name-source.v1', 'oracle_sha256': ORACLE,
        'control_sha256': CONTROL, 'tools_sha256': {name: digest(tools / name) for name in TOOLS},
        'cases': cases, 'heldout_inputs_read': 0, 'writer_output_count': 0}
    path = args.output / 'Trial.json'
    path.write_text(dumps(job, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
                    encoding='utf-8', newline='\n')
    print(dumps({'packet': str(path), 'packet_sha256': digest(path), 'processes_started': 0,
                 'source_kind': 'explicitly disclosed native baselines only',
                 'planned_native_processes': 8, 'heldout_inputs_read': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
