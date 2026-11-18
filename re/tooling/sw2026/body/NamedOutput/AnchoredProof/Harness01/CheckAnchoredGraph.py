from math import isclose


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_graph(candidate, kind, document):
    profile = candidate.ProfileValue
    geometry = profile.GeometryValue
    sketch = geometry.SketchValue
    fields = sketch.FieldsValue
    points, lines, dims = fields['points'], fields['lines'], fields['dims']
    center = kind == 'center'
    expected = (6, 6, 3) if center else (5, 4, 1)
    require((fields['npoints'], fields['nlines'], dims['nlog2']) == expected,
        'anchor point line and coincidence counts do not represent the actual intent')
    require(len(points) == expected[0] and len(lines) == expected[1]
        and len(dims['log_g2']) == expected[2] and dims['ng2'] == 2 and dims['nlog1'] == 4,
        'complete anchor arrays and driver groups disagree')
    require(len(geometry.PointValues) == len(geometry.LineValues) == 4,
        'construction geometry replaced the actual original boss contour')
    for index, point in enumerate(geometry.PointValues):
        require(points[index]['kind'] == 0 and points[index]['point'] is point.FieldsValue,
            'the original contour point does not own its actual published row')
    for index, line in enumerate(geometry.LineValues):
        require(lines[index]['flags'] == 0 and lines[index]['line'] is line.FieldsValue,
            'the original contour line does not own its actual published row')
    relations = [row['d'] for row in dims['log_g2']]
    for row in relations:
        require(row['f80'] == 9 and row['_sketch'] is sketch,
            'coincidence lost the actual sketch owner or native semantic kind')
        for key in ('h1','h2'):
            handle = row[key]
            require(handle.FieldsValue['_sketch'] is sketch,
                'coincidence references a foreign sketch')
            index = handle.FieldsValue['f18']
            require(handle.FieldsValue['idx'] == index,
                'compact and extended actual anchor handles disagree')
            if handle.ClassValue.NameValue == 'sgPointHandle':
                require(handle.FieldsValue['_point'].FieldsValue is points[index]['point'],
                    'point handle does not select its exact owned row')
            elif handle.ClassValue.NameValue == 'sgLineHandle':
                require(handle.FieldsValue['_line'].FieldsValue is lines[index]['line'],
                    'line handle does not select its exact owned row')
            else:
                raise ValueError('unknown anchor handle family')
    ext = points[-1]['point']
    require(points[-1]['kind'] == 1 and ext['pos'] == {'x':0.0,'y':0.0},
        'anchor did not allocate its separate actual external origin')
    external = ext['ext']
    wrapper = external.FieldsValue['f08']
    selection = wrapper.FieldsValue['f58']
    origin = candidate.SystemValue.OriginValue
    actual = selection.FieldsValue['f0f8']
    require(actual.FieldsValue['_sketch'] is origin.SketchValue
        and actual.FieldsValue['_point'] is origin.PointValue
        and selection.FieldsValue['ff0']['f00'] == origin.ProfileValue.FieldsValue['f08']
        and selection.FieldsValue['f100'] == origin.PointValue.FieldsValue['f0c'],
        'external origin does not bind the actual same model origin and point')
    require(origin.ProfileValue.FieldsValue['owner'] is candidate.SystemValue.RootValue,
        'the origin belongs to another part')
    target = 4 if center else 0
    last = relations[-1]
    require(last['h1'].FieldsValue['f18'] == len(points)-1
        and last['h2'].FieldsValue['f18'] == target
        and last['h1'].FieldsValue['_point'] is not last['h2'].FieldsValue['_point'],
        'origin coincidence collapsed distinct external and local identity')
    if center:
        require(points[4]['kind'] == 0 and points[4]['point']['fe4'] == 1
            and points[4]['point']['pos'] == {'x':0.0,'y':0.0},
            'center point lacks its actual origin centered role')
        for index, row in enumerate(lines[4:]):
            line = row['line']
            require(row['flags'] == 2 and line['f54'] & 8 and line['fc8'] == index
                and line['fcc'] == index+2 and line['_start'] is geometry.PointValues[index]
                and line['_end'] is geometry.PointValues[index+2],
                'construction diagonal no longer connects actual opposite corners')
            relation = relations[index]
            require(relation['h1'].FieldsValue['f18'] == 4
                and relation['h2'].ClassValue.NameValue == 'sgLineHandle'
                and relation['h2'].FieldsValue['f18'] == index+4,
                'center point is not bound to both actual diagonal owners')
    for index, row in enumerate(dims['val_g2']):
        parameter = row['d'].FieldsValue['f28']
        require(parameter.FieldsValue['owner'] is profile.ProfileValue
            and parameter.FieldsValue['f18'].FieldsValue['f08'] == document.parameters[index].name
            and isclose(parameter.FieldsValue['f58'], document.parameters[index].value.value * 0.001, rel_tol=1e-12),
            'anchor changed an actual sketch driver owner name or length')
    depth = candidate.BossValue.DimensionsValue[0].ParameterValue
    require(depth.FieldsValue['owner'] is candidate.BossValue.FeatureValue
        and depth.FieldsValue['f18'].FieldsValue['f08'] == document.parameters[2].name,
        'anchor changed the real leaf depth driver name or owner')
    return {'kind':kind,'point_count':len(points),'line_count':len(lines),'boundary_points':4,
        'boundary_lines':4,'construction_diagonals':2 if center else 0,
        'coincidence_count':len(relations),'point_distance_drivers':2,'axis_relations':4,
        'actual_model_origin_bound':True,'distinct_external_local_handles':True,
        'actual_body_contour_preserved':True,'all_three_driver_owners_preserved':True}
