from base64 import b64decode, b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring

sys.dont_write_bytecode = True
root = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
sys.path[:0] = [str(root), str(root / 'src'), str(root / 're/tooling/sw2026')]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(root / 're/tooling/sw2026/serial/defs')
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeColdAtom import MakeColdAtom
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import MakeSelfComp
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughPart import MakeThroughPart
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import ThroughEndInput
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import ThroughPartSpec
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import ThroughStock
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from SdkNativeRoundTrips import roundtrips


def require(value, message):
    if not value:
        raise ValueError(message)


def read_input(request):
    keys = {'name', 'configuration', 'axis', 'stock_size_m', 'stock_center_m', 'circle_center_m', 'radius_m', 'direction', 'native_path', 'written_at'}
    require(set(request) == keys, 'selected-body through-all request has unknown or missing intent')
    require(request['direction'] in ('forward', 'reverse', 'both'), 'unsupported through-all direction')
    width, height, depth = request['stock_size_m']
    cx, cy = request['stock_center_m']
    vertices = ((cx-width/2, cy-height/2), (cx+width/2, cy-height/2), (cx+width/2, cy+height/2), (cx-width/2, cy+height/2))
    axis = request['axis']
    plane = {'x': 'Right Plane', 'y': 'Top Plane', 'z': 'Front Plane'}[axis]
    plan = ThroughStock(request['name'], request['configuration'], plane, 'stock-sketch', 'StockProfile', 'stock-boss', 'StockBoss', 'stock-depth', 'cut-body', vertices, depth, width, height, axis)
    circle = CircleInput(tuple(request['circle_center_m']), request['radius_m'], 19000)
    end = ThroughEndInput('through_all_both' if request['direction'] == 'both' else 'through_all', request['direction'] != 'reverse', 19000)
    return ThroughPartSpec(plan, circle, 'ThroughProfile', 'ThroughFeature', end)


def selected_part(plan, settings):
    candidate = MakeThroughPart(plan, settings)
    root_node = candidate.SystemValue.RootValue
    boss = candidate.BossValue.FeatureValue
    cut = candidate.CutValue.FeatureValue
    manager = root_node.FieldsValue['fd88']
    require(root_node.ClassValue.NameValue == 'moPart_c' and manager['n6c'] == 0 and not manager['atoms'] and manager['fa8'] == 0, 'selected scope needs the actual fresh empty manager')
    require(all(boss.FieldsValue[key] == cut.FieldsValue[key] == 0 for key in ('f544', 'has_f528', 'has_f530', 'has_f548', 'has_f4c0', 'n494')), 'selected scope cannot replace existing scope or atom ownership')
    atom_id = manager['f260'] + 1
    atom = MakeColdAtom(plan.StockValue.FeatureName, atom_id, boss)
    atom.FieldsValue.update(f18=None, f18c=1)
    members = [{'o': atom}]
    manager.update(f260=atom_id, n6c=len(members), atoms=members)
    boss.FieldsValue.update(f544=1, has_f528=1, f528={'n': len(members), 'items': members.copy()}, n494=len(members), f498=[{'v': atom_id}])
    fields = CompRefFields(MakeSelfComp(root_node))
    fields.update(f18=atom_id, f1c=atom_id, ff0=None, n110=1, f110=[{'v': atom_id}], f108=boss.FieldsValue['f08'], f104=0, f100=0)
    wrapper = ArchiveNode(RuntimeClass('moCompSolidBody_c', 1), fields)
    cut.FieldsValue.update(f544=1, has_f548=1, f548={'n': 1, 'items': [{'o': wrapper}]})
    features = (*candidate.SystemValue.FeatureValues, candidate.ProfileValue.ProfileValue, boss, candidate.CutValue.ProfileValue.ProfileValue, cut)
    streams, config, resolved = EmitPartStreams(candidate.SystemValue, features, (candidate.HeaderValue, candidate.TopHeader, candidate.ManagerHeader), candidate.DefinitionValue, settings, candidate.PlanValue, CutValue=candidate.CutValue)
    require(not any('Partition' in key for key in streams), 'selected-body cold construction cannot transmit a kernel body')
    return replace(candidate, StreamsValue=streams, ConfigValue=config, ResolvedValue=resolved, BytesValue=BuildSldprt(streams, FormatVersion=4))


def one(array, name):
    require(isinstance(array, dict) and array['n'] == len(array['items']) == 1, 'expected one actual selected-body owner')
    node = array['items'][0]['o']
    require(isinstance(node, ArchiveNode) and node.ClassValue.NameValue == name and node.ClassValue.SchemaValue == 1, 'selected-body owner class or schema differs')
    return node


