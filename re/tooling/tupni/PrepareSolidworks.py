from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from win32api import OpenProcess
from win32process import GetExitCodeProcess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sw2026"))

import Swapp
from OracleIdentity import application_identity


@contextmanager
def prepare():
    Swapp.sweep()
    with Swapp.Dismisser() as dismisser:
        controller = Swapp.Sw()
        identity = {"revision": controller.revision, "restarted": True, "dialogs": dismisser.log, "progress_windows": dismisser.progress}
        process_handle = None
        try:
            if not controller.revision.startswith(Swapp.EXPECTED_BUILD):
                raise RuntimeError(f"unexpected oracle revision: {controller.revision}")
            identity["oracle_identity"] = application_identity(controller.app)
            if not identity["oracle_identity"]["version_matches"]:
                raise RuntimeError("oracle executable differs from SOLIDWORKS 2026 SP05.2 build 34.5.2.0604")
            process_handle = OpenProcess(0x1000, False, identity["oracle_identity"]["process_id"])
            yield {"controller": controller, "identity": identity}
        finally:
            try:
                if process_handle is not None:
                    try:
                        code = int(GetExitCodeProcess(process_handle))
                        identity["process_status_before_cleanup"] = {
                            "exit_code": code, "exit_code_hex": hex(code),
                            "still_active": code == 259,
                        }
                    finally:
                        process_handle.Close()
            finally:
                controller.close()
                identity["controller_diagnostics"] = controller.diagnostics
