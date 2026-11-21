from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
ORACLE_ROOT = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover')
REFERENCE = ORACLE_ROOT / 'RadialConcentric01'
REQUEST = ORACLE_ROOT / 'ConcentricRadialIntent01/IndependentRequest.json'
STANDALONE = REQUEST.parent / 'NativePacket01/Result.json'
REFERENCE_EPOCH = 1795121000
REFERENCE_TRIAL = '5d7680db342c5c7e037313d0a2bc3e02820b1d21dfcbdad5cd77293430d32d01'
REFERENCE_RESULT = '3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03'
REFERENCE_FILES = {
    'parent': '9474ca54466a450eec3ba5e49703053fe160e0a221647b2bcc984d8d3672dc74',
    'child': '699be1addf4b644f1ebdeecc6862f65610155d294e10fa6d7cbcf3d6a224f1cd',
}
NAMES = {'parent': 'RadialConcentricProbe.SLDASM', 'child': 'DisclosedRadialSceneProbe.SLDPRT'}
STATES = (
    ('Display State-1', (1, 1)),
    ('Left occurrence only', (1, 0)),
    ('Right occurrence only', (0, 1)),
)
PHASES = ('ControlBefore', 'Baseline', 'Generated', 'Reopen', 'ControlAfter')
SCHEMA = 'kit.sw2026.radial-concentric-parent-visibility.v1'
DISPLAY_MODES = ('both', 'xml-only', 'store-only')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checksum(data):
    return sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def publish(path, data):
    with path.open('xb') as stream:
        stream.write(data)
    return checksum(data)


def prepare(name, revision, written_at, display_mode):
    import subprocess
    import tarfile
    from tempfile import TemporaryDirectory

    require(re.fullmatch(r'RadialConcentricDisplay[0-9]{2}', name), 'use a fresh RadialConcentricDisplayNN packet')
    require(re.fullmatch(r'[0-9a-f]{40}', revision), 'pin a full construction commit')
    require(REFERENCE_EPOCH < written_at <= 0xffffffff, 'supply one fresh authored epoch for both lanes')
    require(display_mode in DISPLAY_MODES, 'select one exact display-store experiment')
    require(not (ORACLE_ROOT / name).exists() and (ORACLE_ROOT / name).resolve() == ORACLE_ROOT / name,
            'the host packet must be fresh and unredirected')
    subprocess.run(['git', 'merge-base', '--is-ancestor', revision, 'HEAD'], cwd=REPO, check=True)
    with TemporaryDirectory(prefix='kit-radial-visibility-') as directory:
        root = Path(directory)
        archive = root / 'source.tar'
        for tree, selected in (('src', ()), ('re/tooling/sw2026', ()),
                               ('re/solidworks/inputs', ('ConcentricFeatureNeutral01.json',))):
            subprocess.run(['git', 'archive', '--output', str(archive), '--prefix=' + tree + '/',
                            f'{revision}:{tree}', *selected], cwd=REPO, check=True)
            with tarfile.open(archive) as source:
                source.extractall(root, filter='data')
        tool = root / HERE.relative_to(REPO)
        operator = HERE.read_bytes()
        if tool.exists():
            require(tool.read_bytes() == operator, 'the committed operator differs from the launch tool')
        else:
            publish(tool, operator)
        entry = 'import runpy, sys; runpy.run_path(sys.argv[1])["construct"](sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5])'
        completed = subprocess.run(
            [sys.executable, '-I', '-B', '-c', entry, str(tool), name, revision, str(written_at), display_mode], cwd=root
        )
        return completed.returncode


