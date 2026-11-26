# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# managed capture records the same owner and preserves the exact journal lines for fault scenarios
KCaptureProgress = """# the managed recorder supplies the actual journal and its process output
def CaptureProgress(SourceRoot, OutputPath, Owner):
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
