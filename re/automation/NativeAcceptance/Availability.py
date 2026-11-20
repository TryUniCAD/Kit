import importlib.util
import os
from pathlib import Path
import sys

from ApplicationWorkers.ApplicationProtocol import directory
from NativeAcceptance.Records import Endpoint, FileHash, ReadJson


def ApiStatus(application):
    if application == "solidworks":
        if sys.platform != "win32":
            return {"status": "unavailable", "action": "Run this command on Windows with a licensed SOLIDWORKS installation and its registered COM API"}
        if importlib.util.find_spec("pythoncom") is None or importlib.util.find_spec("win32com") is None:
            return {"status": "unavailable", "action": "Install Kit with pywin32 in its Python environment: uv tool install --python 3.14 --with pywin32 ."}
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"SldWorks.Application\CLSID"):
                pass
        except OSError:
            return {"status": "unavailable", "action": "Enable or repair the SOLIDWORKS COM API registration through the licensed SOLIDWORKS installer"}
        return {"status": "available"}
    if application != "fusion":
        raise ValueError("unsupported native verification application")
    action = "Run kit research --root CHECKOUT api enable fusion, enable KitVerify and Run on Startup in Fusion Scripts and Add-Ins, then close Fusion"
    try:
        directory(Endpoint())
        config = ReadJson(Endpoint() / "config.json")
        ready = ReadJson(Endpoint() / "ready.json")
        executable = Path(ready["executable"])
        if not executable.is_absolute() or not executable.is_file() or ready["config_sha256"] != FileHash(Endpoint() / "config.json"):
            return {"status": "unavailable", "action": action}
        root = Path(config["source_root"])
        if any(FileHash(root / relative) != pin for relative, pin in config["sources"].items()):
            return {"status": "unavailable", "action": action + "; reinstall the add-in after changing Kit sources"}
        return {"status": "available", "executable": str(executable), "endpoint": str(Endpoint())}
    except (OSError, ValueError, KeyError, TypeError):
        return {"status": "unavailable", "action": action}