def guarded_case(radial, document, child, scene, lights, locator, written_at, registry, *, display):
    from dataclasses import replace

    from para.concentric.MakeDisplayTree import DisplayListIntent, DisplayStateIntent, make_display_tree
    from para.concentric.MakeVisualStateStore import STREAM, make_visual_store
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream

    emit = radial.EmitAsmStreams
    emit_proof = []

    def build(state, part, metadata, headers, references, mates):
        shared = emit(state, part, metadata, headers, references, mates)
        require(state.ManagerValue.FieldsValue['f1f8'] == '', 'CMgr must retain the shared empty locator policy')
        ids = tuple(node.FieldsValue['f08'] for node in references)
        config = state.CurrentConfig.FieldsValue['f08']
        require(len(ids) == len(set(ids)) == 2 and STREAM not in shared.StreamsValue
                and KComponentTreeStream in shared.StreamsValue, 'the actual flat generated parent must own this intervention')
        emit_proof.append((config, ids))
        if not display:
            return shared
        intent = DisplayListIntent(config, tuple(
            DisplayStateIntent(name, tuple(zip(ids, map(bool, vector), strict=True))) for name, vector in STATES
        ))
        extra = {}
        if display in ('both', 'xml-only'):
            extra[KComponentTreeStream] = make_display_tree(state, headers[0], part, references, intent)
        if display in ('both', 'store-only'):
            with registry.track_usage('store', STREAM) as usage:
                extra[STREAM] = make_visual_store(state, headers, references, intent, registry)
            report = usage.snapshot()
            require(report['completed'] and not report['raw_operations'] and not report['missing_schemas'],
                    'the new parent store must have complete typed generation')
        return replace(shared, StreamsValue=shared.StreamsValue | extra)

    radial.EmitAsmStreams = build
    try:
        files, proof = radial.guarded_bundle(document, child, scene, lights, locator, written_at)
    finally:
        radial.EmitAsmStreams = emit
    require(len(emit_proof) == 2 and emit_proof[0] == emit_proof[1] and proof['runtime_io_attempts'] == 0,
            'the complete two-build write and owner proof must be stable without runtime reads')
    return files, proof, emit_proof[0]


def linked_proof(parent, child, paths, written_at, ids):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, ReadRows, RequireNode
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    links = {}
    for role, archive, kind in (('parent', parent, 3), ('child', child, 2)):
        link = ReadNativeLink(archive, 0)
        model_header = link.ConfigValue.HeaderValue.FieldsValue
        header2 = ReadHeaderGraph(archive.require('Header2'), 19000).FieldsValue
        self_file = ReadFileKey(model_header['f38'])
        expected = (Path(NAMES[role]).stem, paths[role], kind, written_at)
        require(self_file == ReadFileKey(header2['f38']) == expected and model_header['f40'] == header2['f40'],
                'both native headers must encode the exact owned final file and update stamp')
        manager = ReadCmgrMut(archive.require('Contents/CMgr'), 19000).RootValue
        require(manager.FieldsValue['f1f8'] == '', 'the fresh ordinary files use a fixed empty CMgr locator')
        links[role] = (link, self_file, model_header['f40'])
    model = links['parent'][0].ConfigValue.RootValue
    refs = tuple(RequireNode(row['o'], 'moReference_c') for row in ReadRows(model.FieldsValue['f68']['list']['items']))
    require(tuple(ref.FieldsValue['f08'] for ref in refs) == ids and all(
        ReadFileKey(ref.FieldsValue['f3b0']) == links['child'][1] and ref.FieldsValue['f3e0'] == links['child'][2]
        for ref in refs), 'parent occurrence file identity or child update stamp differs')
    require(refs[0].FieldsValue['f3b0'] is refs[1].FieldsValue['f3b0'], 'references lost their shared child file owner')
    proof = {role: {'file_key': key, 'update_stamp': stamp} for role, (_, key, stamp) in links.items()}
    proof['occurrences'] = [[ref.FieldsValue['f08'], ReadNodeName(ref)] for ref in refs]
    return proof


