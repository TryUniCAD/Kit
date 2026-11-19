from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path


def require(value, message):
    if not value:
        raise RuntimeError(message)


def vector(value, count):
    result = [float(item) for item in value]
    require(len(result) == count and all(math.isfinite(item) for item in result), 'invalid native finite vector')
    return result


def close_vector(author, label, actual, expected):
    require(len(actual) == len(expected), label + ' vector size differs')
    for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
        author.rec.close_number(f'{label}[{index}]', left, right, absolute=2e-9)


def endpoints_match(actual, expected):
    def same(left, right):
        return len(left) == len(right) and all(math.isclose(a, b, rel_tol=2e-7, abs_tol=2e-9) for a, b in zip(left, right, strict=True))
    return (same(actual[0], expected[0]) and same(actual[1], expected[1])) or (same(actual[0], expected[1]) and same(actual[1], expected[0]))


def edge_points(author, raw):
    edge = author.typed(raw, 'Edge')
    curve = author.typed(author.get(edge, 'GetCurve'), 'Curve')
    require(bool(author.get(curve, 'IsLine')), 'selected displayed edge is not an analytic line')
    points = []
    for method in ('GetStartVertex', 'GetEndVertex'):
        raw_vertex = author.get(edge, method)
        require(raw_vertex is not None, 'selected ordinary edge lacks a real endpoint')
        points.append(vector(author.get(author.typed(raw_vertex, 'Vertex'), 'GetPoint'), 3))
    require(any(abs(a - b) > 1e-10 for a, b in zip(*points, strict=True)), 'selected line edge is degenerate')
    return edge, points


def same_file(actual, paths, expected):
    path = Path(actual).resolve(strict=True)
    require(any(path == Path(item).resolve() or path.samefile(item) for item in paths), 'native object resolved an unapproved physical child')
    require(sha256(path.read_bytes()).hexdigest() == expected, 'native object resolved different child bytes')
    return path


def model_view(author, drawing, case):
    sentinel = author.typed(author.get(drawing, 'GetFirstView'), 'View')
    raw = author.get(sentinel, 'GetNextView')
    require(raw is not None, 'ordinary drawing lacks the expected model view')
    view = author.typed(raw, 'View')
    require(author.get(view, 'GetNextView') is None, 'ordinary drawing has extra model views')
    require(str(author.get(view, 'Name')) == case['expected']['view']['name'], 'drawing model view name differs')
    child = author.get(view, 'ReferencedDocument')
    require(child is not None, 'drawing has no resolved child model')
    child_path = same_file(author.get(child, 'GetPathName'), case['approved_child_paths'], case['part_sha256'])
    configuration = str(author.get(view, 'ReferencedConfiguration'))
    require(configuration == case['expected']['view']['configuration'], 'view references an unexpected configuration')
    active = author.get(author.get(child, 'ConfigurationManager'), 'ActiveConfiguration')
    require(str(author.get(active, 'Name')) == configuration, 'child active configuration differs from view')
    return view, child, child_path


def select_edge(author, drawing, case):
    view, child, child_path = model_view(author, drawing, case)
    components = list(author.get(view, 'GetVisibleComponents') or ())
    require(len(components) == 1, 'ordinary view must contain exactly one visible component')
    component = author.typed(components[0], 'Component2')
    same_file(author.get(component, 'GetPathName'), case['approved_child_paths'], case['part_sha256'])
    component_configuration = str(author.get(component, 'ReferencedConfiguration'))
    require(author.get(component, 'IsRoot') is True and author.get(component, 'GetParent') is None, 'visible component must be the actual standalone part root')
    require(component_configuration == '', 'standalone drawing part root unexpectedly owns an occurrence configuration')
    component_model = author.get(component, 'GetModelDoc2')
    require(component_model is not None, 'visible component model is unavailable')
    require(author.get(component_model, 'GetType') == author.get(child, 'GetType') == 1, 'visible root model must be the ordinary part child')
    require(author.get(author.app, 'IsSame', component_model, child) == 1, 'visible component belongs to a different model')
    component_active = author.get(author.get(component_model, 'ConfigurationManager'), 'ActiveConfiguration')
    actual_configuration = str(author.get(component_active, 'Name'))
    require(actual_configuration == case['expected']['view']['configuration'], 'actual part-root model active configuration differs from view')
    edges = list(author.get(view, 'GetVisibleEntities2', component, 1) or ())
    require(0 < len(edges) <= 256, 'visible ordinary edge inventory is empty or exceeds the bound')
    selected = []
    inventory = []
    for raw in edges:
        edge, points = edge_points(author, raw)
        inventory.append(points)
        if endpoints_match(points, case['edge_endpoints_m']):
            selected.append(edge)
    require(len(selected) == 1, 'analytic endpoint rule must select exactly one real visible edge')
    edge = selected[0]
    owner = author.get(author.typed(edge, 'Entity'), 'GetComponent')
    require(owner is not None and author.get(author.app, 'IsSame', owner, component) == 1, 'selected edge is not owned by the actual visible component')
    return view, child, edge, {'visible_edge_count': len(edges), 'visible_edge_endpoints_m': inventory,
                              'selected_endpoints_m': case['edge_endpoints_m'], 'actual_child_path': str(child_path),
                              'configuration': case['expected']['view']['configuration'], 'component_occurrence_configuration_observed': component_configuration,
                              'actual_component_model_configuration': actual_configuration, 'actual_part_root': True, 'actual_parent_null': True}


