def predict_tree(spec):
    folders = (
        ('Comments', 'CommentsFolder'), ('Favorites', 'FavoriteFolder'), ('History', 'HistoryFolder'),
        ('Selection Sets', 'SelectionSetFolder'), ('Sensors', 'SensorFolder'), ('Design Binder', 'DocsFolder'),
        ('Surface Bodies', 'SurfaceBodyFolder'), ('Solid Bodies', 'SolidBodyFolder'),
        ('Lights and Cameras', 'EnvFolder'), ('Markups', 'InkMarkupFolder'),
        ('Equations', 'EqnFolder'), ('Material <not specified>', 'MaterialFolder'))
    rows = []
    for name, kind in folders:
        rows.append([name, kind, None])
        if kind == 'DocsFolder':
            rows += [['Annotations', 'DetailCabinet', None], ['Notes', 'NotesAreaFtrFolder', 'Annotations'],
                ['Notes1___EndTag___', 'NotesAreaFtrFolder', 'Annotations']]
        if kind == 'EnvFolder':
            rows += [['Ambient', 'AmbientLight', name]]
            rows += [[f'Directional{index}', 'DirectionLight', name] for index in (1, 2, 3)]
    rows += [[name, 'RefPlane', None] for name in ('Front Plane', 'Top Plane', 'Right Plane')]
    rows += [['Origin', 'OriginProfileFeature', None], ['RevolveSketch', 'ProfileFeature', None],
        ['OrdinaryBossRevolve', 'Revolution', None]]
    if len(rows) != 25:
        raise ValueError('revolve neutral system recipe does not predict a complete ordinary tree')
    return rows
