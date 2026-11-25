from argparse import ArgumentParser
from json import dumps, loads
from os import environ
from pathlib import Path
from subprocess import Popen, run
from sys import executable
from time import monotonic, sleep


def Main():
    parser=ArgumentParser()
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--host',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    probe=Path(__file__).with_name('ProbeRoutine.py')
    output=args.output.resolve()
    if output.exists():
        raise ValueError('Use a fresh output directory')
    process=Popen([executable,'-B',str(probe),'--cases',str(args.cases),
                   '--host',str(args.host),'--output',str(output)])
    try:
        deadline=monotonic()+60
        while True:
            records=list(output.glob('SolidWorksQueue/*/first-startup.jsonl'))
            if records:
                try:
                    first=loads(records[0].read_text().splitlines()[0])
                except (ValueError,IndexError):
                    sleep(.05)
                    continue
                break
            if monotonic()>deadline or process.poll() is not None:
                raise TimeoutError('First owned launch was not published')
            sleep(.05)
        shell=Path(environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        killed=run([str(shell),'-NoProfile','-NonInteractive','-Command',
                    "$ErrorActionPreference='Stop'; $Native=[Diagnostics.Process]::GetProcessById([int]$env:KIT_PROBE_PID); "
                    "if ($Native.StartTime.ToUniversalTime().ToFileTimeUtc().ToString() -cne $env:KIT_PROBE_CREATED) { throw 'Identity changed' }; "
                    "$Native.Kill(); if (-not $Native.WaitForExit(10000)) { throw 'Owned startup did not exit' }"],
                   env={**environ,'KIT_PROBE_PID':str(first['pid']),'KIT_PROBE_CREATED':str(first['created'])},
                   capture_output=True,text=True,check=True,timeout=20)
        (output/'InjectedStartupFailure.json').write_text(dumps({**first,'injected_owned_process_exit':True}),encoding='utf-8')
        if process.wait(timeout=900)!=0:
            raise RuntimeError('Native comparison failed after injected startup exit')
        startup=loads(records[0].with_suffix('.json').read_bytes())
        attempts=startup['attempts']
        if len(attempts)!=2 or attempts[0]['ready'] or not attempts[1]['ready']:
            raise AssertionError('Startup did not fail once and recover on the next launch')
        if attempts[0]['pid']!=first['pid'] or attempts[1]['pid']==first['pid']:
            raise AssertionError('Startup retry did not use a new owned process')
        print(output/'Probe.json')
    finally:
        if process.poll() is None:
            for queue in output.glob('SolidWorksQueue/*'):
                if queue.is_dir(): (queue/'stop').touch()
            try: process.wait(timeout=45)
            except TimeoutError: process.terminate(); process.wait(timeout=15)


if __name__=='__main__':
    Main()
