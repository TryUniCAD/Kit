from math import isclose

from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings


def signed_geometry(model):
    rings = ReadMassRings(model)
    total = 0.0
    for ring in rings:
        assert len(ring) >= 3
        first = ring[0]
        for index in range(1, len(ring) - 1):
            second, third = ring[index], ring[index + 1]
            total += (first.x * (second.y * third.z - second.z * third.y)
                      + first.y * (second.z * third.x - second.x * third.z)
                      + first.z * (second.x * third.y - second.y * third.x)) / 6.0
    return len(rings), total


def check_geometry(document, case):
    model = document.brep
    assert model is not None
    ids = frozenset(body.id for body in document.bodies)
    assert not model.validate(ids)
    assert len(model.bodies) == 1 and all(shell.closed for shell in model.shells)
    counts = [len(model.faces), len(model.edges), len(model.vertices)]
    assert counts == case["topology"], (case["role"], counts)
    result = {"topology": counts, "closed_shells": len(model.shells)}
    if case["expected_planar_rings"] is not None:
        ring_count, volume = signed_geometry(model)
        assert ring_count == case["expected_planar_rings"] and volume > 0.0
        assert isclose(volume, case["volume_mm3"], rel_tol=0.0, abs_tol=1e-8)
        result.update(directed_rings=ring_count, signed_volume_mm3=volume)
    return result
