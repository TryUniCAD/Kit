# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# the isolated host must use the provisioned operation and session configuration
KHostSetup = """import os
import json
import subprocess
import sys
import time
from pathlib import Path
import win32event
import win32process

sys.path.insert(0, sys.argv[1])
from ApplicationProtocol import configuration, encoded, pin, sha256, write_record
from SolidWorksReadbackWorker import BUILD, DISCOVERY, OUTPUTS, PROVIDER, READBACK_SCOPES, ReadbackQueue, native_identity, native_result, phase_request

config = configuration(Path(sys.argv[2]))
fault = sys.argv[3]
operation = sys.argv[4]
scope, count_field, count = READBACK_SCOPES[operation]
host = ReadbackQueue(config, PROVIDER, operation)

"""


# the fixture needs native process identity and a witnessed exit
KNativeOwner = """def observe(request, work):
    assert request['body'] == phase_request(config, operation)
    output = work / 'readback'
    output.mkdir()
    executable = sys.executable
    command = subprocess.list2cmdline([executable, '-I', '-S', '-c', 'import time; time.sleep(30)'])
    handle, thread, _, _ = win32process.CreateProcess(
        executable, command, None, None, False, subprocess.CREATE_NO_WINDOW,
        None, str(work), win32process.STARTUPINFO(),
    )
    thread.Close()
    try:
        owner = {'version': 1, 'request_sha256': sha256(encoded(request)),
                 'source_revision': config['source_revision'], **native_identity(handle),
                 'build': BUILD, 'initial_documents': 0}
        win32process.TerminateProcess(handle, 0)
        assert win32event.WaitForSingleObject(handle, 5000) == win32event.WAIT_OBJECT_0
    finally:
        if win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_TIMEOUT:
            win32process.TerminateProcess(handle, 1)
            assert win32event.WaitForSingleObject(handle, 5000) == win32event.WAIT_OBJECT_0
        handle.Close()
"""


# the planned fixture roster must be bound to the captured source revision
KFixturePlan = """    names = ([f'{recipe}-solidworks-fixture-{index}.SLDPRT'
              for recipe, size in (('P01', 6), ('P03', 8), ('P04', 11)) for index in range(size)]
             if operation == DISCOVERY else
             [f'fixture-circle-{index}.SLDPRT' for index in range(count)])
    if fault == 'scope':
        names[-1] = 'P03-solidworks-unrelated.SLDPRT'
    if fault == 'duplicate':
        names[-1] = names[-2]
    plan = {'source_revision': config['source_revision'], 'recipe': scope,
            'native_files': dict.fromkeys(names), 'fixture_only': True}
    write_record(output / 'plan.json', plan)
    plan_hash = sha256((output / 'plan.json').read_bytes())
"""


# the report exercises native lifetime and readback claims
KObservations = """    observations = [{'file': name, 'status': 'observed',
                     'circle_verified_before_and_after_rebuild': True} for name in names]
    if fault == 'circle':
        observations[0]['circle_verified_before_and_after_rebuild'] = False
    if fault == 'roster':
        observations[0]['file'] = observations[1]['file']
    report = {'plan_sha256': plan_hash, 'source_bytes_verified_after_readback': True,
              'fixture_only': True, 'run': {
                  'status': 'observed', 'observations': observations, 'application': {'build': BUILD},
                  'native_owner': owner, 'owned_process_exit_observed': True,
                  'application_lifetime': {'user_control_before': False, 'background_control_before': False,
                                           'background_control_after': fault != 'lifetime', 'user_control_after': False},
                  'control_before': {'status': 'observed'}, 'control_after': {
                      'status': 'observed', 'close_operand': 'control.SLDPRT', 'close_method': 'quit_document',
                      'document_visible_at_close': fault == 'visible',
                      'close_state': {'save_flag': True, 'read_only': fault != 'discard', 'document_count': 1}}}}
    if operation == DISCOVERY:
        report['run']['readback_options'] = {
            'command_in_progress_before': False,
            'command_in_progress_during': True, 'command_in_progress_restored': fault != 'restore'}
        for item in observations:
            if item['file'].startswith('P04-'):
                item['face_verified_before_and_after_rebuild'] = True
        if fault == 'cut':
            observations[-1]['face_verified_before_and_after_rebuild'] = False
        if fault == 'command_inactive':
            report['run']['readback_options']['command_in_progress_during'] = False
"""


