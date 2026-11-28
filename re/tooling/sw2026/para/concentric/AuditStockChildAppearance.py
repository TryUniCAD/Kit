from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from unittest.mock import patch


HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
ROOT = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover/ConcentricChildAppearanceContrast03')
REVISION = 'e58710051d653745ec9ed68da724bdc5ee3e028a'
TRIAL = '6900ca2e4a76c5d27dd69e6441733d0ca4c49d6825887ee5399058811aaaf3c4'
RESULT = '2e679029ae772835378119e5c6bded8afc81255be95dd1b896a4c013033cbae8'
RECIPE = '3dc79b11847616ea4e9a195465979d82bdc53cc0cd5c06343f292193c874bed5'
PREPARER = '618e066d62155ff755e493698198cbdba9efc861fd1d9d8ef77f737be36f605d'
RECORDS = {
    'ControlBefore': '5259fcaac4b9e9ce9333a3e3e9f83cae32154003d80cc5d8202d4e8f6ed7539f',
    'AuthorA': '4aa7d686334315d3957bf8f99985b588c5ea3e454299ac8aa40de1dbfb68cc15',
    'ReopenA': '7c6d153088b3d3fd9e83541a27ca3d1e25d6dd124721430f1cd2be4b811e6fa8',
    'AuthorB': '0f91bd8c5b48af3dfe9cff90d14093aa62aff09cdcc33694d94534474e9b46f0',
    'ReopenB': '7375508c6fd36d347991539ad346eaffe2d66bd1412620d5f93b6e1aa455ea73',
    'ControlAfter': 'b8ee16b6aa042b188a1aa7349db4e035914025dfd7980f5254074cb9d74dc6d9',
}
PART = 'DisclosedRadialSceneProbe.SLDPRT'
CLASS = 'PWMaterialProperties_c'
POINT = 'mgPoint_c.restore'
ROUGHNESS = {'A': 0.3125, 'B': 0.6875}
STOCK_RGB = (229, 229, 229)
STOCK_PACKED = 0xE5E5E5
ORDER = (
    ('i32', 'f20'), ('u32', 'f28 f2c f30'), ('f64', 'f38'), ('i32', 'f40 f48 f4c'),
    ('f64', 'f68 f70 f78 f80 f88 f90'), ('i32', 'f1c0 f1c4'), ('f64', 'f50 f58'),
    ('i32', 'f60 f98 f9c'), ('f64', 'fb0 fb8'), ('i32', 'fa0 fa4 fa8'),
    ('text', 'fe0 fe8'), ('i32', 'ff8'), ('f64', 'f100 f108 f110 f118 f120 f128'),
    ('u32', 'f130'), ('f64', 'f138 f140 f150 f158 f168 f170 f178 f180 f188 f190 f198 f1a0'),
    ('i32', 'f1a8'), ('f64', 'f1d8 f1e0 f1e8 f1f0 f1f8 f200'), ('point', 'f208'),
    ('f64', 'fc0 fc8'), ('i32', 'f1ac f220'), ('f64', 'f228 f230 f238 f240'), ('i32', 'f248'),
    ('f64', 'f250 f258 f260 f268 f270 f278'), ('text', 'f280'),
    ('i32', 'fd8 f1b0 f1b4 f1b8 f1bc f288 f2ac'), ('f64', 'f2a0'), ('i32', 'f2a8 f298'),
    ('f64', 'f1c8'), ('i32', 'f2c0'), ('f64', 'f2c8'), ('i32', 'f2d0'), ('text', 'f290'),
    ('i32', 'f2d4 f2e0 f2e8 f2ec'), ('text', 'f2f8'), ('f64', 'f300 f308'), ('i32', 'f310'),
    ('text', 'ff0'), ('i32', 'f314'), ('f64', 'f318'),
)


def require(value, detail):
    if not value:
        raise ValueError(detail)


def verified(path, wanted):
    require(path.is_file() and path.resolve(strict=True) == path, 'source redirected or missing: ' + path.name)
    value = path.read_bytes()
    require(sha256(value).hexdigest() == wanted, 'frozen hash differs: ' + path.name)
    return value


