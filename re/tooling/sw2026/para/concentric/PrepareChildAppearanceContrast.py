from argparse import ArgumentParser
from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re
from struct import pack, unpack
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
SW2026 = HERE.parents[2]
sys.path[:0] = [str(HERE.parent), str(REPO), str(REPO / 'src'), str(SW2026), str(SW2026 / 'serial')]

from ObserveChildAppearanceContrast import BUILD, COLOR, MEMBERS, MODULES, PART_NAME, PHASES, RGB, ROUGHNESS, SCHEMA
from ConcentricNativeContract import checked, digest, require

HOME_PATH = Path('/Users/odin')
MANAGED = HOME_PATH / 'Documents/UniCAD/Oracle121Takeover'
RADIAL = MANAGED / 'ConcentricRadialIntent01'
REFERENCE = MANAGED / 'RadialConcentricDisplay04'
D01 = MANAGED / 'ConcentricMateSourcePacket02/Disclosed/D01/Native/Source'
WRITER = '3f5c5cca62a86569694d1fd9550a04f3217363b7'
AUDITOR = '090620126fcc73d064b83aff722574f2ce29491d'
EPOCH = 1795163100
VISUAL = 'ThirdPtyStore/VisualStates'
PINNED = {
    RADIAL / 'IndependentRequest.json': 'd25e6b4bdd6631c8c40aeae0335f96cebcbc740af0151dd7154ae08a873a6ca1',
    RADIAL / 'NativePacket01/Trial.json': '5834a9b528b526aebf9056881f72a87cbeae2ca8b0ca387ab4bef6c44ac47186',
    REFERENCE / 'Trial.json': 'ac2696da314b7e2d4939fd75664270acecfe0274a479eafb9c2c6d5440aaed4b',
    REFERENCE / 'Evidence/Prediction.json': '767d0a22a75e92f40a83126516a611b987ecf0c927e70ce9c491c3f37613e15c',
    REFERENCE / 'Evidence/GuestPython.json': '2f400697e28561cf93e5352e6f40b81258bf8998a72f6ce1589763bee31b9684',
}
CONTROL = {
    'parent': ('ConcentricD01AlignedFree.SLDASM', '2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2'),
    'child': ('ConcentricD01Child.SLDPRT', '92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa'),
}
EXTERNAL = {
    'frozen_radial': (REFERENCE / 'Frozen' / PART_NAME, 'b877a05784e23ae16c49e5ee74d01cc31ba62a87a24b21780c1327934c352970'),
    'saved_radial': (REFERENCE / 'Working' / PART_NAME, 'ade88a9c5831a2a4e707a7c484ecb8a77a91b389839065080b53cb7920d26fd9'),
    'd01_child': (D01 / CONTROL['child'][0], CONTROL['child'][1]),
}


def guest(path):
    return str(PureWindowsPath(r'\\Mac\Home', *path.relative_to(HOME_PATH).parts))


