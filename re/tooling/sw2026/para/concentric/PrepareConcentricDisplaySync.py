from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys

from PrepareConcentricDisplayOracle import ORACLE_ROOT, REPO, checked, guest, json_bytes, publish


SOURCE = ORACLE_ROOT / 'ConcentricDisplayVisibility04'
SOURCE_TRIAL = 'eace2beb513a3f02ba7a053a6622a1d793f12f55f288e9cc9a675c9b41daa048'
SOURCE_AUTHOR = '8f550dd1a668f917d3186955f5cd242cb8cf0a08f0ffd97c98e9e527617af1ed'
SOURCE_RESULT = 'de275b71e12453fcd4a3454a49806ac50865634d2cbbe6662071ff0c6f4de19f'
AUDIT_RECEIPT = '1b008f32adcaaadd61a1d072ae3a012f8136418a5a6a9fe51b8fc65c2228587a'
AUDIT_TOOL = '3a56ec15756bda01f1ec15cad630954e60bbbbbbcdf9e89f2ddde1dbaf915346'
SCHEMA = 'kit.sw2026.concentric-display-child-cut.v1'
OBSERVER = 'ObserveConcentricDisplaySync.py'
BOOT = {'preflight': ['preflight'], 'ControlBefore': ['control', 'before'], 'Author': ['author'],
        'ControlAfter': ['control', 'after']}
COLD = {'StageStale': ['stage', 'stale'], 'Stale': ['observe', 'stale'],
        'StageSynchronized': ['stage', 'synchronized'], 'Synchronized': ['observe', 'synchronized'],
        'ControlAfter': ['control', 'after'], 'summary': ['summary']}


def require(proof, message):
    if not proof:
        raise ValueError(message)


def guest_argv(root, trial_sha, commands, gate_sha=None):
    python = json.loads((root / 'Evidence/GuestPython.json').read_bytes())['executable']
    prefix = ['prlctl', 'exec', 'Windows 11', '--current-user', python, '-B', guest(root / 'Tools' / OBSERVER)]
    trial = [guest(root / 'Trial.json'), trial_sha]
    return {label: [*prefix, *flags, *trial, *([gate_sha] if gate_sha is not None and flags[0] != 'control' else [])]
            for label, flags in commands.items()}


def prepare(name):
    require(re.fullmatch(r'ConcentricDisplaySync[0-9]{2}', name), 'use a new ConcentricDisplaySyncNN directory')
    root = ORACLE_ROOT / name
    require(not root.exists() and root.resolve() == root, 'the fresh private packet directory is required')
    trial = json.loads(checked(SOURCE / 'Trial.json', SOURCE_TRIAL))
    author = json.loads(checked(SOURCE / 'Inspection/Author/Record.json', SOURCE_AUTHOR))['result']
    result = json.loads(checked(SOURCE / 'Result.json', SOURCE_RESULT))
    evidence = json.loads(checked(REPO / 're/solidworks/measurements/2026/ConcentricDisplayAuthoring04.json', AUDIT_RECEIPT))
    require(result['controls_healthy'] and result['packet_sha256'] == SOURCE_TRIAL and result['phases']['Author'] == author
            and author['passed'] and author['saved']['status'] == [True, 0, 0] and result['phases']['Observe']['open_status'] == [0, 32]
            and evidence['child_file_stamps']['update_stamp'] == 134 and evidence['child_reference_stamps'] == [148, 162]
            and trial['heldout_inputs_read'] == 0, 'the exact disclosed author, failed cold opener and basic stamp evidence are required')
    for owner in trial['controls'].values():
        checked(Path(owner['host_path']), owner['sha256'])
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    files = {relative: checked(SOURCE / relative, checksum) for relative, checksum in trial['files_sha256'].items()}
    files[f'Tools/{OBSERVER}'] = Path(__file__).resolve().with_name(OBSERVER).read_bytes()
    root.mkdir(mode=0o700)
    for name in ('Evidence', 'Tools', 'Working', 'Inspection', 'Revisions', 'Revisions/Stale', 'Revisions/Synchronized'):
        (root / name).mkdir()
    trial.update(guest_root=guest(root), preparation_head=head, sync_from_trial_sha256=SOURCE_TRIAL,
                 sync_author_receipt_sha256=SOURCE_AUTHOR, sync_audit_receipt_sha256=AUDIT_RECEIPT,
                 sync_host_tool_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                 files_sha256={relative: publish(root, relative, data) for relative, data in sorted(files.items())})
    trial_sha = publish(root, 'Trial.json', json_bytes(trial))
    recipe = {'trial_sha256': trial_sha, 'ordered_first_steps': ['preflight', 'ControlBefore', 'Author', 'HostStampGate'],
              'argv': guest_argv(root, trial_sha, BOOT),
              'host_stamp_gate_argv': [sys.executable, '-B', str(Path(__file__).resolve()), 'gate', str(root / 'Trial.json'), trial_sha],
              'trailing_control_argv_available_after_any_native_failure_if_idle': True,
              'max_native_launches': 5, 'host_wait_limit_seconds': {'preflight': 30, 'ControlBefore': 150, 'Author': 240,
                                                                     'HostStampGate': 40, 'ControlAfter': 150}}
    recipe_sha = publish(root, 'Recipe.json', json_bytes(recipe))
    return {'packet': str(root), 'trial_sha256': trial_sha, 'recipe_sha256': recipe_sha, 'native_launches': 0, 'heldout_inputs_read': 0}


