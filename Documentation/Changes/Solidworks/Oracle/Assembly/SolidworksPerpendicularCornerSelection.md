# Select the actual lower-left corner for native source authoring

The perpendicular source author identifies the point matching both
axis minima within the existing geometric tolerance. The previous
point selection could choose the wrong end of the left edge when
its two X values differed by rounding noise.

The D02 native retry passes the four-corner and independent geometry
checks. Both controls pass. Its remaining source failure concerns the
order of returned mate endpoints.

[Controlled source results](../../../../../re/solidworks/measurements/2026/PerpendicularMateSourcePosition04.json)
