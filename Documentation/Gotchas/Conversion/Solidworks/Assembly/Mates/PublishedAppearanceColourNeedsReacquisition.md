# Reacquire the actual display-state appearance to verify colour

The creator's PrimaryColor readback retains the requested RGB after
native material publication. The published self-owned material instead
reports the installed asset colour. Setting the colour on the returned
material changes that COM wrapper's immediate readback. An independent
lookup returns another wrapper for the same material IDs and reports
the installed asset colour again.

Verify the actual selected state's material in an independent lookup
before saving the appearance. Both disclosed trials stop before save
with healthy controls. Their roughness readback stays at the requested
value through the measured publication stage.

[Controlled colour measurements](../../../../../../re/solidworks/measurements/2026/ConcentricChildAppearanceColourReacquisition01.json)
