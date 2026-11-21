from dataclasses import dataclass
from math import cos, pi, sin, sqrt

from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame

from StockCutPlan import AnnularSection, StockCutPlan


@dataclass(frozen=True, slots=True)
class BodyMeasure:
    volume_m3: float
    area_m2: float
    centre_m: tuple[float, float, float]
    face_count: int


def world_point(frame, u, v, normal):
    return tuple(origin + u * du + v * dv + normal * dn for origin, du, dv, dn
                 in zip(frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue, strict=True))


def stock_measure(axis, frame, section: AnnularSection):
    inner, outer = section.radial
    low, high = section.axial
    volume = pi * (outer ** 2 - inner ** 2) * (high - low)
    area = 2 * pi * ((inner + outer) * (high - low) + outer ** 2 - inner ** 2)
    return BodyMeasure(volume, area, world_point(frame, axis, (low + high) / 2, 0), 4)


def bbox_measure(axis, frame, section: AnnularSection):
    low, high = section.axial
    radius = section.radial[1]
    return world_point(frame, axis, (low + high) / 2, 0), sqrt((high - low) ** 2 + 8 * radius ** 2)


def cut_measure(plan: StockCutPlan):
    operation = plan.operations[2]
    axis = operation.AxisStart[0]
    frame = PrincipalFrame(operation.AxisValue)
    stock_bounds, tool_bounds = plan.sections[plan.selected_index], plan.sections[2]
    selected = stock_measure(axis, frame, stock_bounds)
    untouched = stock_measure(axis, frame, plan.sections[1 - plan.selected_index])
    theta = operation.AngleValue
    inner, outer = plan.radial_overlap
    low, high = tool_bounds.axial
    radial_square = outer ** 2 - inner ** 2
    axial = high - low
    removed = 0.5 * theta * axial * radial_square
    radial_moment = 2 * (outer ** 3 - inner ** 3) / (3 * theta * radial_square)
    tool_centre = world_point(frame, axis + radial_moment * sin(theta), (low + high) / 2,
                              -radial_moment * (1 - cos(theta)))
    volume = selected.volume_m3 - removed
    result_centre = tuple((selected.volume_m3 * stock_coord - removed * cut_coord) / volume
                          for stock_coord, cut_coord in zip(selected.centre_m, tool_centre, strict=True))
    wall_delta = (inner - outer) if plan.reached_wall == "outer" else (outer - inner)
    area = selected.area_m2 + theta * (axial * wall_delta + radial_square) + 2 * axial * (outer - inner)
    return untouched, BodyMeasure(volume, area, result_centre, 9)
