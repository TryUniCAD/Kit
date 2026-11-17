# Drawing save events need the explicit drawing event interface

The SOLIDWORKS 2026 blank drawing opened and the pinned type library loaded. `win32com.client.WithEvents` still called automatic makepy discovery on the document and raised `TypeError` before `SaveAs`. That exception describes observer setup. The affected controls produced no save measurement.

Use the pinned library's `DrawingDoc.default_source`, verify `DDrawingDocEvents` IID `{83A33D34-37C5-11CE-BFD4-00400513BB57}`, and bind its source initializer to the existing drawing interface. Put the event handlers first in the Python method resolution order and disconnect after the operation. Require a matching disclosed control to deliver events before interpreting a missing callback. [Probe and native call edges](../../../../../re/solidworks/records/DrawingSaveEvents2026.md)
