from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import (
    TcoedgeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TedgeNode import TedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TvertexNode import (
    TvertexNode,
)

KComplexEntity: TypeAlias = (
    SplineNode | IntcurveNode | PcurveNode | TcoedgeNode | TedgeNode | TvertexNode
)

KComplexTypes = (
    SplineNode,
    IntcurveNode,
    PcurveNode,
    TcoedgeNode,
    TedgeNode,
    TvertexNode,
)
