from AuthorCurves import require
from AuthorRevolveSources import RevolveAuthor


class SdkRevolveObserver(RevolveAuthor):
    expected_trees = {}

    def snapshot(self, case, label, angle_degrees):
        if label == 'reopened':
            require(self.rec.data.get('before_explicit_rebuild', {}).get('bodies') == 1,
                'generated revolve has no initial solid before explicit rebuild')
        feature = super().snapshot(case, label, angle_degrees)
        tree = self.feature_tree(required_names=('RevolveSketch', 'OrdinaryBossRevolve', 'Front Plane'))
        observed = [[row['name'], row['type'], row['parent']] for row in tree]
        require(observed == self.expected_trees[case['name']], 'complete generated revolve native tree differs')
        require(not any(row['suppressed'] for row in tree), 'generated revolve has a suppressed native feature')
        manager = self.get(self.sketch, 'RelationManager')
        relation_count = int(self.get(manager, 'GetRelationsCount', 0))
        require(relation_count == 4, 'generated revolve lost its four authored contour relations')
        profile = self.observe_profile()
        require(profile['configuration'] == 'Default', 'generated revolve active configuration differs')
        segments = profile['segments']
        contour = [row for row in segments if not row['construction']]
        axes = [row for row in segments if row['construction']]
        require(len(contour) == 4 and len(axes) == 1, 'generated revolve profile construction ownership differs')
        ri, ro = case['radius_m']
        low, high = case['axial_m']
        x = case['axis_x_m']
        corners = ((x+ri, low), (x+ro, low), (x+ro, high), (x+ri, high))
        expected = sorted(tuple(sorted((first, second))) for first, second in zip(corners, corners[1:]+corners[:1], strict=True))
        actual = sorted(tuple(sorted((tuple(row['start']), tuple(row['end'])))) for row in contour)
        for edge, target in zip(actual, expected, strict=True):
            for point, wanted in zip(edge, target, strict=True):
                require(len(point) == len(wanted) == 2, 'generated revolve sketch coordinate shape differs')
                for value, planned in zip(point, wanted, strict=True):
                    self.rec.close_number('authored contour coordinate m', value, planned, absolute=1e-12)
        sketch_feature = self.get(self.model, 'FeatureByName', 'RevolveSketch')
        sketch_dimensions = self.get(sketch_feature, 'GetFirstDisplayDimension')
        require(sketch_dimensions is None, 'generated revolve acquired an unrequested sketch driver')
        self.rec.data[label].update(complete_tree=tree, profile=profile, sketch_relation_count=relation_count,
            sketch_has_display_dimensions=False)
        self.rec.flush()
        return feature
