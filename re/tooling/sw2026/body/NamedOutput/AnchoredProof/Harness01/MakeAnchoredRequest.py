from dataclasses import replace

from MakeNamedRequest import request as named_request
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput


def request(case):
    if case['anchor_kind'] not in ('corner', 'center'):
        raise ValueError('an explicit supported origin anchor is required')
    document, settings, dimensions = named_request(case)
    document = replace(document,
        sketches=(replace(document.sketches[0], name='AnchorSketch'),),
        feature_timeline=(replace(document.feature_timeline[0], name='AnchorBoss'),))
    width, height = (case['part'][name] * 0.001 for name in ('width_mm', 'height_mm'))
    left, bottom = (0.0, 0.0) if case['anchor_kind'] == 'corner' else (-width / 2, -height / 2)
    dimensions = RectDimInput((left + width / 2, bottom - height * 0.3),
        (left + width * 1.3, bottom + height / 2), settings.DesignIntent,
        settings.SelectedLeader, False)
    return document, settings, dimensions
