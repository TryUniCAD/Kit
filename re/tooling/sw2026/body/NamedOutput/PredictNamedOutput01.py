from math import isclose


def prediction(build):
    spec = build['spec']
    document = build['neutral_document']
    if document['units']['value'] != 'mm':
        raise ValueError('native naming discovery requires explicit millimetre neutral units')
    sketch, = document['sketches']['$tuple']
    feature, = document['feature_timeline']['$tuple']
    plane, = document['support_planes']['$tuple']
    body, = document['bodies']['$tuple']
    configuration, = document['configurations']['$tuple']
    if body['name'] != spec['body_label'] or body['final_feature_id'] != feature['id']:
        raise ValueError('native naming prediction requires the actual neutral body owner')
    width, height, depth = (spec[name]*0.001 for name in ('width_mm','height_mm','depth_mm'))
    centre_x, centre_y = (value*0.001 for value in spec['centre_xy_mm'])
    points = [[centre_x-width/2,centre_y-height/2],[centre_x+width/2,centre_y-height/2],
              [centre_x+width/2,centre_y+height/2],[centre_x-width/2,centre_y+height/2]]
    entities = sketch['entities']['$tuple']
    if len(entities) != 4:
        raise ValueError('native naming prediction requires the complete four-line sketch')
    for index, entity in enumerate(entities):
        for end, expected in (('start',points[index]),('end',points[(index+1)%4])):
            actual = entity['geometry'][end]
            if not all(isclose(actual[axis]*0.001,target,rel_tol=1e-12,abs_tol=1e-14)
                       for axis,target in zip(('x','y'),expected,strict=True)):
                raise ValueError('native naming prediction differs from the original neutral geometry')
    parameters = document['parameters']['$tuple']
    roles = ['depth'] if len(parameters) == 1 else ['width','height','depth']
    names = build['driver_names'] or ['D1']
    if len(parameters) != len(roles) or len(names) != len(roles):
        raise ValueError('native naming prediction has an unsupported driver inventory')
    owners = {sketch['id']:sketch['name'],feature['id']:feature['name']}
    drivers = []
    for role, parameter, name in zip(roles,parameters,names,strict=True):
        if parameter['name'] != name or parameter['value']['unit'] != 'mm':
            raise ValueError('native naming prediction lost an actual authored driver')
        owner = owners[parameter['owner_id']]
        drivers.append({'role':role,'name':name,'owner':owner,
            'reference':name+'@'+owner,'value_m':parameter['value']['value']*0.001})
    expected = {'width':width,'height':height,'depth':depth}
    if any(not isclose(row['value_m'],expected[row['role']],rel_tol=1e-12) for row in drivers):
        raise ValueError('native naming parameter and analytic dimensions differ')

    def prism(length):
        return {'body_count':1,'volume_m3':width*height*length,
            'area_m2':2*(width*height+(width+height)*length),
            'mass_kg':width*height*length,'centre_of_mass_m':[centre_x,centre_y,length/2]}

    edited = spec['edited_depth_mm']*0.001
    return {'body_label':body['name'],'expected_initial':prism(depth),
        'edit':{'dimension':drivers[-1]['reference'],'new_depth_m':edited,'expected':prism(edited)},
        'intent':{'model_name':spec['model_name'],'self_path':spec['self_path'],
            'configuration_name':configuration['name'],'profile':sketch['name'],'feature':feature['name'],
            'support':plane['name'],'vertices_m':points,'sketch_lines':4,'resolved_roots':19,
            'coordinate_frame':'local_front_xy','width_mm':spec['width_mm'],'height_mm':spec['height_mm'],
            'depth_m':depth,'relation_count':len(sketch['constraints']['$tuple']),
            'has_sketch_display_dimensions':len(parameters)==3,'drivers':drivers}}
