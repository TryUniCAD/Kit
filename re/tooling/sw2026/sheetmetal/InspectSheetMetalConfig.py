from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

LEGACY = 'moPerBodySheetMetalData_c'
MAX_PART = 128 * 1024 * 1024
REFERENCE = 'b87f3b12b72874f4289b627d56e3740da2ab725b'
FIELDS = ('f08', 'f10', 'f18', 'f20')
INHERITED = ('f18', 'f78', 'f258', 'f2f0')


def describe(value):
    if value is None:
        return None
    slot = getattr(value, 'index', None)
    return dict(class_name=getattr(value, 'cls', type(value).__name__),
                schema=getattr(value, 'schema', None), slot=slot,
                start=getattr(value, 'pos', None), end=getattr(value, 'end', None))


def image(data):
    return sha256(data).hexdigest()


def map_members(reader):
    return {row.IndexValue: row.EntryValue for row in reader.map_state().state.EntriesValue}


def inspect(archive, registry, name):
    from Core import ArchiveError
    from Dsl import i32, obj
    from Schema import Fn
    from defs.ConfigPart import load_config_compat, store_config_state_compat
    from convert.adapters.solidworks.Container.Archive import ContainerMo

    version = ContainerMo(archive.streams)
    if version != 19000:
        raise ArchiveError('research check is scoped to generation 19000')
    data = archive.require(name)
    rules = registry()
    observations = []
    frames = []

    def begin(reader, fields, owner):
        if owner.schema != 1:
            raise ArchiveError('legacy per-body wire descriptor is outside the schema-one proposal')
        frames.append((reader.p, map_members(reader)))

    def end(reader, values, owner):
        start, incoming = frames.pop()
        outgoing = map_members(reader)
        preserved = all(outgoing.get(slot) is value for slot, value in incoming.items())
        if not preserved:
            raise ArchiveError('the per-body candidate changed existing map member identities')
        links = {}
        for field in FIELDS:
            target = values[field]
            item = describe(target)
            if item is not None:
                slot = item['slot']
                item['map_disposition'] = ('unmapped' if slot is None else
                                           'inherited' if incoming.get(slot) is target else 'allocated')
            links[field] = item
        observations.append(dict(body_start=start, body_end=reader.p,
                                 owner=describe(owner), links=links,
                                 active=values['f28'], old_atom_id=values['f2c'],
                                 incoming_identities_preserved=preserved,
                                 allocated_slots=sorted(outgoing.keys()-incoming.keys())))

    def store_noop(writer, fields, owner):
        return None

    rules.provisional(LEGACY, [Fn(begin, store_noop), *(obj(field) for field in FIELDS),
                              i32('f28'), i32('f2c'), Fn(end, store_noop)])
    document, reader = load_config_compat(data, rules, version, archive=archive, name=name)
    if document.tail:
        raise ArchiveError('configuration retains unconsumed bytes')
    part = document.roots[0]
    master = part.get('f1018')
    modern = part.get('f16e8')
    children = [] if master is None else [row['o'] for row in master['f358']]
    count = 0 if master is None else master['n370']
    if master is not None and (master.cls != 'moSheetMetalMaster_c' or master.index is not None):
        raise ArchiveError('f1018 is not the directly owned tagless master')
    if count != len(children):
        raise ArchiveError('master count and child roster differ')
    slots = {node.index for node in children if node is not None}
    if slots != {row['owner']['slot'] for row in observations} or None in slots:
        raise ArchiveError('decoded legacy owners do not match the master child slots')
    generated, written_map = store_config_state_compat(document, rules, version)
    if data != generated or reader.count != written_map.count:
        raise ArchiveError('configuration or allocation count differs after symbolic re-emission')
    source_map = map_members(reader)
    store_map = {entry.IndexValue: entry.EntryValue for entry in written_map.state.EntriesValue}
    if source_map.keys() != store_map.keys():
        raise ArchiveError('store changed the class or object slot roster')
    for slot, value in source_map.items():
        stored = store_map[slot]
        if stored is not value and stored != value:
            raise ArchiveError('store changed the typed owner of a map slot')
    return dict(config_sha256=image(data), config_bytes=len(data), config_version=version,
                fully_consumed=True, exact_replay=True, exact_slot_roster=True, research_only=True,
                master_present=master is not None,
                master_inherited_links={} if master is None else {key: describe(master.get(key)) for key in INHERITED},
                master_legacy_count=count, master_children=[describe(node) for node in children],
                positive_populated_observed=bool(slots),
                later_body_count=None if modern is None else len(modern),
                legacy_wire_observations=observations)


def main():
    parser = ArgumentParser(description='Check a digest-pinned native Config stream against the provisional sheet-metal child layout')
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--part', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    with args.part.open('rb') as handle:
        source = handle.read(MAX_PART + 1)
    digest = image(source)
    if not source or len(source) > MAX_PART or digest != args.sha256:
        parser.error('part is empty, oversized or differs from its supplied digest')
    git = ['git', '--no-replace-objects', '-C', str(args.reference)]
    clean_env = {key: value for key, value in os.environ.items()
                 if not key.upper().startswith('GIT_')}
    with TemporaryDirectory(prefix='KitSheetMetal') as temporary:
        root = Path(temporary)
        archive = root / 'Reference.tar'
        serial = 're/tooling/sw2026/serial'
        for arguments in ([REFERENCE, 'src'], [f'--prefix={serial}/', f'{REFERENCE}:{serial}']):
            with archive.open('wb') as output:
                subprocess.run([*git, 'archive', *arguments], check=True,
                               stdout=output, env=clean_env, timeout=90)
            with open_tar(archive) as payload:
                payload.extractall(root, filter='data')
        sys.path[:0] = [str(root / 'src'), str(root / 're/tooling/sw2026/serial')]
        from Classes import registry
        from Core import ArchiveError
        from convert.adapters.solidworks.Container.Container import SldprtArchive
        try:
            result = inspect(SldprtArchive.from_bytes(source), registry, 'Contents/Config-0')
        except (ArchiveError, ValueError, KeyError) as error:
            print(json.dumps(dict(source_sha256=digest, reference_revision=REFERENCE,
                                  research_only=True, exact_replay=False,
                                  error_type=type(error).__name__, diagnostic=str(error)[:350])))
            return 2
    print(json.dumps(dict(source_sha256=image(source), reference_revision=REFERENCE, **result), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())