def publish(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(data)
    return sha256(data).hexdigest()


def read_json(path, wanted):
    return json.loads(checked(path, wanted).read_bytes())


def load_installed(path, wanted, runtime):
    path = checked(path, wanted)
    require(path.parent == MANAGED and path.resolve(strict=True) == path and re.fullmatch(r'ChildAppearanceInstalled[0-9]{2}\.json', path.name),
            'expected one managed immutable installed metadata receipt')
    value = read_json(path, wanted)
    asset = value['asset']
    oracle = PureWindowsPath(value['oracle'])
    data_root = PureWindowsPath(asset['data_root'])
    require(value['schema'] == SCHEMA and value['build'] == BUILD and value['modules'] == MODULES
            and value['native_processes_started'] == 0 and value['specified_state_selector'] == 3
            and all(value['runtime'][field] == runtime[field] for field in ('executable', 'version', 'pointer_bits'))
            and oracle.is_absolute() and data_root == oracle.parent / 'data'
            and PureWindowsPath(asset['path']) == data_root / 'graphics/materials/color.p2m'
            and re.fullmatch(r'[0-9a-f]{64}', asset['sha256']) and 0 < asset['bytes'] <= 32 * 1024 * 1024,
            'unexpected pinned build, installed color asset or guest runtime')
    for name, wanted_members in MEMBERS.items():
        members = value['interfaces'][name]['members']
        require({(member.casefold(), kind, count) for member, kind, count in wanted_members} <=
                {(member['name'].casefold(), member['kind'], member['count']) for member in members},
                f'wrong official invocation surface for {name}')
    return value


def checkout(directory, revision, paths):
    archive = directory / 'source.tar'
    for tree, selected in paths:
        subprocess.run(['git', 'archive', '--format=tar', '--output', str(archive), '--prefix=' + tree + '/',
                        revision + ':' + tree, *selected], cwd=REPO, check=True)
        with tarfile.open(archive) as source:
            source.extractall(directory, filter='data')


def prepare(name, installed_path, installed_sha):
    require(re.fullmatch(r'ConcentricChildAppearanceContrast[0-9]{2}', name), 'use a numbered disclosed packet')
    root = MANAGED / name
    require(not root.exists() and root.resolve() == root and MANAGED.resolve(strict=True) == MANAGED, 'packet path already exists or is redirected')
    radial_trial = read_json(RADIAL / 'NativePacket01/Trial.json', PINNED[RADIAL / 'NativePacket01/Trial.json'])
    reference = read_json(REFERENCE / 'Trial.json', PINNED[REFERENCE / 'Trial.json'])
    require(radial_trial['heldout_inputs_read'] == 0 and reference['heldout_inputs_read'] == 0, 'disclosed controls are required')
    runtime = read_json(REFERENCE / 'Evidence/GuestPython.json', PINNED[REFERENCE / 'Evidence/GuestPython.json'])
    installed = load_installed(installed_path, installed_sha, runtime)
    prediction = read_json(REFERENCE / 'Evidence/Prediction.json', PINNED[REFERENCE / 'Evidence/Prediction.json'])
    controls = reference['controls']
    require(set(controls) == set(CONTROL), 'control pair changed')
    for role, (name, expected) in CONTROL.items():
        control = checked(D01 / name, expected)
        require(controls[role] == {'host_path': str(control), 'guest_path': guest(control), 'sha256': expected,
                                   'bytes': control.stat().st_size}, 'original disclosed D01 locator differs')
    request = RADIAL / 'IndependentRequest.json'
    checked(request, PINNED[request])
    observer = HERE.with_name('ObserveChildAppearanceContrast.py')
    tool_bytes = {observer.name: observer.read_bytes()}
    for relative, wanted in reference['files_sha256'].items():
        if not relative.startswith('Tools/'):
            continue
        filename = Path(relative).name
        require(filename not in tool_bytes and relative == 'Tools/' + filename and filename.endswith('.py'), 'unexpected or duplicate tool')
        tool_bytes[filename] = checked(REFERENCE / relative, wanted).read_bytes()
    radial_observer = 'ObserveRadialScene.py'
    tool_bytes[radial_observer] = checked(RADIAL / 'NativePacket01/Tools' / radial_observer,
                                           radial_trial['tool_sha256'][radial_observer]).read_bytes()
    with TemporaryDirectory(prefix='kit-child-appearance-writer-') as scratch:
        scratch = Path(scratch)
        checkout(scratch, WRITER, [('src', ()), ('re/tooling/sw2026', ())])
        writer = scratch / SW2026.relative_to(REPO) / 'para/concentric/ProjectConcentricRadialIntent.py'
        working = root / 'Working' / PART_NAME
        arguments = [sys.executable, '-I', '-B', str(writer), 'build', '--request', str(request),
                     '--sha256', PINNED[request], '--output', str(scratch / 'Build'), '--native-destination', guest(working),
                     '--written-at', str(EPOCH)]
        completed = subprocess.run(arguments, cwd=scratch, stdout=subprocess.PIPE, check=True)
        generated = scratch / 'Build' / PART_NAME
        build = json.loads(completed.stdout)
        generated_bytes = checked(generated, build['output_sha256']).read_bytes()
        require(build == json.loads((generated.parent / 'Build.json').read_bytes()) and build['runtime_io_attempts'] == 0
                and build['generated_part_only'] is True and not build['native_processes_started']
                and len(build['linked_stream_bytes']) == 5 and build['request_sha256'] == PINNED[request], 'independent writer proof differs')
        shape = radial_trial['case']['request']['document']
        initial = build['independent_prediction']['initial']
        require(initial['radius_m'] == shape['radius_m'] and initial['depth_m'] == shape['depth_m']
                and initial['centre_of_mass_m'] == [*shape['center_m'], shape['depth_m'] / 2]
                and build['ordered_lights'] == [item[0] for item in radial_trial['lights']], 'native shape prediction disagrees with guarded input')
        root.mkdir(mode=0o700, exist_ok=False)
        for directory in ['Tools', 'Evidence', 'Working', 'Frozen', 'Inspection']:
            (root / directory).mkdir()
        frozen = {'Working': publish(working, generated_bytes), 'Frozen': publish(root / 'Frozen' / PART_NAME, generated_bytes)}
        require(set(frozen.values()) == {build['output_sha256']}, 'frozen input copies differ')
        files = {'Frozen/' + PART_NAME: frozen['Frozen']}
        for filename, data in tool_bytes.items():
            files['Tools/' + filename] = publish(root / 'Tools' / filename, data)
        for filename, data in {'Installed.json': checked(installed_path, installed_sha).read_bytes(),
                               'Neutral.json': checked(request, PINNED[request]).read_bytes(), 'Build.json': build,
                               'AppearanceInputs.json': {'owner': 'native part self', 'asset_sha256': installed['asset']['sha256'],
                                                         'rgb': list(RGB), 'roughness': ROUGHNESS}}.items():
            files['Evidence/' + filename] = publish(root / 'Evidence' / filename, data)
    trial = root / 'Trial.json'
    job = {'schema': SCHEMA, 'guest_root': guest(root), 'files_sha256': files, 'controls': controls, 'installed': installed,
           'baseline_sha256': frozen['Frozen'], 'part_name': PART_NAME, 'rgb': list(RGB), 'roughness': ROUGHNESS,
           'radial': {key: radial_trial[key] for key in ('case', 'lights')}, 'prediction_control': prediction['control'],
           'phases': list(PHASES), 'heldout_inputs_read': False, 'source_evidence_only': True,
           'revision': {'writer': WRITER, 'auditor': AUDITOR, 'preparer_sha256': digest(HERE), 'writer_epoch': EPOCH}}
    trial_sha = publish(trial, job)
    prefix = ['prlctl', 'exec', 'Windows 11', '--current-user', runtime['executable'], '-B', guest(root / 'Tools' / observer.name)]
    tail = [guest(trial), trial_sha]
    argv = {'Verify': [*prefix, 'verify', *tail], **{role: [*prefix, 'phase', *tail, role] for role in PHASES},
            'ResetB': [*prefix, 'reset-b', *tail], 'Summary': [*prefix, 'summary', *tail]}
    order = ['Verify', 'ControlBefore', 'AuthorA', 'ReopenA', 'ResetB', 'AuthorB', 'ReopenB', 'ControlAfter', 'Summary']
    recipe_sha = publish(root / 'Recipe.json', {'order': order, 'argv': argv, 'always_run_trailing_control_if_idle': True,
                                              'first_failure_stops_candidate_phases': True, 'trial_sha256': trial_sha})
    return {'packet': str(root), 'trial_sha256': trial_sha, 'recipe_sha256': recipe_sha, 'baseline_sha256': frozen['Frozen'],
            'installed_asset_sha256': installed['asset']['sha256'], 'native_processes_started': 0, 'emitter_reads': build['runtime_io_attempts']}


def f32(value):
    return unpack('<f', pack('<f', value))[0]


def leaves(value, prefix=''):
    if isinstance(value, Mapping):
        return {path: leaf for key, item in value.items() for path, leaf in leaves(item, f'{prefix}.{key}').items()}
    if isinstance(value, (list, tuple)):
        return {path: leaf for index, item in enumerate(value) for path, leaf in leaves(item, f'{prefix}[{index}]').items()}
    if hasattr(value, 'TextValue'):
        value = value.TextValue
    require(value is None or type(value) in (bool, int, str, float), 'unrepresented material leaf: ' + prefix)
    return {prefix.lstrip('.'): value}


def change(a, b):
    return {key: {'A': a.get(key), 'B': b.get(key), 'present': [key in a, key in b]}
            for key in sorted(a.keys() | b.keys()) if key not in a or key not in b or a[key] != b[key]}


def prospective(properties, expected_roughness):
    expected = [f32(channel * f32(1 / 255)) for channel in RGB]
    legacy = properties['f20']
    rv = legacy.get('f90')
    pbr = properties.get('f88')
    pbr_groups = {label: [pbr[f'{offset}_{index}'] for index in range(3)]
                  for label, offset in {'albedo': 'f10', 'attenuation': 'fdc', 'flake': 'f84', 'flip_flop': 'f9c',
                                        'emission': 'fb8'}.items()} if pbr else {}
    return {'packed_legacy_color': properties['f0c'], 'packed_realview_color': None if rv is None else rv['f14'],
            'matching_packed_color': [owner for owner, actual in [('visual.f0c', properties['f0c']),
                                                                  ('realview.f14', None if rv is None else rv['f14'])] if actual == COLOR],
            'realview_id_words': None if rv is None else [rv['f00'], rv['f04']],
            'legacy_roughness': None if rv is None else rv['f74'], 'pbr_roughness': None if pbr is None else pbr['f2c'],
            'matching_roughness': [owner for owner, actual in [('realview.f74', None if rv is None else rv['f74']),
                                                               ('pbr.f2c', None if pbr is None else pbr['f2c'])]
                                   if expected_roughness is not None and actual == expected_roughness],
            'pbr_color_groups': pbr_groups, 'matching_pbr_color_groups': [key for key, actual in pbr_groups.items() if actual == expected]}


def inspect_part(path, wanted, expected_roughness=None):
    from Classes import registry
    from para.concentric.ProveVisualStateStore import owner_clocks, replay
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    archive = SldprtArchive.from_bytes(checked(path, wanted).read_bytes())
    visual, clocks, visual_proof, state, visual_configuration_links = None, [], None, [], []
    if VISUAL in archive.streams:
        visual, visual_proof = replay(archive, registry())
        link, clocks = owner_clocks(archive, visual)
    else:
        link = ReadNativeLink(archive, 0)
    model = link.ConfigValue.RootValue
    roots = model.FieldsValue
    require(model.ClassValue.NameValue == 'moPart_c', 'expected actual part root')
    cmgr = ReadCmgrMut(archive.require('Contents/CMgr'), 19000).RootValue
    config = cmgr.FieldsValue['f360']
    require(config.ClassValue.NameValue == 'moPartConfiguration_c', 'expected real selected part configuration')
    config_fields = config.FieldsValue
    definition = ReadModelDef(archive.require('Contents/Definition'), 19000).GraphValue
    fields = definition.DocumentValue.FieldsValue
    top = ReadHeaderGraph(archive.require('Header2'), 19000)
    config_bytes, config_map = WriteConfigMut(model, 19000, link.ConfigValue.HeaderValue)
    resolved = link.ResolvedValue
    resolved_bytes, _ = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, config_map.MapValue, resolved.ContextValue)
    linked = {'Contents/Config-0': config_bytes, 'Contents/Config-0-ResolvedFeatures': resolved_bytes,
              'Contents/CMgr': WriteCmgrMut(cmgr, 19000), 'Header2': WriteHeadGraph(top, 19000),
              'Contents/Config-0-ModelHeader': WriteHeadGraph(link.ConfigValue.HeaderValue, 19000),
              'Contents/Definition': WriteModelDef(definition).OutputValue}
    require(all(archive.require(name) == body for name, body in linked.items()), 'inexact typed linked replay')
    filekeys = [ReadFileKey(owner.FieldsValue['f38']) for owner in (link.ConfigValue.HeaderValue, top)]
    require(filekeys[0] == filekeys[1], 'two typed self locators disagree')
    manager = fields.get('f1110')
    mgr = {'present': fields['has_pwmaterial']}
    if manager is not None:
        items = manager['list']['items']
        require(len(items) == manager['list']['n'], 'material reference manager count differs')
        mgr |= {'allocator_words': [manager['f08'], manager['f0c']], 'references': len(items),
                'reference_classes': [item['o'].ClassValue.NameValue for item in items]}
    materials = roots.get('f1420')
    density = None if materials is None else materials.FieldsValue['f08']
    physical = {'part_material_class': None if materials is None else materials.ClassValue.NameValue,
                'density_class': None if density is None else density.ClassValue.NameValue,
                'density': None if density is None else density.FieldsValue['f58'], 'configuration_fc50': config_fields['fc50'],
                'material_tree': sorted(name for name in archive.streams if name.casefold().endswith('/materialtree'))}
    properties = {'model': roots.get('f78'), 'selected_configuration': config_fields.get('f78')}
    if visual is not None:
        view = visual.head['root'].f
        state = view['f0f0']
        visual_configuration_links = view['f118']
        holders = [row for row in view['f78'] if row['ref'].cls == 'moCompHolder_c']
        require(len(holders) == 1 and view['n_comps'] == 0 and view['n_ents'] == len(view['f78']), 'unknown non-part holder inventory')
        holder = holders[0]
        shared = holder['ref'].FieldsValue['f58']
        require(shared['owner'] is None and shared['has_ext'] == 0, 'appearance holder refers to an external owner')
        variants = [(attribute['key'], item['o'].FieldsValue['f10']) for attribute in holder['attrs'] for item in attribute['objs']
                    if item['o'] is not None and item['o'].cls == 'visStateVisualPropertiesAttribute_c']
        require(len(variants) == 1 and variants[0][1].cls == 'moVisualProperties_c', 'part self lacks a single typed appearance attribute')
        properties['part_self_visual_state'] = variants[0][1]
        require(len(state) == len(visual_configuration_links) == 1 and variants[0][0] == state[0]['id']
                and visual_configuration_links[0]['key'] == config_fields['f08'], 'part holder state/config joins differ')
    graph = {}
    semantics = {}
    for role, value in properties.items():
        if value is None:
            graph[role] = None
            continue
        graph[role] = leaves({key: field for key, field in value.FieldsValue.items() if key not in ('props',)})
        semantics[role] = prospective(value.FieldsValue, expected_roughness)
    said = {'file_sha256': wanted, 'bytes': path.stat().st_size, 'linked_byte_identity': {key: len(value) for key, value in linked.items()},
            'self_file': list(filekeys[0]), 'physical_material': physical, 'definition_appearance_manager': mgr,
            'appearance': semantics, 'creation_logs': clocks, 'visual_replay': visual_proof, 'visual_states': state,
            'visual_config_links': visual_configuration_links}
    return archive, graph, said


