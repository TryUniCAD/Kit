# An implicit cylinder name needs its body owner

An ordinary saved SOLIDWORKS cylinder can have a null archive atom name and still carry a body-owned `SWIMPLICITBODYNAME_ID_U`. The Solid Bodies folder caption describes the tree folder. The matching extrusion label describes the feature. A reader must resolve the actual selected partition, body attribute, reciprocal atom and producer before exposing the kernel label on the neutral body.

The saved cylinder's two closed circular rims transmit no vertex records. The public B-rep decoder derives one seam vertex per rim. Validate those derived vertices against their actual curves and retain their neutral ownership. A cache-free cylinder instead has its computed B-rep and actual typed producer. That route carries no native body or face identity. [Ownership evidence](../../../../../../re/solidworks/records/ImplicitCylinderBodyNames2026.md)
