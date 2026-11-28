from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys


parser = ArgumentParser(description='Audit only the disclosed selected-body generated through-all native derivative')
parser.add_argument('--sdk-root', type=Path, required=True)
parser.add_argument('--helpers-root', type=Path, required=True)
parser.add_argument('--native-root', type=Path, required=True)
parser.add_argument('--source-manifest', type=Path, required=True)
parser.add_argument('--result-sha256', required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
sys.dont_write_bytecode = True
root = args.native_root.resolve(strict=True)
assert root.name == 'GeneratedThroughAllSelected01'
assert sha256((root / 'Trial02.json').read_bytes()).hexdigest() == '2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a'
terminal = root / 'Inspection/Result.json'
assert sha256(terminal.read_bytes()).hexdigest() == args.result_sha256
native = json.loads(terminal.read_bytes())
assert native['passed'] and native['controls_healthy'] and native['distinct_native_processes'] == 4 and native['all_inputs_immutable'] and native['all_numeric_checks_passed'] and native['numeric_checks'] == 72
assert sha256((root / 'GeneratedInput/GeneratedThroughG01.SLDPRT').read_bytes()).hexdigest() == '339b4a635c9695306bcc8be512ba21f1473d97201a63b4ac668132ba7ef777a4'
assert sha256((args.helpers_root / 'AuditThroughAllDisclosed.py').read_bytes()).hexdigest() == '3efab18180d8c849fc8eb8a809bfb2f9bff2726ca01b0faec5d8fbdf7ee9b9bb'
assert sha256(args.source_manifest.read_bytes()).hexdigest() == '7ff3eacf713c39e109c09bb786f521c9f97df3413c1224a5e7278438d4a4639e'
for relative, expected in json.loads(args.source_manifest.read_bytes())['source_files'].items():
    assert sha256((args.sdk_root / relative).read_bytes()).hexdigest() == expected['sha256']
sys.path[:0] = [str(args.sdk_root / 'src'), str(args.helpers_root)]
from AuditThroughAllDisclosed import graph, roundtrip
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadManagedCutAtoms
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import ReadSavedCutBodies
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import CheckSavedCutScope
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner

generated_record = root / 'Inspection/Generated/Record.json'
generated = json.loads(generated_record.read_bytes())
assert sha256(generated_record.read_bytes()).hexdigest() == native['phases']['Generated']['record_sha256']
assert generated['passed'] and generated['result']['save'] == [True, 0, 0]
expected = json.loads((root / 'GeneratedCase.json').read_bytes())['prediction']['edited']
file = root / 'Inspection/Generated/Saved.SLDPRT'
payload = file.read_bytes()
assert sha256(payload).hexdigest() == generated['result']['saved_sha256']
archive, link, _, named = graph(payload)
for report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue):
    assert report['completed'] and not report['missing_schemas'] and not report['provisional_schemas']
boss, cut = named['StockBoss'], named['ThroughFeature']
fields = cut.FieldsValue
end = fields['f818'].FieldsValue
atoms = ReadManagedCutAtoms(link)
consumed, produced = ReadSavedCutBodies(boss, cut, atoms)
scope = CheckSavedCutScope(link.ConfigValue.RootValue, boss, cut, consumed)
assert scope == boss.FieldsValue['f544'] == fields['f544'] == 1
wrapper = fields['f548']['items'][0]['o'].FieldsValue
assert wrapper['ff0'] is None and wrapper['f100'] == wrapper['f104'] == 0
cold = json.loads((root / 'SelectedScopeProof.json').read_bytes())
case = next(row for row in cold['positive_cases'] if row['case'] == 'G01')
assert consumed == case['grammar']['generated_stock_atom_id'] and produced != consumed
assert wrapper['f108'] == case['grammar']['feature_ids']['StockBoss']
depth = ReadDepthOwner(link, boss.FieldsValue['f818'].FieldsValue['f18'])
assert depth.DepthValue.native_value == expected['stock_depth_m']
assert tuple(end[key] for key in ('f08', 'f0c', 'f10', 'f88', 'f8c')) == (1, 1, 0, 0, 1)
assert all(end[key] is None for key in ('f18', 'f20', 'fc8', 'fd0'))
result = {'schema': 'kit.sw2026.selected-through-all-saved-typed.v1', 'passed': True, 'tool_sha256': sha256(Path(__file__).read_bytes()).hexdigest(), 'native_packet_sha256': sha256((root / 'Trial02.json').read_bytes()).hexdigest(), 'native_result_sha256': args.result_sha256, 'input_sha256': sha256(payload).hexdigest(), 'bytes': len(payload), 'sdk_source_manifest_sha256': sha256(args.source_manifest.read_bytes()).hexdigest(), 'stream_roundtrips': roundtrip(archive, link), 'stock_scope': boss.FieldsValue['f544'], 'cut_scope': scope, 'actual_body_manager_aliases': True, 'actual_selected_wrapper_owner': True, 'actual_base_feature_lineage': True, 'scope_preserved_after_edit_save_and_fresh_reopen': True, 'stock_depth_m': depth.DepthValue.native_value, 'consumed_boss_atom_id': consumed, 'produced_cut_atom_id': produced, 'cut_has_saved_wrapper': fields['has_f548'], 'cut_has_saved_chooser': fields['has_f4c0'], 'cut_end': {key: end[key] for key in ('f08', 'f0c', 'f10', 'f88', 'f8c', 'f148', 'f14c', 'f150', 'f154', 'f158')}, 'continuous_automatic_selection_proven': False, 'heldout_payloads_read': 0, 'original_source_equivalence': False, 'public_read_qualified': False, 'public_writer_qualified': False}
encoded = (json.dumps(result, indent=2, sort_keys=True)+'\n').encode()
if args.check:
    assert args.output.read_bytes() == encoded
else:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
print(json.dumps({'passed': True, 'sha256': sha256(encoded).hexdigest(), 'stream_roundtrips': len(result['stream_roundtrips']), 'cut_scope': scope}))
