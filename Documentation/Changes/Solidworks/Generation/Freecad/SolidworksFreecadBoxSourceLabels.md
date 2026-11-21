# Preserve FreeCAD origin box source labels

The internal SOLIDWORKS origin-box generator can use a disclosed FreeCAD part's actual body label and the property names of its three driving dimensions. Add `"preserve_source_labels": true` to the existing neutral JSON request for `re/tooling/sw2026/SdkFreecadBoxProcess.py`. The ordinary request generates its existing parameter names.

The measured F14a body retains `Body` and its native drivers retain `Length`, `Width` and `Height` through independent edits, native save and fresh reopen. Both candidate files pass the public SOLIDWORKS reader and six linked archive comparisons each. The scoped result covers one disclosed origin-fixed FreeCAD 0.21.2 AdditiveBox. Public FreeCAD-to-SOLIDWORKS registration and original corpus qualification remain open. [Measurement receipt](../../../../../re/solidworks/measurements/2026/SdkFreecadBoxSourceNames01.json)