# the managed journal fixture must receive the same owner as the report
KProgressCapture = """    owner_path = output / 'fixture-owner.json'
    write_record(owner_path, owner)
    powershell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    journal_path = output / 'native-progress.jsonl'
    generated = subprocess.run([
        str(powershell), '-NoProfile', '-NonInteractive', '-File', str(Path(__file__).with_name('Progress.ps1')),
        '-Source', str(Path(config['source_root']) / 're/automation/CaptureTools/SolidWorksAuthoring/ReadbackProgress.cs'),
        '-OwnerPath', str(owner_path), '-JournalPath', str(journal_path), '-MarkerPath', str(output / 'fixture-action.txt'),
    ], capture_output=True, check=False, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    assert generated.returncode == 0, generated.stderr.decode(errors='replace')
    native_progress = json.loads(generated.stdout)
    progress = journal_path.read_bytes().splitlines(keepends=True)
"""


# ordering and operand faults must preserve downstream hashes
KOrderingFaults = """    if fault == 'operand':
        slot = next(index for index, line in enumerate(progress) if json.loads(line)['stage'] == 'quit_document')
        event = json.loads(progress[slot])
        event['detail']['operand'] = 'unrelated.SLDPRT'
        progress[slot] = encoded(event)
        for index in range(slot + 1, len(progress)):
            event = json.loads(progress[index])
            event['previous_sha256'] = sha256(progress[index - 1])
            progress[index] = encoded(event)
    if fault == 'hidden':
        for index, line in enumerate(progress):
            event = json.loads(line)
            if event['stage'] == 'final_control_hidden':
                event['stage'] = 'other_visibility'
            event['previous_sha256'] = sha256(progress[index - 1]) if index else None
            progress[index] = encoded(event)
    if fault == 'late_hidden':
        settings, progress = progress[:2], progress[2:]
        progress[-2:-2] = settings
        for index, line in enumerate(progress):
            event = json.loads(line)
            event['sequence'] = index + 1
            event['previous_sha256'] = sha256(progress[index - 1]) if index else None
            progress[index] = encoded(event)
"""


# binding faults exercise distinct journal rejection paths
KBindingFaults = """    if fault == 'chain':
        event = json.loads(progress[1])
        event['previous_sha256'] = '0' * 64
        progress[1] = encoded(event)
    if fault == 'binding':
        event = json.loads(progress[0])
        event['binding']['request_sha256'] = '0' * 64
        progress[0] = encoded(event)
    if fault == 'stage':
        event = json.loads(progress[1])
        event['stage'] = 'other_control'
        progress[1] = encoded(event)
"""


# receipt generation pins the exact measurements and journal
KReadbackReceipt = """    journal = b''.join(progress)
    if fault == 'incomplete':
        journal = journal[:-1]
    (output / 'native-progress.jsonl').write_bytes(journal)
    report['run']['native_progress'] = {'version': 1, 'journal_utf8': journal.decode(),
                                      'sha256': sha256(journal), 'events': len(progress), 'write_error': None}
    write_record(output / 'measurements.json', report)
    write_record(output / 'receipt.json', {
        'schema': 1, 'status': 'observed', 'observed_files': count, count_field: count,
        'plan_sha256': plan_hash, 'measurements_sha256': sha256((output / 'measurements.json').read_bytes())})
    proof = native_result(work, config, operation, progress_required=True, local_progress=True)
    files = {role: pin(work / relative, relative) for role, relative in OUTPUTS.items()}
    return 'completed', 'disposable process transport fixture only', {
        **phase_request(config, operation), **proof,
        'claim': 'unqualified_application_observation', 'fixture_only': True}, files

"""


# the queue host serves requests until its parent signals shutdown
KHostLoop = """try:
    write_record(Path(config['endpoint']) / 'ready.json', {'fixture_only': True})
    while not (Path(config['endpoint']) / 'stop-fixture').exists():
        request = host.next_path()
        if request is None:
            time.sleep(.02)
        else:
            host.perform(request, observe)
finally:
    host.close()
"""


# the external python process needs one complete script with its callback and dispatch loop
KReadbackScript = (
    KHostSetup
    + KNativeOwner
    + KFixturePlan
    + KObservations
    + KProgressCapture
    + KOrderingFaults
    + KBindingFaults
    + KReadbackReceipt
    + KHostLoop
)
