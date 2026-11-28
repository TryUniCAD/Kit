# Windows can refuse a cold circle write before checking its receipt

A strict cold circle read identifies the complete measured archive. A
Windows path write uses the actual destination as its encoded locator.
Regenerating at a different path changes the archive and fails the cold
readback comparison before the exact receipt check. A binary stream can
retain the original locator and reproduce the measured bytes.

Check the specific cold-read refusal and the unchanged destination on
Windows. Keep the exact receipt guard for unmeasured output.
See [cold circle republication](../../../Changes/Solidworks/Construction/SolidworksColdCircleRepublication.md).
