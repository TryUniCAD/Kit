from dataclasses import replace
from types import MappingProxyType


def require(value, message):
    if not value:
        raise ValueError('concentric neutral brep: ' + message)


def check_complete_brep(actual, expected):
    require(type(actual) is type(expected) and actual.schema_version == expected.schema_version,
            'the complete ordinary model schema is required')
    identifiers = {}
    groups = (
        ('vertices', ()), ('curves', ()), ('surfaces', ()), ('pcurves', ()),
        ('edges', ('start_vertex_id', 'end_vertex_id', 'curve_id')),
        ('coedges', ('edge_id', 'pcurve_id')),
        ('loops', ('coedge_ids',)), ('wires', ('coedge_ids',)),
        ('faces', ('surface_id', 'loop_ids')),
        ('face_uses', ('face_id',)), ('shells', ('face_use_ids',)),
        ('shell_uses', ('shell_id',)), ('regions', ('shell_use_ids',)),
        ('bodies', ('region_ids', 'wire_ids', 'vertex_ids')),
    )
    for name, references in groups:
        rows = getattr(actual, name)
        target_rows = getattr(expected, name)
        require(len(rows) == len(target_rows), name + ' has unrepresented or missing records')
        used = set()
        for row in rows:
            updates = {}
            for field in references:
                value = getattr(row, field)
                if type(value) is tuple:
                    require(all(member in identifiers for member in value), name + ' has an unresolved owned reference')
                    updates[field] = tuple(identifiers[member] for member in value)
                else:
                    require(not value or value in identifiers, name + ' has an unresolved owned reference')
                    updates[field] = identifiers[value] if value else value
            matches = tuple(target for target in target_rows if type(row) is type(target)
                            and replace(row, id=target.id, **updates) == target)
            require(len(matches) == 1 and matches[0].id not in used,
                    name + ' differs from the complete independently reconstructed ordinary model or has ambiguous ownership')
            require(row.id not in identifiers, 'the neutral graph reuses an entity identity')
            identifiers[row.id] = matches[0].id
            used.add(matches[0].id)
    return MappingProxyType(identifiers)
