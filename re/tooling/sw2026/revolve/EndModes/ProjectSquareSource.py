from math import isclose, radians

from AuditEqualLengthRows import inspect
from SquareEdgeRoles import contour_roles, edge_role
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners


def square_source(raw, case):
    structural = inspect(raw)
    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    owner, = ReadRevOwners(link)
    equal = owner.ProfileGraph.EqualValue
    assert equal is not None
    loop = owner.ProfileGraph.LoopValue
    lines = {line.IndexValue: line for line in loop.LinesValue}
    role_map = {}
    roles = contour_roles(case)
    for index, line in lines.items():
        positions = [tuple(value * 0.001 for value in loop.PointsValue[i].PositionValue)
                     for i in (line.StartValue, line.EndValue)]
        role_map[index] = edge_role(roles, positions)
    assert len(role_map) == len(set(role_map.values())) == 4
    assert tuple(equal.Indices) == tuple(structural["binary_equal_owners"])
    end = owner.EndValue
    assert end.ModeValue == {"midplane": "symmetric_full", "two": "two_sided"}[case["mode"]]
    assert owner.IsReverse == case["reverse"]
    assert isclose(end.AlongValue.RadiansValue, radians(case["angle_deg"]), rel_tol=1e-13)
    if case["mode"] == "two":
        assert end.AgainstValue is not None and isclose(end.AgainstValue.RadiansValue, radians(case["second_deg"]), rel_tol=1e-13)
    return tuple(role_map[index] for index in equal.Indices), structural
