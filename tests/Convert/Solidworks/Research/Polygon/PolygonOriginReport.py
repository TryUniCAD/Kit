from __future__ import annotations

# constructor state must remain distinguishable from a completed native origin solve
KOriginReport = """
OriginReport = {
    'origin_flags': OriginPoint['pflags'], 'origin_type': OriginPoint['fe4'],
    'origin_relations': OriginSketch['dims']['nlog1'], 'origin_bytes': len(OriginBytes),
    'ordinary_origin_clear': all((Record['point']['pflags'] & 1) == 0 for Record in Profile.sketch['points']),
    'plane_reuse_blocked': ReuseBlocked, 'plane_wrappers_distinct': OriginPlane is not PlaneRef,
    'plane_owner_identity': OriginPlane['_profile_owner'] is OriginFeature and PlaneRef['_profile_owner'] is Profile.profile,
    'origin_pending_flags': OriginNode['f0c'],
    'origin_statuses': [OriginSketch['f128'], OriginSketch['f12c'], OriginPoint['f34']],
    'origin_colour': OriginPoint['f30'],
}
"""