def collect_audit(root, trial_sha, result_sha):
    job = read_json(root / 'Trial.json', trial_sha)
    result = read_json(root / 'Result.json', result_sha)
    require(job['schema'] == result['schema'] == SCHEMA and result['trial_sha256'] == trial_sha and result['passed'] is True
            and result['controls_healthy'] is True and result['native_processes'] == 6 and result['heldout_credit'] == 0
            and result['source_evidence_only'] is True and job['heldout_inputs_read'] is False and job['rgb'] == list(RGB)
            and job['roughness'] == ROUGHNESS and set(result['phases']) == set(PHASES), 'no complete healthy native source trial')
    for role, phase in result['phases'].items():
        row = json.loads((root / 'Inspection' / role / 'Record.json').read_bytes())
        require(row['job'] == {'trial_sha256': trial_sha, 'phase': role} and row['result'] == phase and row['passed'] is True
                and phase['open_errors'] == phase['open_warnings'] == 0, 'native phase receipt differs: ' + role)
    frozen = root / 'Frozen' / PART_NAME
    basis, basis_graph, base_proof = inspect_part(frozen, job['baseline_sha256'])
    require(base_proof['visual_replay'] is None and base_proof['self_file'][1] == guest(root / 'Working' / PART_NAME),
            'fresh neutral baseline unexpectedly has a visual state or another native self locator')
    a, b = (result['phases']['Author' + lane]['saved_sha256'] for lane in ('A', 'B'))
    reset = json.loads((root / 'ResetB.json').read_bytes())
    require(reset == {'trial_sha256': trial_sha, 'before': a, 'after': job['baseline_sha256'], 'native_processes_started': 0}
            and len({a, b, job['baseline_sha256']}) == 3, 'stored same-locator interventions are not independent paired saves')
    ars, graphs, reports = {}, {}, {}
    for lane, expected in (('A', a), ('B', b)):
        cold = result['phases']['Reopen' + lane]['appearance']
        require(cold['same_model_iunknown'] is True and cold['entity_count'] == 1 and cold['primary_color'] == COLOR
                and cold['asset_sha256'] == job['installed']['asset']['sha256'] and cold['roughness'] == ROUGHNESS[lane],
                'native self owner or actual author input differs')
        ars[lane], graphs[lane], reports[lane] = inspect_part(root / 'Inspection' / ('Author' + lane) / PART_NAME,
                                                             expected, ROUGHNESS[lane])
        stored = PureWindowsPath(reports[lane]['self_file'][1])
        require(stored.name == PART_NAME and reports[lane]['visual_replay'] is not None, 'saved part has no typed VisualStates or self locator')
    require(reports['A']['self_file'] == reports['B']['self_file'] and reports['A']['physical_material'] == reports['B']['physical_material']
            and reports['A']['visual_config_links'] == reports['B']['visual_config_links']
            and reports['A']['visual_states'] == reports['B']['visual_states'] and graphs['A'].keys() == graphs['B'].keys(),
            'the contrast changes selected configuration, appearance owners or independent physical identity')
    for key in ('rebuild_geometry',):
        require(result['phases']['ReopenA'][key] == result['phases']['ReopenB'][key], 'comparison changed body, dimensions, lights or actual tree')
    deltas = {role: change(graphs['A'][role] or {}, graphs['B'][role] or {}) for role in graphs['A']}
    streams_changed = sorted(name for name in ars['A'].streams.keys() | ars['B'].streams.keys()
                             if ars['A'].streams.get(name) != ars['B'].streams.get(name))
    require(checked(root / 'Working' / PART_NAME, b).stat().st_size == reports['B']['bytes'], 'final B save changed after fresh reopen')
    return {'schema': SCHEMA, 'trial_sha256': trial_sha, 'result_sha256': result_sha, 'native_source_evidence_only': True,
            'source_evidence': reports, 'paired_appearance_field_delta': deltas, 'paired_stream_delta': streams_changed,
            'physical_equal_between_arms': True, 'generated_baseline': base_proof,
            'baseline_appearance_roles': {key: value is not None for key, value in basis_graph.items()},
            'baseline_streams': sorted(basis.streams), 'expected_f32': [f32(channel * f32(1 / 255)) for channel in RGB],
            'heldout_credit': 0, 'writer_qualified': False}