def display_proof(base, parent, registry, configuration, ids, parent_locator):
    from xml.etree.ElementTree import tostring

    from defs.Visual import load_visual_states, store_visual_states
    from para.concentric.MakeDisplayTree import PREFIX
    from para.concentric.MakeVisualStateStore import STREAM
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm, XmlRoot
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    original = XmlRoot(base.require(KComponentTreeStream))
    tree = XmlRoot(parent.require(KComponentTreeStream))
    (config,) = tree.iter(f'{PREFIX}swConfiguration')
    (listing,) = config.findall(f'{PREFIX}swDisplayStateList')
    require(config.get('swID') == str(configuration)
            and listing.get('swCompNameList') == ''.join(f'{value},' for value in ids),
            'XML display list lost its actual configuration and occurrence joins')
    expected = [(name, ''.join('Yes,' if val else 'No,' for val in vector)) for name, vector in STATES]
    native = DecodeNativeAsm(parent)
    require([(row.name, dict(row.attributes)['swShowState']) for row in native.display_states] == expected
            and native.display_owner is None, 'the scoped XML rows differ or the existing public gate changed')
    leaf_ids = [int(listing.get('id')), *(row.object_id for row in native.display_states)]
    first_id = int(original.get('swObjCount')) + 1
    require(leaf_ids == list(range(first_id, first_id + len(STATES) + 1))
            and tree.get('swObjCount') == str(leaf_ids[-1]), 'XML list and leaf ids are not allocated after the actual existing tree')
    config.remove(listing)
    tree.set('swObjCount', original.get('swObjCount'))
    require(tostring(tree) == tostring(original), 'the XML changed outside its authored display list and calculated object count')
    data = parent.require(STREAM)
    with registry.track_usage('load', STREAM, sources=parent.streams) as load:
        doc, reader = load_visual_states(data, registry)
    with registry.track_usage('store', STREAM) as store:
        repeated = store_visual_states(doc, registry)
    reports = [load.snapshot(), store.snapshot()]
    require(repeated == data and not doc.tail and all(
        report['completed'] and not report['raw_operations'] and not report['missing_schemas'] for report in reports
    ), 'typed VisualStates store failed complete exact replay')
    fields = doc.head['root'].f
    keys = list(range(1, len(STATES) + 1))
    require(fields['f118'] == [{'key': configuration, 'value': 1, 'one': 1}]
            and [(row['id'], row['name']) for row in fields['f0f0']] == list(zip(keys, (name for name, _ in STATES)))
            and (fields['n_comps'], fields['n_ents'], fields['n_f88'], fields['n']) == (2, 3, 0, 0),
            'VisualStates lost its actual configuration, display keys or complete member counts')
    visual_members = []
    for row in fields['comps']:
        context = row['comp'].f
        chain = context['f20'].f
        (target,) = chain['f08'].f['f08']
        feature = target['o'].f
        feature_id = feature['f44']
        file = context['f40'].f
        actions = []
        require(file['f58'] == 0 and ReadFileText(file['shared']['h18']) == parent_locator
                and file['shared']['h18'] is feature['f10']['h18'], 'VisualStates detached owner lost its generated parent locator')
        for key, attr in zip(keys, row['attrs'], strict=True):
            _, visual, _ = (member['o'] for member in attr['objs'])
            require(attr['key'] == key and attr['k'] == 3, 'VisualStates component attribute keys differ')
            actions.append(visual.f['f10'])
        require(actions == [vector[ids.index(feature_id)] for _, vector in STATES], 'VisualStates action differs from its same-ID XML row')
        visual_members.append([feature_id, actions])
    require([row[0] for row in visual_members] == list(reversed(ids)), 'VisualStates occurrence order differs')
    link = ReadNativeLink(parent, 0)
    header = link.ConfigValue.HeaderValue
    top = ReadHeaderGraph(parent.require('Header2'), 19000)
    planes = [row.FieldsValue['f08'] for row in link.ResolvedValue.RootsValue if row.ClassValue.NameValue == 'moRefPlane_c']
    observed_planes = [(row['ref'].f['ff0']['f00'], row['ref'].f['ff0']['f08']) for row in fields['f78']]
    require(len(planes) == 3 and [key for key, _ in observed_planes] == list(reversed(planes))
            and all(DatumTime(header, key) == DatumTime(top, key) == stamp for key, stamp in observed_planes),
            'VisualStates persistent plane ids or actual creation-log times differ')
    return {'xml_leaf_ids': leaf_ids, 'configuration': [configuration, config.get('swName')],
            'xml_states': expected, 'visual_keys': keys, 'visual_occurrences': visual_members,
            'visual_planes': observed_planes, 'visual_terminal_map': reader.count,
            'visual_byte_identity': True, 'visual_opaque_operations': 0,
            'provisional_schemas': sorted({name for report in reports for name in report['provisional_schemas']}),
            'sdk_raw_xml_rows': True, 'sdk_multi_state_public_owner': False}


