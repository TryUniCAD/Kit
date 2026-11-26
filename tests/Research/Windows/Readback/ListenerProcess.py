# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# the measured identity comes from a real disposable process whose exit is witnessed
KNativeOwner = """def NativeOwner(Config, Request, WorkPath):
    Executable = sys.executable
    Command = subprocess.list2cmdline(
        [Executable, '-I', '-S', '-c', 'import time; time.sleep(30)']
    )
    Handle, Thread, _, _ = win32process.CreateProcess(
        Executable, Command, None, None, False, subprocess.CREATE_NO_WINDOW,
        None, str(WorkPath), win32process.STARTUPINFO(),
    )
    Thread.Close()
    try:
        Owner = {'version': 1, 'request_sha256': sha256(encoded(Request)),
                 'source_revision': Config['source_revision'], **native_identity(Handle),
                 'build': BUILD, 'initial_documents': 0}
        win32process.TerminateProcess(Handle, 0)
        assert win32event.WaitForSingleObject(Handle, 5000) == win32event.WAIT_OBJECT_0
        return Owner
    finally:
        if win32event.WaitForSingleObject(Handle, 0) == win32event.WAIT_TIMEOUT:
            win32process.TerminateProcess(Handle, 1)
            assert win32event.WaitForSingleObject(Handle, 5000) == win32event.WAIT_OBJECT_0
        Handle.Close()


"""


# managed capture records the same owner and preserves the exact journal lines for fault scenarios
KCaptureProgress = """def CaptureProgress(SourceRoot, OutputPath, Owner):
    OwnerPath = OutputPath / 'fixture-owner.json'
    write_record(OwnerPath, Owner)
    PowerShell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    JournalPath = OutputPath / 'native-progress.jsonl'
    SourcePath = Path(SourceRoot) / 're/automation/PairedCaptures/SolidWorksAuthoring/ReadbackProgress.cs'
    Generated = subprocess.run([
        str(PowerShell), '-NoProfile', '-NonInteractive', '-File', str(Path(__file__).with_name('Progress.ps1')),
        '-Source', str(SourcePath), '-OwnerPath', str(OwnerPath),
        '-JournalPath', str(JournalPath), '-MarkerPath', str(OutputPath / 'fixture-action.txt'),
    ], capture_output=True, check=False, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    assert Generated.returncode == 0, Generated.stderr.decode(errors='replace')
    json.loads(Generated.stdout)
    return JournalPath.read_bytes().splitlines(keepends=True)


"""