def audit(arguments):
    with TemporaryDirectory(prefix='kit-child-appearance-auditor-') as scratch:
        scratch = Path(scratch)
        checkout(scratch, AUDITOR, [('src', ()), ('re/tooling/sw2026', ()),
                                    ('tests/Convert/Solidworks/Research', ('ConstructionGuard.py',))])
        local = scratch / HERE.relative_to(REPO)
        publish(local, HERE.read_bytes())
        publish(local.with_name('ObserveChildAppearanceContrast.py'), HERE.with_name('ObserveChildAppearanceContrast.py').read_bytes())
        done = subprocess.run([sys.executable, '-I', '-B', str(local), *arguments], cwd=scratch, stdout=subprocess.PIPE, check=True)
        return json.loads(done.stdout)


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='mode', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('name')
    prep.add_argument('installed', type=Path)
    prep.add_argument('installed_sha256')
    for name in ('audit', '_collect'):
        compare = commands.add_parser(name)
        compare.add_argument('trial', type=Path)
        compare.add_argument('trial_sha256')
        compare.add_argument('result_sha256')
        if name == 'audit':
            compare.add_argument('output', type=Path)
    for name in ('disclosed', '_disclosed'):
        commands.add_parser(name)
    args = parser.parse_args()
    if args.mode == 'prepare':
        value = prepare(args.name, args.installed, args.installed_sha256)
    elif args.mode in ('audit', '_collect'):
        trial = args.trial
        require(trial.name == 'Trial.json' and trial.parent.parent == MANAGED and trial.resolve(strict=True) == trial
                and re.fullmatch(r'ConcentricChildAppearanceContrast[0-9]{2}', trial.parent.name), 'only a managed disclosed trial may be read')
        if args.mode == 'audit':
            require(args.output.parent == trial.parent and args.output.name == 'TypedAudit.json' and not args.output.exists(), 'wrong fresh audit destination')
            value = audit(['_collect', str(trial), args.trial_sha256, args.result_sha256])
            value = {'typed_audit_sha256': publish(args.output, value), 'path': str(args.output)}
        else:
            value = collect_audit(trial.parent, args.trial_sha256, args.result_sha256)
    elif args.mode == 'disclosed':
        value = audit(['_disclosed'])
    else:
        value = {role: inspect_part(path, wanted)[2] for role, (path, wanted) in EXTERNAL.items()}
    print(json.dumps(value, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
