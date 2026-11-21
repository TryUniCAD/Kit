from collections import defaultdict as Defaultdict
from dataclasses import dataclass as DataClass
from typing import Mapping

from convert.adapters.solidworks.Core.NativeDimension import NativeDimension
from interchange.geometry.Models.Sketch import SketchEntity


# this state exists because sketch rule resolution shares occurrence counters
@DataClass(slots=True)
class RuleContext:
    Candidates: Mapping[float, list[tuple[str, str]]]
    DimensionsByName: Mapping[str, list[NativeDimension]]
    ParamIdsByName: Mapping[str, list[str]]
    DimensionUsage: Defaultdict[float, int]
    ParamUsage: Defaultdict[str, int]
    RuleIdUsage: Defaultdict[str, int]
    ParamIds: set[str]
    MarkerCircles: tuple[SketchEntity, ...] = ()