def inspect(archive, linked, expected):
    features = linked.ResolvedValue.RootsValue
    named = {ReadNodeName(node): node for node in features}
    require(len(named) == len(features), 'generated feature names are not unique')
    stock, boss, circle, cut = (named[key] for key in ('StockProfile', 'StockBoss', 'ThroughProfile', 'ThroughFeature'))
    require(features[-4:] == (stock, boss, circle, cut), 'native through-all order differs')
    model = linked.ConfigValue.RootValue
    require(model.ClassValue.NameValue == 'moPart_c', 'selected-body owner is not the actual part')
    manager = model.FieldsValue['fd88']
    require(manager['n6c'] == len(manager['atoms']) == 1, 'fresh selection must own one generated stock atom')
    atom = manager['atoms'][0]['o']
    atom_id = atom.FieldsValue['f140']
    require(atom.ClassValue.NameValue == 'moAtom_c' and one(boss.FieldsValue['f528'], 'moAtom_c') is atom, 'manager and boss output must alias the actual same atom')
    require(manager['f260'] == atom_id and boss.FieldsValue['n494'] == 1 and boss.FieldsValue['f498'] == [{'v': atom_id}], 'boss output ids differ from actual manager allocation')
    require(atom.FieldsValue['f12c'] == atom.FieldsValue['f130'] == boss.FieldsValue['f08'], 'cold stock atom lost its actual feature owners')
    require(atom.FieldsValue['body_kind'] == 0 and atom.FieldsValue['f18'] is None and atom.FieldsValue['f18c'] == 1, 'cold stock atom acquired body bytes or an authored name')
    require(boss.FieldsValue['f544'] == cut.FieldsValue['f544'] == 1 and boss.FieldsValue['has_f548'] == 0, 'selected scope differs from actual sole stock/cut ownership')
    wrapper = one(cut.FieldsValue['f548'], 'moCompSolidBody_c').FieldsValue
    component = wrapper['f58']
    require(component.ClassValue.NameValue == 'moUnitComponent_c' and component.FieldsValue['owner'] is model and component.FieldsValue['has_ext'] == 0, 'selected-body component lost actual model identity')
    require(wrapper['f18'] == wrapper['f1c'] == atom_id and wrapper['f108'] == boss.FieldsValue['f08'] and wrapper['n110'] == 1 and wrapper['f110'] == [{'v': atom_id}], 'selection base and lineage differ from the actual first-boss atom walk')
    require(wrapper['ff0'] is None and wrapper['f100'] == wrapper['f104'] == 0, 'selected cold body acquired a face or kernel node id')
    require(all(cut.FieldsValue[key] == 0 for key in ('has_f528', 'has_f530', 'has_f4c0', 'n494')) and cut.FieldsValue['f538'] is None, 'cold cut precomputed an unobserved native output or chooser cache')
    require('f558' not in boss.FieldsValue and 'f558' not in cut.FieldsValue, 'runtime auto-select is not an archive field')
    for extrude, profile in ((boss, stock), (cut, circle)):
        require(extrude.FieldsValue['f60']['list']['items'][0]['o'] is profile, 'extrusion lost its actual sketch owner')
    end = cut.FieldsValue['f818'].FieldsValue
    both = expected.EndValue.ModeValue == 'through_all_both'
    values = (int(not both), 1, int(both), 0, int(expected.EndValue.IsReversed))
    require(tuple(end[key] for key in ('f08', 'f0c', 'f10', 'f88', 'f8c')) == values and cut.FieldsValue['f810'] == 1, 'through-all type reversal or cut operation differs')
    require(all(end[key] is None for key in ('f18', 'f20', 'fc8', 'fd0', 'f138', 'f90')), 'depthless cut acquired an unused owner')
    require(all(end[key] == 0 for key in ('f150', 'f154', 'f158')), 'fresh end inherited a native saved runtime word')
    rows = list(fromstring(archive.require('swXmlContents/KeyWords')[1:]))[-4:]
    require(tuple(row.attrib['Name'] for row in rows) == ('StockProfile', 'StockBoss', 'ThroughProfile', 'ThroughFeature') and len(rows[3]) == 0, 'selected-body scope changed authored feature names or invented a cut driver')
    return {'feature_ids': {key: named[key].FieldsValue['f08'] for key in ('StockProfile', 'StockBoss', 'ThroughProfile', 'ThroughFeature')}, 'end_tuple': values, 'selected_scope': 1, 'generated_stock_atom_id': atom_id, 'actual_manager_boss_alias': True, 'actual_wrapper_self_owner': True, 'actual_wrapper_base_and_lineage': True, 'kernel_bodies_transmitted': 0, 'cut_output_atoms_precomputed': 0, 'runtime_auto_word_emitted': False}


def main(request):
    recipe = request['recipe'] if phase == 'audit' else request
    plan = read_input(recipe)
    if phase == 'build':
        settings = MakePartRecipe(plan.StockValue, recipe['written_at'])
        settings = replace(settings, OutputValue=replace(settings.OutputValue, PathName=recipe['native_path']))
        data = selected_part(plan, settings).BytesValue
    elif phase == 'audit':
        data = b64decode(request['generated'], validate=True)
    else:
        raise ValueError('expected build or audit phase')
    archive = SldprtArchive.from_bytes(data)
    linked, _, _, _, streams = roundtrips(archive, False)
    grammar = inspect(archive, linked, plan)
    require(BuildSldprt({row.name: row.data for row in archive.records}, FormatVersion=4) == data, 'selected-body container changed during exact repack')
    research = [name for name, module in tuple(sys.modules.items()) if name not in ('__main__', 'SdkNativeRoundTrips') and str(getattr(module, '__file__', '')).startswith(str(root / 're') + '/')]
    require(not audit.DeniedReads and not research, f'construction read runtime file or research inputs: {audit.DeniedReads!r}, {research!r}')
    result = {'passed': True, 'phase': phase, 'sha256': sha256(data).hexdigest(), 'bytes': len(data), 'streams': streams, 'grammar': grammar, 'runtime_input_file_reads': len(audit.DeniedReads), 'sdk_runtime_research_imports': len(research), 'native_acceptance': False, 'original_source_equivalence': False, 'public_writer_qualified': False}
    if phase == 'build':
        result['generated'] = b64encode(data).decode('ascii')
    return result


codecs = tuple(lookup(name) for name in ('utf-16-le', 'utf-8', 'latin-1'))
request = json.load(sys.stdin)
audit.BeginBuild()
print(json.dumps(main(request), sort_keys=True, allow_nan=False))