def prepare_worker(folder):
    tar = folder / 'source.tar'
    for tree in ('src', 're/tooling/sw2026'):
        subprocess.run(['git', 'archive', '--format=tar', '--output', str(tar), '--prefix=' + tree + '/',
                        REVISION + ':' + tree], cwd=REPO, check=True)
        with tarfile.open(tar) as source:
            source.extractall(folder, filter='data')
    helpers = 'tests/Convert/Solidworks/Research'
    subprocess.run(['git', 'archive', '--format=tar', '--output', str(tar), '--prefix=' + helpers + '/',
                    REVISION + ':' + helpers, 'ConstructionGuard.py'], cwd=REPO, check=True)
    with tarfile.open(tar) as source:
        source.extractall(folder, filter='data')
    target = folder / HERE.relative_to(REPO)
    with target.open('xb') as stream:
        stream.write(HERE.read_bytes())
    return target


def definition_context(version):
    from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.GeometryFields import KGeometryFields
    from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
    from convert.adapters.solidworks.Archive.Definition.ModelDefContext import ModelDefContext

    require(version == 19000, 'research appearance extension requires effective archive version 19000')
    context = ModelDefContext(version)
    require(CLASS not in context.LayoutsValue and CLASS not in context.SchemasValue, 'overlapping SDK registration')
    rows = []
    for kind, names in ORDER:
        for name in names.split():
            if kind == 'text':
                fields = NativeField('Text', name)
            elif kind == 'point':
                fields = NativeField('Embed', name, POINT)
            else:
                fields = NativeField('Scalar', name, kind)
            rows.append(fields)
    require(len(rows) == 98 and len({row.NameValue for row in rows}) == 98, 'static native appearance field order differs')
    return replace(context, LayoutsValue=dict(context.LayoutsValue) | {CLASS: tuple(rows), POINT: KGeometryFields[POINT]},
                   SchemasValue=dict(context.SchemasValue) | {CLASS: (1,)})


def definition_evidence(archive, reader, writer, expected_ids, roughness, leaves):
    raw = archive.require('Contents/Definition')
    loaded = reader(raw, 19000)
    stored = writer(loaded.GraphValue)
    root = loaded.GraphValue.DocumentValue
    require(root.ClassValue.NameValue == 'uiPartDoc_c' and root.FieldsValue['has_pwmaterial'] == 1,
            'populated archive must be owned by the actual part Definition')
    mgr = root.FieldsValue['f1110']
    items = mgr['list']['items']
    require(len(items) == mgr['list']['n'] == 2, 'unmeasured appearance reference inventory')
    require(stored.OutputValue == raw and loaded.MapValue == stored.MapValue
            and all(wire.UsageValue.IsComplete and not wire.UsageValue.MissingNames and not wire.UsageValue.ByteFields
                    and wire.UsageValue.SchemaCalls[CLASS] == len(items) for wire in (loaded, stored)),
            'Definition replay, terminal map or typed owners differ')
    graphs, proof = {}, []
    for item in items:
        node = item['o']
        values = node.FieldsValue
        require(node.ClassValue.NameValue == CLASS and node.ClassValue.SchemaValue == 1 and values['f20'] == 1
                and len(values) == 98,
                'unmeasured material class, schema or inner version')
        ids = [values['f2e8'] & 0xffffffff, values['f2ec'] & 0xffffffff]
        require(type(node.IndexValue) is int and node.IndexValue not in graphs and ids == expected_ids
                and (values['f140'], values['f28']) == (roughness, STOCK_PACKED),
                'separate Definition records do not bind their observed common material ID and authored roughness')
        graphs[node.IndexValue] = leaves(values)
        proof.append({'object_offset': node.StartOffset, 'end_exclusive': node.EndOffset, 'archive_slot': node.IndexValue,
                      'schema': node.ClassValue.SchemaValue, 'internal_version': values['f20'], 'fields': len(values),
                      'packed_primary_color': values['f28'], 'classic_roughness': values['f140'], 'ids': ids})
    return {'bytes': len(raw), 'sha256': sha256(raw).hexdigest(), 'typed_replay': True, 'opaque_bytes': 0,
            'manager_allocator_words': [mgr['f08'], mgr['f0c']], 'records_in_manager_order': proof,
            'terminal_map': loaded.MapValue.CounterValue, 'same_public_id_distinct_graph_nodes': True}, graphs


