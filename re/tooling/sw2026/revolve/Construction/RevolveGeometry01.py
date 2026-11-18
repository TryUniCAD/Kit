from math import radians, sin, cos, tau


def predict_geometry(spec, angle_degrees):
    inner, outer = (value / 1000 for value in spec['radial_mm'])
    low, high = (value / 1000 for value in spec['axial_mm'])
    theta = radians(angle_degrees)
    height = high - low
    moment = (outer * outer - inner * inner) / 2
    volume = height * theta * moment
    surface = theta * (height * (outer + inner) + 2 * moment)
    if theta != tau:
        surface += 2 * height * (outer - inner)
    mean_radius = (outer**3 - inner**3) / (3 * moment)
    center = [spec['axis_x_mm'] / 1000 + mean_radius * sin(theta) / theta,
        (low + high) / 2, (1 if spec['reverse'] else -1) * mean_radius * (1 - cos(theta)) / theta]
    return {'body_count': 1, 'volume_m3': volume, 'area_m2': surface,
        'center_of_mass_m': center, 'angle_rad': theta, 'reverse': spec['reverse'],
        'axis_points_m': [[spec['axis_x_mm'] / 1000, value / 1000, 0.0] for value in spec['axis_span_mm']]}


def predict_case(spec):
    return {'initial': predict_geometry(spec, spec['angle_deg']),
        'edited': predict_geometry(spec, spec['edit_angle_deg']),
        'source_kind': 'independently_authored_disclosed_neutral',
        'native_qualified': False, 'heldout_qualified': False}
