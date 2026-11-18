from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from runpy import run_path
import sys


ROOT = Path(sys.argv[1]).resolve(strict=True)
BUFFER = StringIO()


with redirect_stdout(BUFFER):
    run_path(str(Path(__file__).parent / 'RunPerpRegistry.py'), run_name='__main__')


RESULT = json.loads(BUFFER.getvalue())
IMPORTS = []
VENDOR = []


for NAME, MODULE in tuple(sys.modules.items()):
    FILE_NAME = getattr(MODULE, '__file__', None)
    if isinstance(FILE_NAME, str) and Path(FILE_NAME).resolve().is_relative_to(ROOT / 're'):
        if NAME != 'SdkNativeRoundTrips':
            IMPORTS.append(NAME)
    if NAME.split('.', 1)[0] in ('FreeCAD', 'FreeCADGui', 'pythoncom', 'win32com', 'SldWorks'):
        VENDOR.append(NAME)


if IMPORTS or VENDOR:
    raise PermissionError('the normal SDK registry worker imported research rules or a CAD application runtime')


RESULT.update(sdk_runtime_research_imports=len(IMPORTS), cad_runtime_modules=len(VENDOR))
print(json.dumps(RESULT, sort_keys=True, allow_nan=False))
