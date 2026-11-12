from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GeoValue import GeoValue
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.TextValue import TextValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.VertexFormat import VertexFormat
from convert.formats.Fusion.GraphicsCodec.Model.Values.IndexData import IndexData
from convert.formats.Fusion.GraphicsCodec.Model.Values.StyleValue import StyleValue

KObjectValue = GroupValue | GeoValue | TextValue | VertexFormat | IndexData | StyleValue
