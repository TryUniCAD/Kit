# FreeCAD cylinder companion source preparation

The research runner prepares two disclosed SOLIDWORKS source requests from independently authored origin-aligned FreeCAD cylinders. It checks that each strict neutral model retains the actual `Part::Cylinder` owner, its radius and height drivers, and the source file hash. Independent equations verify volume, surface area and centre of mass.

The native source requests model a radius-driven Front Plane circle and a forward blind depth. Each calls for separate radius and depth edits. Native authoring and the first-writer held-out locks remain pending. [Host source deck](../../../../../re/solidworks/measurements/2026/FreecadCylinderSourceDeck01.json) [Preparation tool](../../../../../re/tooling/sw2026/freecad_cylinder/PrepareSourceDeck.py)
