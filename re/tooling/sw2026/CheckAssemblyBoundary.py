from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT / 'src'), str(ROOT), str(ROOT / 're/tooling/sw2026')]
from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly as compile_assembly
from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import KAsmWriteCaps
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmBundle import WriteAsmBundle
from MakeAssemblyBoundaryCase import make_case
from convert.adapters import AdapterInfo, AdapterRegistry, WriteOptions, WriteResult
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry.RegistryErrors import NotFoundError


def require(value, text):
    if not value:
        raise ValueError(text)


class CandidateAdapter:
    def __init__(self, document, native_parent, saved_at):
        self.native_parent = native_parent
        self.saved_at = saved_at
        self.info = AdapterInfo('solidworks.sldasm', 'private ordinary assembly boundary', '2026', ('.sldasm',),
                                capabilities=KAsmWriteCaps, native_capabilities=KAsmWriteCaps, assembly_extensions=('.sldasm',))

    def supports(self, document, target):
        if not isinstance(target, (str, Path)) or Path(target).suffix.casefold() != '.sldasm' or Path(target).stem != document.metadata.get('name'):
            return False
        try:
            PlanAsmWrite(document, self.native_parent, self.saved_at)
        except (ValueError, TypeError, KeyError):
            return False
        return True

    def write(self, document, destination, options=None):
        require(isinstance(destination, (str, Path)), 'assembly streams cannot publish external children')
        settings = CheckAsmOpts(options)
        require(settings.configuration in (None, document.configurations[0].name), 'write configuration differs from the actual assembly configuration')
        final = Path(settings.values.get('final_destination', destination))
        native = str(settings.values.get('native_destination', self.native_parent))
        require(native == self.native_parent and final.name == native.split('\\')[-1], 'final path and pinned native parent identity differ')
        candidate = compile_assembly(document, native, self.saved_at)
        return WriteAsmBundle(candidate, Path(destination))


def contents(path):
    return {value.name: sha256(value.read_bytes()).hexdigest() for value in path.iterdir() if value.is_file()}


def run_case(mode, count, output):
    output.mkdir(parents=True, exist_ok=False)
    document = make_case(count)
    native = 'C:\\KitAssemblyBoundary\\' + document.metadata['name'] + '.SLDASM'
    registry = AdapterRegistry()
    registry.register(CandidateAdapter(document, native, 1794001000))
    target = output / (document.metadata['name'] + '.SLDASM')
    child = output / 'PublicDatumPrism.SLDPRT'
    overwrite, carrier, stream = False, True, None
    if mode == 'child-collision':
        child.write_bytes(b'existing unrelated child')
    elif mode == 'root-collision':
        target.write_bytes(b'existing unrelated assembly')
    elif mode == 'overwrite-rejected':
        target.write_bytes(b'existing assembly')
        child.write_bytes(b'existing child')
        overwrite = True
    elif mode == 'policy-rejected':
        carrier = False
    elif mode == 'stream-rejected':
        stream = BytesIO(b'existing stream')
    elif mode == 'commit-failure':
        failed = False
        def fail_once(event, args):
            nonlocal failed
            if event == 'os.rename' and not failed and Path(args[1]) == child:
                failed = True
                raise PermissionError('injected second-file publication failure')
        sys.addaudithook(fail_once)
    elif mode != 'fresh':
        raise ValueError('unknown scoped transaction case')
    before = contents(output)
    error = None
    try:
        result = registry.write(document, stream if stream is not None else target,
            format_id='solidworks.sldasm', options=WriteOptions(overwrite=overwrite, values={'allow_carrier': carrier}))
    except Exception as exception:
        error = {'type': type(exception).__name__, 'message': str(exception)}
    after = contents(output)
    require(not any(value.name.startswith('.') for value in output.iterdir()), 'transaction left staging output behind')
    if mode == 'fresh':
        require(error is None and set(after) == {target.name, child.name}, 'fresh complete bundle was not published')
        require(result.application_usable is False and result.vendor_loadable is False, 'prototype invented native qualification')
    else:
        require(error is not None and before == after, 'failed transaction altered existing files or published a partial bundle')
    if stream is not None:
        require(stream.getvalue() == b'existing stream', 'stream rejection altered caller data')
    return {'case': mode, 'occurrences': count, 'passed': True, 'before': before, 'after': after,
            'error': error, 'native_processes_started': 0, 'native_acceptance': False,
            'registered_in_private_registry_only': True}


if __name__ == '__main__':
    record = run_case(sys.argv[2], int(sys.argv[3]), Path(sys.argv[4]))
    print(json.dumps(record, sort_keys=True))
