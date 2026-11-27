# SOLIDWORKS absolute depth units

The SOLIDWORKS research encoder now applies absolute depth edits in millimetres even when an authored request stores its driving length in metres or inches. Pass `{"dimension": "depth", "value_mm": 19.87}` to `prepare_generation_input`. The native-source research command passes its `--depth-mm` value through the same edit path after source admission. Both the D1 parameter and the linked blind extrusion receive the same typed length. The existing no-op check compares the exact planned native depth before and after the edit.

Run `python -I -B re/solidworks/EncoderBoundary/CheckDepthUnits.py` to replay the two authored cases. Fresh offline processes edited metre and inch requests to 19.87 mm. Both produced the same archive with SHA-256 `f49702b15d7b279c9b0352ddbc7ca1f1ba67678df6c41b9e411111587eb64b97` on the recorded Python 3.14.6 Windows runtime. Strict SDK readback retained the driving D1, linked boss, and one solid with volume 10,531.1 mm³. The exact edit from 0.0125 m to 12.5 mm refused. Both original requests remained unchanged.

This verifies the offline research edit and readback boundary. Vendor-authored source admission and native measurement retain their existing gates. [Depth unit gotcha](../../../Gotchas/Research/Writers/SolidworksAbsoluteDepthEditUnits.md)
