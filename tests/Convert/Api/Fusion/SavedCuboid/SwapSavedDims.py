from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# each list can retain its own ordering while both dimensions refer to their actual independent model drivers
def SwapSavedDims(
    Model: DocumentModel, ReverseDrivers: bool, ReverseCompute: bool
) -> DocumentModel:
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Sketch = Context.Sketch
    Dimensions = SeriesItems(Sketch.Fields["dimensions"])
    Changed = ChangeField(
        Model, Sketch.ObjectId, "dimensions", ValueSeries(Dimensions[::-1])
    )
    Feature = Context.SketchFeature
    Bindings = SeriesItems(Feature.Fields["dcParameters"])
    if ReverseDrivers:
        Changed = ChangeField(
            Changed, Feature.ObjectId, "dcParameters", ValueSeries(Bindings[::-1])
        )
    if ReverseCompute:
        Compute = Graph.OneClass("DcComputeManager")
        Order = SeriesItems(Compute.Fields["sortedNodesAll"])
        First, Second = (Order.index(Binding) for Binding in Bindings)
        Values = list(Order)
        Values[First], Values[Second] = Values[Second], Values[First]
        Changed = ChangeField(
            Changed, Compute.ObjectId, "sortedNodesAll", ValueSeries(tuple(Values))
        )
    return Changed