def persist_id(author, extension, entity):
    raw = author.get(extension, 'GetPersistReference3', entity)
    require(raw is not None, 'persistent edge reference is unavailable')
    data = bytes(raw)
    require(0 < len(data) <= 16384, 'persistent edge reference length is invalid')
    return data


def resolve_persist(author, extension, data):
    sw = author.sw
    encoded = sw.VARIANT(sw.pythoncom.VT_ARRAY | sw.pythoncom.VT_UI1, list(data))
    error = sw.byref_long()
    raw = author.get(extension, 'GetObjectByPersistReference3', encoded, error)
    require(raw is not None and int(error.value) == 0, 'persistent edge reference did not resolve successfully')
    return author.typed(raw, 'Edge')


def annotation_state(author, annotation, expected_text, expected_position, edge, endpoints):
    require(int(author.get(annotation, 'GetType')) == 6, 'the edited annotation is not a note')
    note = author.typed(author.get(annotation, 'GetSpecificAnnotation'), 'Note')
    require(str(author.get(note, 'GetText')) == expected_text, 'note text differs from explicit authored edit')
    position = vector(author.get(annotation, 'GetPosition'), 3)
    close_vector(author, 'annotation position', position, expected_position)
    attached = list(author.get(annotation, 'GetAttachedEntities3') or ())
    types = [int(item) for item in author.get(annotation, 'GetAttachedEntityTypes') or ()]
    require(len(attached) == 1 and attached[0] is not None and types == [1], 'note must be attached to exactly one actual edge')
    require(author.get(annotation, 'IsDangling') is False, 'the actual edge annotation is dangling')
    bound, points = edge_points(author, attached[0])
    require(endpoints_match(points, endpoints), 'annotation points at a different analytic edge')
    require(author.get(author.app, 'IsSame', bound, edge) == 1, 'annotation points at a different edge object')
    return {'name': str(author.get(annotation, 'GetName')), 'text': str(author.get(note, 'GetText')),
            'position_m': position, 'attachment_types': types, 'attachment_count': len(attached),
            'dangling': False, 'attached_endpoints_m': points, 'actual_edge_identity_matches': True}


def find_annotation(author, view, name):
    annotations = list(author.get(view, 'GetAnnotations') or ())
    require(len(annotations) <= 256, 'annotation inventory exceeds its bound')
    selected = [author.typed(raw, 'Annotation') for raw in annotations
                if str(author.get(author.typed(raw, 'Annotation'), 'GetName')) == name]
    require(len(selected) == 1, 'exact saved annotation name was not found uniquely on the actual view')
    return selected[0]


def create_note(author, drawing, view, edge, case):
    model = author.model
    require(bool(author.get(drawing, 'ActivateView', case['expected']['view']['name'])), 'actual model view could not be activated')
    author.get(model, 'ClearSelection2', True)
    require(bool(author.get(view, 'SelectEntity', edge, False)), 'view could not select its actual edge')
    note = author.typed(author.get(model, 'InsertNote', case['annotation']['before_text']), 'Note')
    annotation = author.typed(author.get(note, 'GetAnnotation'), 'Annotation')
    attached = author.sw.VARIANT(author.sw.pythoncom.VT_ARRAY | author.sw.pythoncom.VT_DISPATCH, (edge,))
    require(bool(author.get(annotation, 'SetAttachedEntities', attached)), 'native note did not accept the actual displayed edge')
    require(bool(author.get(annotation, 'SetPosition2', *case['annotation']['before_position_m'])), 'native note initial position failed')
    initial = annotation_state(author, annotation, case['annotation']['before_text'], case['annotation']['before_position_m'], edge, case['edge_endpoints_m'])
    require(bool(author.get(note, 'SetText', case['annotation']['after_text'])), 'native note text edit failed')
    require(bool(author.get(annotation, 'SetPosition2', *case['annotation']['after_position_m'])), 'native note position edit failed')
    author.get(model, 'ClearSelection2', True)
    return annotation, initial
