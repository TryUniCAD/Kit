# SOLIDWORKS assembly display-state names

The public assembly reader projects the display-state label from `swDisplayStateName`. Files with only `swName` retain their existing label.

Read `CadDocument.assembly.attributes["display_states"]` after opening a native assembly. Each entry retains its original XML attributes and any declared configuration identity.

The disclosed D01 source and the native-saved radial discriminator both store `Display State-1` in the display-state attribute. Normal SDK reads project that label after the correction. Repository CI provides the existing assembly XML integration path for both spellings. [Root audit](../../../../../re/solidworks/records/ConcentricParentRootAudit2026.md) · [Display-state attribute gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Assembly/DisplayStateNamesHaveTheirOwnAttribute.md)
