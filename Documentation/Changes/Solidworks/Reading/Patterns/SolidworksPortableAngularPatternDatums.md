# Preserve editable oblique pattern datums in the neutral model

The strict SOLIDWORKS 2026 part reader projects the measured finite hinge as a portable plane-intersection axis and the angular plane as a bound construction feature. It retains both ordered principal plane selections, both exact finite endpoints, the angular plane's actual base and hinge, and the original driving D1 in radians. The hinge-coincidence offset is a derived zero.

Six cache-free generated variants and four native-saved disclosures retain the complete typed datum graph through ordinary neutral JSON round trips. The saved variants retain their prior body geometry and scoped pattern semantics. The bounded public native writer remains closed for these documents. [Verification](../../../../../re/solidworks/records/SdkPortableAngularDatums2026.md)
