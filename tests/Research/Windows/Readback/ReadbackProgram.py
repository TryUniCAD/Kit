# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# the queue fixture needs independent native handles while avoiding licensed cad execution
KReadbackScript = """import os
import subprocess
import sys
import time
from pathlib import Path
import win32event
import win32process

sys.path.insert(0, sys.argv[1])
from ApplicationProtocol import configuration, encoded, pin, sha256, write_record
from SolidWorksReadbackWorker import BUILD, CIRCULAR, OUTPUTS, PROVIDER, ReadbackQueue, native_identity, native_result, phase_request

config = configuration(Path(sys.argv[2]))
fault = sys.argv[3]
host = ReadbackQueue(config, PROVIDER, CIRCULAR)

def observe(request, work):
    assert request['body'] == phase_request(config, CIRCULAR)
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
    names = [f'fixture-circle-{index}.SLDPRT' for index in range(5)]
    plan = {'source_revision': config['source_revision'], 'recipe': 'P02',
            'native_files': dict.fromkeys(names), 'fixture_only': True}
    write_record(output / 'plan.json', plan)
    plan_hash = sha256((output / 'plan.json').read_bytes())
    observations = [{'file': name, 'status': 'observed',
                     'circle_verified_before_and_after_rebuild': True} for name in names]
    if fault == 'circle':
        observations[0]['circle_verified_before_and_after_rebuild'] = False
    if fault == 'roster':
        observations[0]['file'] = observations[1]['file']
    report = {'plan_sha256': plan_hash, 'source_bytes_verified_after_readback': True,
              'fixture_only': True, 'run': {
                  'status': 'observed', 'observations': observations, 'application': {'build': BUILD},
                  'native_owner': owner, 'owned_process_exit_observed': True,
                  'control_before': {'status': 'observed'}, 'control_after': {'status': 'observed'}}}
    write_record(output / 'measurements.json', report)
    write_record(output / 'receipt.json', {
        'schema': 1, 'status': 'observed', 'observed_files': 5, 'circle_bindings_verified': 5,
        'plan_sha256': plan_hash, 'measurements_sha256': sha256((output / 'measurements.json').read_bytes())})
    proof = native_result(work, config, CIRCULAR)
    files = {role: pin(work / relative, relative) for role, relative in OUTPUTS.items()}
    return 'completed', 'disposable process transport fixture only', {
        **phase_request(config, CIRCULAR), **proof,
        'claim': 'unqualified_application_observation', 'fixture_only': True}, files

try:
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