def stamp_gate(packet, trial_sha):
    trial = json.loads(checked(packet, trial_sha))
    root = packet.parent
    require(root.parent == ORACLE_ROOT and re.fullmatch(r'ConcentricDisplaySync[0-9]{2}', root.name)
            and packet.name == 'Trial.json' and guest(root) == trial['guest_root']
            and trial['sync_from_trial_sha256'] == SOURCE_TRIAL and trial['heldout_inputs_read'] == 0
            and trial['sync_host_tool_sha256'] == sha256(Path(__file__).read_bytes()).hexdigest(), 'require the original stamp-gate closure')
    require(not (root / 'Gate.json').exists() and not (root / 'ColdRecipe.json').exists(), 'host gate already used')
    for relative, checksum in trial['files_sha256'].items():
        checked(root / relative, checksum)
    for owner in trial['controls'].values():
        checked(Path(owner['host_path']), owner['sha256'])
    receipts = {}
    for role in ('Preflight', 'ControlBefore', 'Author'):
        data = (root / 'Inspection' / role / 'Record.json').read_bytes()
        phase = json.loads(data)
        require(phase['job'] == {'phase': role, 'packet_sha256': trial_sha} and phase['passed'], f'{role} must pass first')
        receipts[role] = (phase['result'], sha256(data).hexdigest())
    author, author_sha = receipts['Author']
    require(author['preflight_sha256'] == receipts['Preflight'][1] and receipts['ControlBefore'][0]['open_status'] == [0, 0]
            and author['open_status'] == [0, 0] and author['saved']['status'] == [True, 0, 0]
            and author['child_save_status'] == [True, 0, 0] and author['immutable_inputs_unchanged'], 'author custody or save status differs')
    names = trial['working_names']
    fixed = {'parent': root / 'Revisions' / names['parent'], 'Stale': root / 'Revisions/Stale' / names['child'],
             'Synchronized': root / 'Revisions/Synchronized' / names['child']}
    hashes = author['revision_sha256']
    data = {key: checked(path, hashes[key]) for key, path in fixed.items()}
    require(hashes['parent'] == author['saved']['files_sha256']['parent']
            and hashes['Stale'] == author['saved']['files_sha256']['child'] == trial['controls']['child']['sha256']
            and hashes['Stale'] != hashes['Synchronized'], 'the original parent and two distinct owned revisions must be intact')
    working_parent, working_child = (root / 'Working' / names[side] for side in ('parent', 'child'))
    checked(working_parent, hashes['parent'])
    checked(working_child, hashes['Synchronized'])
    checked(Path(__file__).resolve().with_name('AuditConcentricDisplayAuthoring.py'), AUDIT_TOOL)
    from AuditConcentricDisplayAuthoring import (
        INSTANCE, VISUAL, FieldInt, ReadFileKey, ReadHeaderGraph, SldprtArchive, XmlRoot,
        archive_stamps, file_owners, index_graph, model_inputs,
    )

    parent = SldprtArchive.from_bytes(data['parent'])
    refs, config, name, _, parent_header = model_inputs(parent)
    states = tuple((row['name'], tuple(row['visibility'])) for row in trial['states'])
    tree = XmlRoot(parent.require(INSTANCE))
    _, index, _ = index_graph(tree, refs, config, name, states)
    children = {lane: SldprtArchive.from_bytes(data[lane]) for lane in ('Stale', 'Synchronized')}
    headers = {lane: ReadHeaderGraph(child.require('Contents/Config-0-ModelHeader'), 19000) for lane, child in children.items()}
    directory = next(iter(refs.values())).FieldsValue['f3b0']
    saved_child_locator = PureWindowsPath(ReadFileKey(directory)[1])
    require(saved_child_locator.drive.casefold() == 'z:' and saved_child_locator.parts[1:] == PureWindowsPath(guest(working_child)).parts[1:],
            'saved parent child locator differs from the intended fixed destination')
    owner = file_owners(tree, index, refs, parent_header, headers['Stale'], saved_child_locator)
    require(owner['parent_path_sha256'] == sha256(guest(working_parent).encode()).hexdigest(), 'the parent was saved under another locator')
    stale_key, synced_key = (ReadFileKey(headers[lane].FieldsValue['f38']) for lane in ('Stale', 'Synchronized'))
    require(stale_key[:1] + stale_key[2:] == synced_key[:1] + synced_key[2:], 'the synchronized child changed the linked file identity')
    stamps = {lane: archive_stamps(child, headers[lane])['update_stamp'] for lane, child in children.items()}
    reference = [FieldInt(row.FieldsValue, 'f3e0') for row in refs.values()]
    live = author['live_child_stamp']
    require(stamps['Stale'] == 134 and live != stamps['Stale'] and reference == [live, live]
            and owner['child_reference_stamp'] == stamps['Synchronized'] == live
            and author['child_before_own_save']['update_stamp'] == author['child_after_own_save']['update_stamp'] == live,
            f'abort cold dispatch, child disk stamps {stamps}, reference stamps {reference} and live {live} do not isolate the native child save')
    gate = {'schema': SCHEMA, 'trial_sha256': trial_sha, 'author_record_sha256': author_sha, 'artifact_sha256': hashes,
            'child_persisted_stamps': stamps, 'parent_reference_stamps': reference, 'live_child_stamp': live,
            'saved_child_locator': str(saved_child_locator), 'selected_child_configuration': owner['child_configuration'],
            'display_stream_sha256': {stream: sha256(parent.require(stream)).hexdigest() for stream in (INSTANCE, VISUAL)},
            'heldout_inputs_read': 0, 'native_launches': 0, 'passed': True}
    gate_sha = publish(root, 'Gate.json', json_bytes(gate))
    recipe = {'trial_sha256': trial_sha, 'gate_sha256': gate_sha, 'ordered_steps': list(COLD),
              'argv': guest_argv(root, trial_sha, COLD, gate_sha), 'fixed_parent_sha256': hashes['parent'],
              'paired_child_sha256': {key: hashes[key] for key in stamps},
              'always_attempt_trailing_control_after_native_failure_if_idle': True,
              'diagnostic_success_requires_both_observations_and_healthy_brackets': True,
              'host_wait_limit_seconds': {'StageStale': 30, 'Stale': 180, 'StageSynchronized': 30, 'Synchronized': 180,
                                          'ControlAfter': 150, 'summary': 30}}
    checksum = publish(root, 'ColdRecipe.json', json_bytes(recipe))
    return {'gate_sha256': gate_sha, 'cold_recipe_sha256': checksum, 'stamps': stamps, 'reference_stamps': reference}


def main():
    parser = argparse.ArgumentParser(description='Prepare or host-gate one fixed-parent native child-save trial')
    sub = parser.add_subparsers(dest='command', required=True)
    prepare_mode = sub.add_parser('prepare')
    prepare_mode.add_argument('--name', default='ConcentricDisplaySync01')
    gate_mode = sub.add_parser('gate')
    gate_mode.add_argument('trial', type=Path)
    gate_mode.add_argument('trial_sha')
    args = parser.parse_args()
    result = prepare(args.name) if args.command == 'prepare' else stamp_gate(args.trial.resolve(), args.trial_sha)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
