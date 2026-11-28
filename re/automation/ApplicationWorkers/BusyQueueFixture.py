import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import time

import win32con
import win32file

import ApplicationProtocol
import ProtocolFixture
import WindowsRecords


def run_host(config):
    publish = ApplicationProtocol.write_record
    endpoint = Path(config["endpoint"])

    def publish_busy(path, value, replace=False):
        path = Path(path)
        if path.name != "phase.done":
            return publish(path, value, replace)
        temporary = ApplicationProtocol.stage_bytes(path, ApplicationProtocol.encoded(value))
        handle = win32file.CreateFile(
            str(temporary), win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None,
        )
        try:
            os.rename(temporary, path)
            (endpoint / "busy-ready").touch()
            deadline = time.monotonic() + 30
            while not (endpoint / "release-busy").exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError("fixture publication handle was not released")
                time.sleep(0.02)
        finally:
            handle.Close()

    ApplicationProtocol.write_record = publish_busy
    ProtocolFixture.run_host(config)


def run_client(config, seconds):
    original = WindowsRecords.open_record

    @contextmanager
    def observe_record(path):
        try:
            with original(path) as source:
                yield source
        except BlockingIOError as error:
            if error.winerror == 32 and Path(path).name == "phase.done":
                (Path(config["endpoint"]) / "busy-observed").touch()
            raise

    WindowsRecords.open_record = observe_record
    ProtocolFixture.run_client(config, "echo", seconds)


def main():
    parser = argparse.ArgumentParser(description="Native Windows publication-handoff process fixture")
    parser.add_argument("operation", choices=("host", "client"))
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--mode", choices=("echo",), default="echo")
    parser.add_argument("--seconds", type=float, default=15)
    args = parser.parse_args()
    config = ApplicationProtocol.configuration(args.installation)
    if args.operation == "host":
        run_host(config)
    else:
        run_client(config, args.seconds)


if __name__ == "__main__":
    main()
