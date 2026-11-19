# The drawing extension dependency call can throw on a pristine file

`IModelDocExtension.GetDependencies(True, False, False, True, True)` is
documented as a model dependency inspection. In the exact SOLIDWORKS 2026
SP05.2 drawing batch it returned COM error `-2147417851` on both clean
read-only opens of the pristine unlinked drawing. One process then lost its
COM close methods. The note phases remained unexecuted.

Keep the two controls and preserve the interruption as observer evidence.
Test a file-level dependency query before introducing it into an acceptance
batch, and retain sheet view enumeration as an independent measurement.
After a failed COM exit, verify an owned read-only process by its recorded
creation identity and executable digest before clearing it.

[Documented extension query](https://help.solidworks.com/2019/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~GetDependencies.html) · [Control receipt](../../../../../../re/solidworks/measurements/2026/PlainDrawingNotePresentationObserverFailure01.json)
