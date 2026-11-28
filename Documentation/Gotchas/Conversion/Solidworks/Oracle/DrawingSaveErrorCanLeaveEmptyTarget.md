# Failed drawing save can leave an empty target

The generated blank drawing passed native open, rebuild and an in-memory sheet scale edit. Its silent `IModelDocExtension.SaveAs3` then returned `[false,1,0]` and created an empty `.SLDDRW` at the target. The same operation saved and reopened the native reduction with the same seven input stream roles. [Controlled blank drawing receipt](../../../../../re/solidworks/measurements/2026/GeneratedBlankDrawingNative01.json) · [SaveAs3 API](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~SaveAs3.html?format=P&value=)

A valid save requires the API success status and a separately verified native derivative. Preserve the failed zero-byte file as a save-stage observation and keep it outside fresh reopen or acceptance counts.