def construct(name, revision, written_at, display_mode):
    sys.path.insert(0, str(HERE.parent))
    import PrepareRadialConcentric as radial
    from Classes import registry
    from PrepareConcentricDisplayOracle import CONTROLS, SOURCE, checked, guest
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    from para.concentric.MakeVisualStateStore import STREAM

    old = json.loads(checked(REFERENCE / 'Trial.json', REFERENCE_TRIAL))
    result = json.loads(checked(REFERENCE / 'Result.json', REFERENCE_RESULT))
    require(result['packet_sha256'] == REFERENCE_TRIAL and result['passed'] and result['controls_healthy']
            and result['distinct_native_processes'] == 4 and old['heldout_inputs_read'] == 0
            and old['working_names'] == NAMES and old['generated_sha256'] == REFERENCE_FILES,
            'the exact previously accepted generated radial fixture is required')
    for role, expected in REFERENCE_FILES.items():
        checked(REFERENCE / 'Frozen' / NAMES[role], expected)
    controls = {role: radial.input_row(SOURCE / basename, expected) for role, (basename, expected) in CONTROLS.items()}
    require(controls == old['controls'], 'the exact disclosed D01 controls are required')
    request = json.loads(checked(REQUEST, radial.REQUEST))
    standalone = json.loads(checked(STANDALONE, radial.STANDALONE))
    child = radial.FromData(request['child'])
    case = next(row for row in radial.disclosed_cases() if row['id'] == 'D01')
    document = radial.author_parent(child, case)
    prior_prediction = json.loads(checked(REFERENCE / 'Evidence/Prediction.json', old['files_sha256']['Evidence/Prediction.json']))
    prediction = radial.predict(document, case, prior_prediction['control'], standalone)
    require(standalone['passed'] and prediction == prior_prediction, 'independent radial prediction changed')
    neutral = {'document': radial.ToData(document), 'lighting': request['lights']}
    require(neutral == json.loads(checked(REFERENCE / 'Evidence/Neutral.json', old['files_sha256']['Evidence/Neutral.json'])),
            'neutral geometry, placements, mate or light intent differs from the accepted fixture')
    reg = registry()
    original, original_proof, owner = guarded_case(
        radial, document, child, request['environment_name'], radial.read_intents(request['lights'], REFERENCE_EPOCH),
        guest(REFERENCE / 'Working' / NAMES['parent']), REFERENCE_EPOCH, reg, display=None,
    )
    require({role: checksum(data) for role, data in original.items()} == REFERENCE_FILES,
            'neutral reconstruction of the previously accepted fixed radial fixture changed bytes')
    require(owner == (0, tuple(row['native_id'] for row in result['phases']['Generated']['rebuilt']['occurrences'])),
            'actual prior native occurrence owners differ from the regenerated fixed fixture')
    root = ORACLE_ROOT / name
    require(re.fullmatch(r'RadialConcentricDisplay[0-9]{2}', root.name) and root.resolve() == root and not root.exists(),
            'the private managed packet has to be fresh')
    paths = {role: guest(root / 'Working' / basename) for role, basename in NAMES.items()}
    args = (radial, document, child, request['environment_name'], radial.read_intents(request['lights'], written_at),
            paths['parent'], written_at, reg)
    baseline, base_proof, base_owner = guarded_case(*args, display=None)
    complete_variant, complete_proof, complete_owner = guarded_case(*args, display='both')
    variant, variant_proof, variant_owner = (
        (complete_variant, complete_proof, complete_owner)
        if display_mode == 'both' else guarded_case(*args, display=display_mode)
    )
    require(base_owner == owner == variant_owner and variant_proof == base_proof
            and baseline['child'] == variant['child'], 'display intent changed the linked body, part or mate proof')
    left, right, linked = (SldprtArchive.from_bytes(payload) for payload in (baseline['parent'], variant['parent'], baseline['child']))
    full = SldprtArchive.from_bytes(complete_variant['parent'])
    require(complete_owner == base_owner and complete_proof == base_proof and complete_variant['child'] == baseline['child'],
            'complete control changed the paired neutral proof')
    before, after = left.streams, right.streams
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = {'both': {KComponentTreeStream, STREAM}, 'xml-only': {KComponentTreeStream}, 'store-only': {STREAM}}
    require(changed == expected[display_mode] and after.keys() - before.keys() == ({STREAM} & changed)
            and all(after[key] == full.require(key) for key in changed)
            and STREAM not in linked.streams, 'the trial may change only parent XML and parent VisualStates')
    links = linked_proof(left, linked, paths, written_at, owner[1])
    require(links == linked_proof(right, linked, paths, written_at, owner[1]), 'the two parents do not identify the same child')
    display = display_proof(left, full, reg, *owner, paths['parent'])
    hashes = {role: checksum(data) for role, data in variant.items()}
    baseline_hash = checksum(baseline['parent'])
    proof = {'schema': SCHEMA, 'revision': revision, 'preparer_sha256': checksum(HERE.read_bytes()),
             'reference_trial_sha256': REFERENCE_TRIAL, 'reference_result_sha256': REFERENCE_RESULT,
             'reference_archive_sha256': REFERENCE_FILES, 'reference_explicit_epoch': REFERENCE_EPOCH,
             'reference_rebuilt_exactly': True, 'authored_epoch': written_at, 'architecture': 'ordinary flat concentric/four-light radial',
             'native_processes_started': 0, 'heldout_inputs_read': 0, 'runtime_io_attempts': 0,
             'display_mode': display_mode, 'guarded_builds': 6 if display_mode == 'both' else 8,
             'baseline_sha256': baseline_hash, 'variant_sha256': hashes, 'same_final_links': links,
             'manager_locator': '', 'child_visual_states_present': False, 'source_request_sha256': radial.REQUEST,
             'changed_parent_streams': {key: {'before': len(before.get(key, b'')), 'after': len(after[key]),
                                                 'baseline_sha256': checksum(before[key]) if key in before else None,
                                                 'variant_sha256': checksum(after[key])} for key in sorted(changed)},
             'same_parent_stream_sha256': {key: checksum(before[key]) for key in sorted(before.keys() - changed)},
             'display': display, 'shared_assembly_proof': base_proof, 'reference_proof': original_proof}
    tools = {path: checked(REFERENCE / path, wanted) for path, wanted in old['files_sha256'].items() if path.startswith('Tools/')}
    tools.update({f'Tools/{HERE.name}': HERE.read_bytes(),
                  'Tools/ObserveConcentricDisplayOracle.py': HERE.with_name('ObserveConcentricDisplayOracle.py').read_bytes()})
    runtime = checked(REFERENCE / 'Evidence/GuestPython.json', old['files_sha256']['Evidence/GuestPython.json'])
    root.mkdir(mode=0o700)
    for folder in ('Tools', 'Evidence', 'OldBranch', 'Frozen', 'Working', 'Inspection'):
        (root / folder).mkdir()
    frozen_paths = tools | {'Evidence/GuestPython.json': runtime, 'Evidence/Prediction.json': canonical(prediction),
                            'Evidence/Neutral.json': canonical(neutral), 'Evidence/Build.json': canonical(proof),
                            f'OldBranch/{NAMES["parent"]}': baseline['parent']}
    file_hashes = {relative: publish(root / relative, payload) for relative, payload in frozen_paths.items()}
    for role, basename in NAMES.items():
        publish(root / 'Frozen' / basename, variant[role])
        publish(root / 'Working' / basename, baseline[role])
    job = dict(old, controls=controls, files_sha256=file_hashes, generated_sha256=hashes,
               display_trial_schema=SCHEMA, native_phases=list(PHASES), baseline_parent_sha256=baseline_hash,
               guest_root=guest(root), authored_states=STATES, occurrence_ids=owner[1], revision=revision,
               manager_locator_policy='ordinary empty f1f8 in both', display_mode=display_mode)
    trial = publish(root / 'Trial.json', canonical(job))
    prefix = ['prlctl', 'exec', 'Windows 11', '--current-user', json.loads(runtime)['executable'], '-B', guest(root / 'Tools' / HERE.name)]
    tail = [guest(root / 'Trial.json'), trial]
    argv = {'Verify': [*prefix, 'verify', *tail],
            **{role: [*prefix, 'phase', *tail, role] for role in PHASES},
            'SelectVariant': [*prefix, 'select-variant', *tail], 'Summary': [*prefix, 'summary', *tail]}
    order = ['Verify', 'ControlBefore', 'Baseline', 'SelectVariant', 'Generated', 'Reopen', 'ControlAfter', 'Summary']
    recipe = {'argv': argv, 'ordered_steps': order, 'trial_sha256': trial, 'maximum_native_launches': len(PHASES),
              'stop_candidate_steps_after_first_failure': True, 'always_run_trailing_control_if_idle': True,
              'host_wait_limit_seconds': dict(zip(order, (30, 150, 150, 30, 240, 180, 150, 30), strict=True))}
    recipe_hash = publish(root / 'Recipe.json', canonical(recipe))
    print(json.dumps({'packet': str(root), 'trial_sha256': trial, 'recipe_sha256': recipe_hash,
                      'build_sha256': file_hashes['Evidence/Build.json'], 'baseline_sha256': baseline_hash,
                      'variant_sha256': hashes, 'native_processes_started': 0, 'heldout_inputs_read': 0}, sort_keys=True))


