from __future__ import annotations

import math
from dataclasses import dataclass

from builders.Definition import identity_transform
from builders.Metadata import fields, integer, text
from builders.Units import LENGTH_CODES


_METRES_PER_INCH = 0.0254
_ANSI_A_LANDSCAPE = (11 * _METRES_PER_INCH, 8.5 * _METRES_PER_INCH)
_METRIC_LENGTHS = frozenset({"mm", "cm", "m", "angstrom", "nm", "um"})
_METRIC_ZONES = (
    (0.01, 1), (0.05, 2), (0.21, 4), (0.297, 6),
    (0.42, 8), (0.594, 12), (0.841, 16), (1.189, 24),
)
_INCH_ZONES = tuple(
    (threshold, count) for threshold, count in (
        (0.01, 1),
        (2 * _METRES_PER_INCH, 2),
        (17 * _METRES_PER_INCH, 4),
        (28 * _METRES_PER_INCH, 6),
        (34 * _METRES_PER_INCH, 8),
    )
)


def _positive_dimension(value, label):
    if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"drawing {label} must be a finite positive measurement")
    return float(value)


def _zones_for_axis(size, *, table, normal_margin):
    margin = min(normal_margin, size * 0.5 - 0.005)
    for index, (limit, count) in enumerate(table):
        if limit <= size and (index + 1 == len(table) or size < table[index + 1][0] - 1e-8):
            return count, margin
    return 1, margin


def default_zones(*, width, height, length_unit):
    width = _positive_dimension(width, "paper width")
    height = _positive_dimension(height, "paper height")
    if length_unit not in LENGTH_CODES:
        raise ValueError("drawing zone policy requires an admitted document length unit")
    if min(width, height) < 0.01:
        return 1, 1, 0.0, 0.0
    metric = length_unit in _METRIC_LENGTHS
    table = _METRIC_ZONES if metric else _INCH_ZONES
    normal_margin = 0.01 if metric else _METRES_PER_INCH * 0.5
    columns, horizontal = _zones_for_axis(width, table=table, normal_margin=normal_margin)
    rows, vertical = _zones_for_axis(height, table=table, normal_margin=normal_margin)
    return columns, rows, horizontal, vertical


def _paper_text(value, label):
    value = text(value, label)
    if not value or "@" in value:
        raise ValueError(f"{label} must be nonempty and cannot contain the drawing index delimiter")
    return value


@dataclass(frozen=True, kw_only=True)
class DrawingSheet:
    name: str
    paper_size: str
    scale_numerator: int
    scale_denominator: int
    length_unit: str
    custom_property_view: str

    def __post_init__(self):
        _paper_text(self.name, "sheet name")
        _paper_text(self.custom_property_view, "sheet property view")
        if self.paper_size != "ansi-a-landscape":
            raise ValueError("unformatted paper construction supports ANSI A landscape")
        integer(self.scale_numerator, "sheet scale numerator", low=1, high=999999)
        integer(self.scale_denominator, "sheet scale denominator", low=1, high=999999)
        if self.length_unit not in LENGTH_CODES:
            raise ValueError("unsupported semantic drawing length unit")

    @property
    def dimensions(self):
        return _ANSI_A_LANDSCAPE

    @property
    def native_paper_code(self):
        return 0

    @property
    def native_paper_name(self):
        return "A_H"

    @property
    def native_template_name(self):
        return "*.drt"

    @property
    def scale(self):
        return self.scale_numerator / self.scale_denominator

    def model_sketch_frame(self):
        return {**identity_transform(), "f70": 1.0 / self.scale}

    def ui_sketch_frame(self):
        return {**identity_transform(), "f70": self.scale}

    def authored_fields(self):
        width, height = self.dimensions
        columns, rows, horizontal, vertical = default_zones(
            width=width, height=height, length_unit=self.length_unit
        )
        return {
            "f3f8": float(self.scale_numerator), "f400": float(self.scale_denominator),
            "f39c": self.native_paper_code, "f3c0": 13,
            "f3e8": height, "f3f0": width, "f3b8": self.native_template_name,
            "f3d0": self.custom_property_view,
            "f4a8": horizontal, "f4b0": horizontal, "f4b8": vertical, "f4c0": vertical,
            "f4c8": columns, "f4cc": rows, "f4d8": 1,
        }


def drawing_sheet(request):
    return DrawingSheet(**fields(
        request, "drawing sheet",
        ("name", "paper_size", "scale_numerator", "scale_denominator", "length_unit", "custom_property_view"),
    ))
