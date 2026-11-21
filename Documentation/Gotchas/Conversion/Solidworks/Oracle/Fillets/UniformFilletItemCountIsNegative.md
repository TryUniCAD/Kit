# A uniform fillet has a negative item count

On the disclosed SOLIDWORKS 2026 SP05.2 axial fillet, rollback selection access exposed one actual `IEdge` and `GetEdgeCount=1`. Native identity matched the edge independently found on the stock body. The same uniform-radius definition returned `FilletItemsCount=-1`. The vendor documents this sentinel for simple fillets with a uniform radius. [Native observation](../../../../../../re/solidworks/measurements/2026/EdgeFilletSourceAttempt02.json) · [Official item-count property](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISimpleFilletFeatureData2~FilletItemsCount.html)

Use `Edges` and `GetEdgeCount` for the selected-edge inventory in the uniform case. Keep the constant-radius mode, actual edge identity, and stock-ownership checks. The item count describes the separate multiple-radius inventory, so a uniform fillet does not need `GetFilletItemAtIndex`.