def guest_mode(command, packet, expected, role):
    import ObserveConcentricDisplayOracle as display
    import ObserveConcentricPersistence as persistence
    from ConcentricNativeContract import checked, digest, signature

    root = packet.resolve().parent
    job, _ = persistence.verify(packet, expected)
    persistence.ensure_runtime(root)
    require(HERE.parent == root / 'Tools' and packet.name == 'Trial.json' and job['display_trial_schema'] == SCHEMA
            and Path(job['guest_root']).resolve() == root and job['native_phases'] == list(PHASES)
            and job['working_names'] == NAMES and job['manager_locator_policy'] == 'ordinary empty f1f8 in both'
            and job['display_mode'] in DISPLAY_MODES
            and job['authored_states'] == json.loads(json.dumps(STATES)), 'different frozen visibility trial')
    parent, child = persistence.working_paths(root, job)
    original = checked(root / 'OldBranch' / parent.name, job['baseline_parent_sha256'])
    preflight = root / 'Inspection/Verification.json'
    selection = root / 'Inspection/VariantSelection.json'
    variant = root / 'Frozen' / parent.name
    have_baseline = {'parent': job['baseline_parent_sha256'], 'child': job['generated_sha256']['child']}
    initial_variant = job['generated_sha256']
    custody = {'packet_sha256': expected, 'locator': str(parent), 'baseline': have_baseline, 'variant': initial_variant}

    def baseline_paths(root_arg, job_arg, prior=None):
        require(root_arg == root and job_arg == job and prior is None and not selection.exists(),
                'the baseline must use the original owned working pair')
        return checked(parent, have_baseline['parent']), checked(child, have_baseline['child'])

    if command == 'verify':
        require(not preflight.exists(), 'the packet verification is single use')
        baseline_paths(root, job)
        api = display.metadata()
        baseline_paths(root, job)
        publish(preflight, canonical({'custody': custody, 'api': api, 'native_launches': 0}))
        return True
    if command == 'select-variant':
        require(not selection.exists() and not any((root / 'Inspection' / name).exists() for name in PHASES[2:]),
                'this fixed-locator selector is single use')
        display.previous(root, expected, 'ControlBefore')
        display.previous(root, expected, 'Baseline')
        baseline_paths(root, job)
        import Swapp

        Swapp.sweep()
        new = checked(variant, initial_variant['parent']).read_bytes()
        pending = parent.with_suffix('.SLDASM.pending')
        publish(pending, new)
        baseline_paths(root, job)
        pending.replace(parent)
        persistence.verify_working(root, job)
        publish(selection, canonical(custody))
        return True
    if command == 'summary':
        phases = {phase: persistence.phase_record(root, expected, phase) for phase in PHASES}
        complete = all(row and row['passed'] for row in phases.values())
        births = [row['oracle_identity']['process_creation_filetime'] for row in phases.values() if row and 'oracle_identity' in row]
        first, last = (phases[phase] for phase in ('ControlBefore', 'ControlAfter'))
        controls = bool(first and first['passed'] and last and last['passed']
                        and signature(first['rebuilt']) == signature(last['rebuilt'])
                        and first['oracle_identity']['process_creation_filetime'] < last['oracle_identity']['process_creation_filetime'])
        baseline = phases['Baseline']
        candidate = phases['Generated']
        contrast = bool(complete and selection.is_file() and json.loads(selection.read_bytes()) == custody
                        and signature(baseline['rebuilt']) == signature(candidate['initial'])
                        and baseline['child_stamp_on_open'] == candidate['child_stamp_on_open']
                        and baseline['initial']['link_display_states_to_configurations'] is candidate['initial']['link_display_states_to_configurations']
                        and all('display' in phases[phase][point] for phase, points in
                                (('Generated', ('initial', 'rebuilt', 'edited', 'saved_state')), ('Reopen', ('initial', 'rebuilt')))
                                for point in points))
        if complete:
            persistence.verify_working(root, job, phases['Generated'])
        passed = bool(controls and contrast and len(births) == len(PHASES)
                      and all(a < b for a, b in zip(births, births[1:])))
        report = {'schema': SCHEMA, 'packet_sha256': expected, 'passed': passed, 'controls_healthy': controls,
                  'display_mode': job['display_mode'],
                  'same_locator_baseline_and_variant': contrast, 'distinct_native_processes': len(set(births)),
                  'numeric_checks': sum(row.get('numeric_checks', 0) for row in phases.values() if row),
                  'heldout_acceptance': False, 'source_appearance_acceptance': False, 'phases': phases}
        publish(root / 'Result.json', canonical(report))
        return passed
    require(command == 'phase' and role in PHASES, 'expected one frozen phase')
    if role != 'ControlAfter':
        require(preflight.is_file() and not preflight.is_symlink() and json.loads(preflight.read_bytes())['custody'] == custody,
                'verified preflight custody is required')
    if role == 'ControlBefore':
        baseline_paths(root, job)
    original_capture = persistence.capture
    original_working = persistence.verify_working
    if role == 'Baseline':
        display.previous(root, expected, 'ControlBefore')
        persistence.verify_working = baseline_paths
    elif role in {'Generated', 'Reopen'}:
        require(selection.is_file() and json.loads(selection.read_bytes()) == custody, 'the controlled same-locator swap is required')
        display.previous(root, expected, 'Baseline')

    if role in {'Baseline', 'Generated', 'Reopen'}:
        def capture(author, model, assembly, child_path, prediction, edited):
            state, resolved = original_capture(author, model, assembly, child_path, prediction, edited)
            occurrences = {row['name']: row for row in state['occurrences']}
            require([row['native_id'] for row in occurrences.values()] == job['occurrence_ids'],
                    'the native display experiment changed either generated occurrence identity')
            state['native_parent_path'] = str(author.get(model, 'GetPathName'))
            state['native_child_path'] = str(author.get(resolved, 'GetPathName'))
            require(display.same_file(state['native_parent_path'], parent) and display.same_file(state['native_child_path'], child),
                    'the native phase must use the identical actual parent and child locators')
            config = author.typed(author.get(model, 'GetActiveConfiguration'), 'Configuration')
            require(str(author.get(config, 'Name')) == prediction['parent_configuration'], 'wrong native display configuration')
            manager = author.typed(author.get(model, 'ConfigurationManager'), 'ConfigurationManager')
            link = author.get(manager, 'LinkDisplayStatesToConfigurations')
            require(type(link) is bool, 'the native configuration display-link flag must be explicit')
            state['link_display_states_to_configurations'] = link
            if role != 'Baseline':
                state['display'] = display.read_states(author, model, config, assembly, child_path, occurrences, STATES, tuple(reversed(STATES[1:])))
                require(author.get(manager, 'LinkDisplayStatesToConfigurations') is link, 'display inspection changed the link policy')
            return state, resolved

        persistence.capture = capture
    try:
        passed = persistence.run_phase(packet, expected, role)
    finally:
        persistence.capture = original_capture
        persistence.verify_working = original_working
    if role in {'ControlBefore', 'Baseline'}:
        baseline_paths(root, job)
    require(digest(original) == have_baseline['parent'], 'the immutable generated baseline changed')
    return passed


def main():
    parser = argparse.ArgumentParser(description='Freeze or observe one disclosed generated radial display-state discriminator')
    parser.add_argument('command', choices=('prepare', 'verify', 'phase', 'select-variant', 'summary'))
    parser.add_argument('target')
    parser.add_argument('pin')
    parser.add_argument('value', nargs='?')
    parser.add_argument('--display-component', choices=DISPLAY_MODES, default='both')
    args = parser.parse_args()
    if args.command == 'prepare':
        require(os.name == 'posix' and args.value is not None, 'host construction requires a name, commit and authored epoch')
        return prepare(args.target, args.pin, int(args.value), args.display_component)
    require(os.name == 'nt', 'observation requires the root-owned Windows guest')
    passed = guest_mode(args.command, Path(args.target), args.pin, args.value)
    print(json.dumps({'passed': passed, 'role': args.value}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
