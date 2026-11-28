# Windows can select an embedded browser instead of the SOLIDWORKS frame

When catalogue authoring hides SOLIDWORKS, the visible window that Windows
reports as its main window can belong to an embedded component. In the 28 mm
cut-extrude replay at `1bbad52da2fc89787b0aa7cbf038a1b256d7deee`, the reported
handle `0x900b8a` belonged to an `Internet Explorer_Hidden` window. The actual
SOLIDWORKS frame remained hidden and enabled. A window close was successfully
posted through the generic Windows process API, and the owned process still
needed forced cleanup.

Read `IFrame.GetHWndx64` before releasing the COM connection. Check that the
handle still belongs to the exact owned process before sending `WM_CLOSE`.
The original process handle and the normal-exit receipt remain required to
advance to fresh reopen. [SOLIDWORKS frame API](https://help.solidworks.com/2021/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFrame~GetHWndx64.html)
