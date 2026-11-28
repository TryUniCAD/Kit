from argparse import ArgumentParser
from codecs import lookup
from io import BytesIO
from importlib import import_module
from json import dumps, loads
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CheckThinReviewBoundary import SavedReadAudit
from CheckThinSuiteCase import read
from ProveMeasuredPrincipalRevolve import ROOT, digest
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition, HasPayload
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Adapter import NativePartModel, SldprtAdapter
from interchange import CadDocument
from interchange.Features.ThinRevolve import ThinRevolve

FIXTURES = ROOT / 're/solidworks/v2026/corpus/revolve/SavedThinQueue20261128'
NAMES = ('ThinQueueFrontOriginal', 'ThinQueueFrontEdited', 'ThinQueueRightOriginal', 'ThinQueueRightEdited')
MANIFEST_SHA256 = '5bdd5ef5823b0fb0dc41485d36d31ebc1108e3732ee13beda005d07874ff653a'


def custody(name, row):
    receipts = {}
    for suffix, expected in row['receipt_sha256'].items():
        blob = (FIXTURES / (name + suffix)).read_bytes()
        assert digest(blob) == expected
        receipts[suffix] = loads(blob)
    author, reopened = receipts['Author.json'], receipts['Reopen.json']
    assert author['native_process']['pid'] == row['author_pid']
    assert reopened['native_process']['pid'] == row['reopen_pid']
    assert row['author_pid'] != row['reopen_pid']
    assert reopened['native_process']['exited_observed'] and reopened['readOnly']
    assert not author['readOnly'] and len(author['edits']) == row['driving_edits']
    baseline = row['volume_m3']
    assert abs(author['measured'][3] - baseline) < 1e-16
    assert abs(reopened['measured'][3] - baseline) < 1e-16
    for edit in author['edits']:
        assert abs(edit['changed'][3] - baseline) > baseline * 1e-4
        assert abs(edit['restored'][3] - baseline) < 1e-16


def controls(manifest):
    for name, expected in manifest['retained_receipt_sha256'].items():
        blob = (FIXTURES / name).read_bytes()
        assert digest(blob) == expected
    for campaign in ('Author', 'Recovery'):
        observations = []
        for phase in ('before', 'after'):
            receipt = loads((FIXTURES / (campaign + 'Stock-' + phase + '.json')).read_bytes())
            assert receipt['native_process']['exited_observed'] and receipt['read_only']
            assert receipt['open_errors'] == 0 and receipt['open_warnings'] == 0
            assert receipt['observation']['rebuild']
            body, = receipt['observation']['bodies']
            assert abs(body['volume_m3'] - 8e-6) < 1e-16
            observations.append((receipt['native_process']['pid'], receipt['archive']['sha256']))
        assert observations[0][0] != observations[1][0]
        assert observations[0][1] == observations[1][1]


def verify(name):
    manifest_raw = (FIXTURES / 'Manifest.json').read_bytes()
    assert digest(manifest_raw) == MANIFEST_SHA256
    manifest = loads(manifest_raw)
    controls(manifest)
    row, = (row for row in manifest['cases'] if row['name'] == name)
    custody(name, row)
    source = FIXTURES / row['file']
    raw = source.read_bytes()
    assert digest(raw) == row['sha256'] and len(raw) == row['bytes']
    archive = SldprtArchive.from_bytes(raw)
    config = NativePartModel(archive, None).active_configuration_id
    stream = f'Contents/Config-{config}-Partition'
    partitions = [key for key, value in archive.streams.items() if HasPayload(value)]
    assert partitions == [stream]
    expected = DecodePartition(archive.require(stream), stream)
    assert expected and all(value.data for value in expected)
    for encoding in ('utf-8', 'utf-16-le'):
        lookup(encoding)
    import_module('interchange.brep.Validation.BrepValidate')
    import_module('interchange.document.Models.DocumentProvenance')
    model = (FIXTURES / (name + 'Model.json')).read_bytes()
    assert digest(model) == row['receipt_sha256']['Model.json']
    CadDocument.from_json(model.decode('utf-8')).assert_valid()
    with TemporaryDirectory(prefix='KitSavedThinRead-') as folder:
        audit = SavedReadAudit(Path(folder))
        for full in (True, False):
            try:
                audit.run(lambda: read(raw, full))
            except SldprtFormat as error:
                assert str(error) == 'saved thin revolve has unverified editable history'
            else:
                raise AssertionError('a genuine saved thin part lost its strict history guard')
            document = audit.run(lambda: read(raw, full, strict=False))
            assert len(document.bodies) == 1 and (document.brep is not None) is full
            assert all(not isinstance(step.definition, ThinRevolve) for step in document.feature_timeline)
        document = audit.run(lambda: SldprtAdapter().read(
            BytesIO(raw), ReadOptions(extract_raw_brep=True, include_brep=True, strict=True),
        ))
        actual = [value for value in document.brep_payloads if value.source_stream == stream]
        assert [(value.data, value.sha256) for value in actual] == [
            (value.data, digest(value.data)) for value in expected
        ]
        assert len(actual) == len(document.brep_payloads)
        runtime = audit.report()
    assert source.read_bytes() == raw
    return {'case': name, 'sha256': digest(raw), 'bytes': len(raw), 'strict_refusals': 2,
            'partial_permissive_reads': 2, 'raw_payloads': len(actual), 'runtime': runtime,
            'installed_grammar_reads': audit.layout_reads, 'native_launches': 0}


if __name__ == '__main__':
    parser = ArgumentParser(description='Exercise genuine native saved thin parts through guarded SDK reads')
    parser.add_argument('--case', choices=NAMES, required=True)
    args = parser.parse_args()
    print(dumps(verify(args.case), sort_keys=True))
