from pathlib import Path
from hashlib import sha256
import argparse
import dataclasses
import importlib.abc
import importlib.util
import json
import os
import sys
import sysconfig

TARGET = 'convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex'
RELATIVE = 'src/convert/adapters/solidworks/Drawing/Construction/Indexes/ReadViewIndex.py'
BASE = '03969f0bad9bf1d36e55a23725ad1d7af1b5f1ce657edbf866ad0bb4d1dbcc78'
RESULT = 'e3ad40cbda5ca34d5f55015b0dc57f6c0af12c60bef70d2032cb96625c9462bb'


def digest(data):
    return sha256(data).hexdigest()


def changed(source):
    replacements = (
        ('    ConfigName = ConfigValue["f08"]\n', '    ConfigName = ConfigValue["f08"]\n    if isinstance(ConfigName, CStringValue):\n        ConfigName = ConfigName.TextValue\n'),
        ('or not isinstance(ConfigName, CStringValue)', 'or type(ConfigName) is not str'),
        ('CheckDrawText(ConfigName.TextValue, True)', 'CheckDrawText(ConfigName, True)'),
        ('return DrawViewIndex(NameValue, PathValue, ConfigName.TextValue, ConfigId)',
         'return DrawViewIndex(NameValue, PathValue, ConfigName, ConfigId)'),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('source delta anchor differs')
        source = source.replace(old, new)
    if digest(source.encode()) != RESULT:
        raise ValueError('in-memory source result differs')
    return source


class Overlay(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, root):
        self.path = root / RELATIVE
        self.count = 0

    def find_spec(self, fullname, path=None, target=None):
        if fullname == TARGET:
            return importlib.util.spec_from_loader(fullname, self, origin=str(self.path))
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raw = self.path.read_bytes()
        if digest(raw) != BASE:
            raise ValueError('source base differs')
        module.__file__ = str(self.path)
        exec(compile(changed(raw.decode()), str(self.path), 'exec'), module.__dict__)
        self.count += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--orientation', required=True)
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--mutation', default='none')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    source = args.source.read_bytes()
    if digest(source) != args.source_sha256 or args.output.exists():
        raise ValueError('source custody or output differs')
    if digest((root / RELATIVE).read_bytes()) != BASE:
        raise ValueError('current SDK target differs from the frozen base')
    sys.path[:0] = [str(root / 'src'), str(root)]
    overlay = Overlay(root)
    if args.variant == 'candidate':
        sys.meta_path.insert(0, overlay)

    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import WalkDrawNodes
    from convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex import ReadViewIndex
    from convert.adapters.solidworks.Drawing.Metadata.ReadDrawKeywords import ReadSheetKeys
    from convert.adapters.solidworks.Container.Format import KeywordsStream
    import codecs
    for name in ('utf-16-le', 'utf-16-be', 'utf-8', 'cp1252'):
        codecs.lookup(name)

    allowed = [root, Path(sys.base_prefix).resolve(), Path(sys.prefix).resolve(),
               Path(sysconfig.get_path('stdlib')).resolve(), Path(__file__).resolve().parent]
    denied = []
    opened = []
    def is_model_file(name):
        return isinstance(name, (str, bytes, Path)) and str(name).casefold().endswith(('.sldprt', '.sldasm', '.slddrw'))
    def audit(event, values):
        if event != 'open':
            return
        name = values[0]
        if is_model_file(name):
            denied.append({'event': event, 'path': str(name)})
            raise ValueError('unexpected runtime native-model file read')
        if not isinstance(name, (str, bytes)):
            return
        path = Path(name.decode() if isinstance(name, bytes) else name)
        resolved = path.absolute()
        if any(resolved.is_relative_to(parent) for parent in allowed):
            opened.append(str(path))
            return
        denied.append(str(path))
        raise RuntimeError('undeclared runtime file access: ' + str(path))
    sys.addaudithook(audit)
    for name in ('stat', 'lstat'):
        original = getattr(os, name)
        def checked_stat(path, *values, _original=original, _name=name, **options):
            if is_model_file(path):
                denied.append({'event': _name, 'path': str(path)})
                raise ValueError('unexpected runtime native-model file metadata access')
            return _original(path, *values, **options)
        setattr(os, name, checked_stat)

    archive = SldprtArchive.from_bytes(source)
    data = archive.require('Contents/Definition')
    parsed = ReadNamedDef(data, 19000, args.orientation)
    before = WriteNamedDef(parsed.GraphValue)
    if before.OutputValue != data:
        raise ValueError('normal Definition baseline byte identity failed')
    views = [node for node in WalkDrawNodes(parsed.GraphValue.DocumentValue)
             if node.ClassValue.NameValue == 'moAbsoluteView']
    if len(views) != 1:
        raise ValueError('selected source does not have one actual model view')
    view, = views
    config = view.FieldsValue['f5d8'].FieldsValue['f3c0']
    shared = view.FieldsValue['f5d8'].FieldsValue['f3b0'].FieldsValue['shared']
    name = config['f08']
    sheet = ReadSheetKeys(archive.require(KeywordsStream))
    result = {'passed': False, 'variant': args.variant, 'mutation': args.mutation,
              'source_sha256': args.source_sha256, 'definition_sha256': digest(data),
              'decoded_config_type': type(name).__name__, 'index': None,
              'raw_roundtrip_before': True, 'runtime_extra_file_accesses': denied}
    saved = []
    def set_value(mapping, key, value):
        saved.append((mapping, key, mapping[key]));mapping[key] = value
    mutations = {
        'config_bool': lambda: set_value(config, 'f08', True),
        'config_empty': lambda: set_value(config, 'f08', ''),
        'config_separator': lambda: set_value(config, 'f08', 'invalid@configuration'),
        'config_nul': lambda: set_value(config, 'f08', 'invalid\0configuration'),
        'config_wrapped_empty': lambda: set_value(config, 'f08', CStringValue('', True)),
        'config_id_negative': lambda: set_value(config, 'f10', -1),
        'config_id_bool': lambda: set_value(config, 'f10', False),
        'path_relative': lambda: set_value(shared['h18'].FieldsValue, 'value', CStringValue('child.SLDPRT', True)),
        'path_suffix': lambda: set_value(shared['h18'].FieldsValue, 'value', CStringValue('C:\\input\\child.SLDASM', True)),
        'file_kind': lambda: set_value(shared, 'f20', 3),
        'title_mismatch': lambda: set_value(shared['h10'].FieldsValue, 'value', CStringValue('DifferentTitle', True)),
    }
    if args.mutation != 'none':
        if args.mutation not in mutations:
            raise ValueError('unknown negative fixture')
        if args.mutation in {'config_id_negative', 'config_id_bool', 'path_relative', 'path_suffix', 'file_kind', 'title_mismatch'}:
            set_value(config, 'f08', CStringValue(name, True))
        mutations[args.mutation]()
    try:
        index = ReadViewIndex(view)
        result['index'] = {'view': index.NameValue, 'path': str(index.PathValue),
                           'configuration': index.ConfigName, 'configuration_id': index.ConfigId}
    except ValueError as error:
        result['index_rejection'] = str(error)
    if args.mutation != 'none':
        result['passed'] = result['index'] is None
        for mapping, key, value in reversed(saved):
            mapping[key] = value
    else:
        if args.variant == 'baseline':
            if result['index'] is not None or result.get('index_rejection') != 'drawing indexes require actual typed generated child strings':
                raise ValueError('baseline did not preserve its measured typed-text refusal')
        else:
            if result['index'] is None or index.NameValue != sheet.ViewName or index.ConfigName != sheet.ConfigName:
                raise ValueError('candidate index did not retain actual view/configuration identities')
        config['f08'] = CStringValue(name, True)
        wrapped = ReadViewIndex(view)
        result['constructed_text_representation'] = {'view': wrapped.NameValue, 'path': str(wrapped.PathValue),
                                                   'configuration': wrapped.ConfigName, 'configuration_id': wrapped.ConfigId}
        config['f08'] = name
        profiles = parsed.ProfileDisplays
        result['profile_counts'] = [len(group.ItemsValue) for group in profiles]
        result['unprojected'] = list(parsed.Unprojected)
        for group in profiles:
            for item in group.ItemsValue:
                previous = item.DisplayValue.FieldsValue['f200']
                item.DisplayValue.FieldsValue['f200'] = 2
                try:
                    parsed.ProfileDisplays
                except ValueError:
                    result['unknown_profile_flag_still_rejected'] = True
                else:
                    raise ValueError('existing profile guard changed')
                finally:
                    item.DisplayValue.FieldsValue['f200'] = previous
        document = open_document(source, source_format='solidworks.slddrw', strict=False)
        result['partial_drawing_sha256'] = digest(json.dumps(dataclasses.asdict(document.DrawingValue),sort_keys=True).encode())
        result['diagnostics'] = [value.code for value in document.diagnostics]
        if result['diagnostics'] != ['slddrw.layout_inspection']:
            raise ValueError('public inspection diagnostic changed')
        try:
            open_document(source, source_format='solidworks.slddrw', strict=True)
        except Exception as error:
            result['strict_refusal'] = {'type': type(error).__name__, 'message': str(error)}
        else:
            raise ValueError('strict public drawing reading was enabled')
        result['passed'] = True
    after = WriteNamedDef(parsed.GraphValue)
    result['raw_roundtrip_after'] = after.OutputValue == data
    result['map_counters_unchanged'] = before.MapValue.CounterValue == after.MapValue.CounterValue == parsed.MapValue.CounterValue
    result['target_source_unchanged'] = digest((root / RELATIVE).read_bytes()) == BASE
    result['patched_module_loads'] = overlay.count
    result['runtime_trusted_code_file_reads'] = len(opened)
    result['native_runs'] = 0
    result['generated_cad_files'] = 0
    result['heldout_inputs_read'] = 0
    if denied or not result['raw_roundtrip_after'] or not result['map_counters_unchanged'] or not result['target_source_unchanged']:
        raise ValueError('raw/source/runtime custody failed')
    if (args.variant == 'candidate') != (overlay.count == 1):
        raise ValueError('private patch was not applied exactly once')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'sha256':digest(args.output.read_bytes())}))
    if not result['passed']:
        raise SystemExit(3)


if __name__ == '__main__':
    main()
