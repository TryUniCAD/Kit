from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe


# the closed circular seam needs complete recursive adjacency rather than an edge label alone
def CheckRimVertex(Value: EdgeRecipe) -> None:
    if len(Value.AdjacentVertices) != 1:
        raise ValueError("Native rim selection requires one closed circular seam")
    Vertex = Value.AdjacentVertices[0]
    if (
        Vertex.PrimaryTagIndex != -1
        or Vertex.AdjacentFaces != Value.AdjacentFaces
        or Vertex.AdjacentEdges != (EdgeRecipe(0, -1, (), (), -1),)
        or len(Vertex.UvOrders) != 1
        or Vertex.UvOrders[0].KeyValue != 0
    ):
        raise ValueError("Native rim seam adjacency is not qualified")
    Orders = Vertex.UvOrders[0].Value
    if (
        Orders.FaceVertexCount,
        Orders.UOrder,
        Orders.ULowerOrder,
        Orders.UUpperOrder,
        Orders.VOrder,
        Orders.VLowerOrder,
        Orders.VUpperOrder,
    ) != (2, 2, 2, 2, 1, 0, 1):
        raise ValueError("Native rim seam ordering is not qualified")