def compare():
    sw2026 = HERE.parents[2]
    sys.path[:0] = [str(HERE.parent), str(REPO), str(REPO / 'src'), str(sw2026), str(sw2026 / 'serial')]
    verified(HERE.with_name('PrepareChildAppearanceContrast.py'), PREPARER)
    from PrepareChildAppearanceContrast import change, collect_audit, leaves
    from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    trial = json.loads(verified(ROOT / 'Trial.json', TRIAL))
    result = json.loads(verified(ROOT / 'Result.json', RESULT))
    recipe = json.loads(verified(ROOT / 'Recipe.json', RECIPE))
    require(recipe['trial_sha256'] == TRIAL and trial['revision']['preparer_sha256'] == PREPARER,
            'earlier frozen native recipe or evaluator differs')
    for name, wanted in trial['files_sha256'].items():
        require((ROOT / name).is_relative_to(ROOT), 'unexpected frozen input path')
        verified(ROOT / name, wanted)
    for role, wanted in RECORDS.items():
        verified(ROOT / 'Inspection' / role / 'Record.json', wanted)
    paths = {lane: (ROOT / 'Inspection' / ('Author' + lane) / PART, result['phases']['Author' + lane]['saved_sha256'])
             for lane in ('A', 'B')}
    archives = {lane: SldprtArchive.from_bytes(verified(path, wanted)) for lane, (path, wanted) in paths.items()}
    read_module = import_module('convert.adapters.solidworks.Archive.Definition.ReadModelDef')
    write_module = import_module('convert.adapters.solidworks.Archive.Definition.WriteModelDef')
    reader = read_module.ReadModelDef
    writer = write_module.WriteModelDef
    try:
        reader(archives['A'].require('Contents/Definition'), 19000)
    except BodyUnsupported as exc:
        require(str(exc) == 'unsupported SOLIDWORKS body class PWMaterialProperties_c schema 1', 'earlier refusal differs')
    else:
        raise ValueError('unextended SDK unexpectedly admitted the populated material manager')
    proofs, graphs = {}, {}
    with patch.object(read_module, 'ModelDefContext', definition_context), patch.object(write_module, 'ModelDefContext', definition_context):
        audit = collect_audit(ROOT, TRIAL, RESULT)
        for lane, archive in archives.items():
            target = result['phases']['Reopen' + lane]['appearance']
            require(target['primary_color'] == STOCK_PACKED and target['roughness'] == ROUGHNESS[lane], 'cold native source inputs differ')
            proofs[lane], graphs[lane] = definition_evidence(archive, reader, writer, target['ids'], ROUGHNESS[lane], leaves)
    require(tuple(graphs['A']) == tuple(graphs['B']), 'same-model contrast changed the ordered archive owner slots')
    slots = tuple(graphs['A'])
    delta = {str(slot): change(graphs['A'][slot], graphs['B'][slot]) for slot in slots}
    copies = {lane: change(graphs[lane][slots[0]], graphs[lane][slots[1]]) for lane in ('A', 'B')}
    return audit | {'audit_revision': REVISION, 'recipe_sha256': RECIPE, 'native_phase_receipt_sha256': RECORDS,
                    'preparer_sha256': PREPARER, 'frozen_files_verified': len(trial['files_sha256']),
                    'populated_definition': proofs, 'definition_material_leaf_delta': delta, 'definition_within_arm_pair_delta': copies,
                    'native_processes': result['native_processes'], 'native_checks': sum(row['numeric_checks'] for row in result['phases'].values()),
                    'stock_rgb': list(STOCK_RGB), 'original_sdk_refuses': True, 'native_assets_emitted': 0}


def main():
    parser = ArgumentParser()
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--verify-existing', action='store_true')
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(compare(), sort_keys=True, allow_nan=False))
        return
    output = ROOT / 'TypedAuditStockAppearance.json'
    require(ROOT.resolve(strict=True) == ROOT and (output.is_file() if args.verify_existing else not output.exists()),
            'expected audited evidence in the requested publication mode')
    with TemporaryDirectory(prefix='kit-stock-appearance-auditor-') as directory:
        directory = Path(directory).resolve(strict=True)
        entry = prepare_worker(directory)
        worker = subprocess.run([sys.executable, '-I', '-B', str(entry), '--worker'], cwd=directory,
                                stdout=subprocess.PIPE, check=True)
        verified_run = json.loads(worker.stdout)
    payload = (json.dumps(verified_run, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    if args.verify_existing:
        require(verified(output, sha256(payload).hexdigest()) == payload, 'audit is not reproducible')
    else:
        with output.open('xb') as stream:
            stream.write(payload)
    print(json.dumps({'typed_audit': str(output), 'sha256': sha256(payload).hexdigest(),
                      'definition_delta': verified_run['definition_material_leaf_delta'],
                      'appearance_delta': verified_run['paired_appearance_field_delta']}, sort_keys=True))


if __name__ == '__main__':
    main()
