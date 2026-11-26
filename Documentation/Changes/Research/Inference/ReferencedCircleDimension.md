# Circle dimensions with referenced coordinates

When a sketch has a native circle without a separate profile, `kit run solidworks --input <part> --directory <new-directory>` follows the circle record’s center and endpoint indices inside the owning feature. The two endpoints must select the same rim marker. The measured radius, driving scalar, constraint reference and public reader span must agree.

In the turbine wheel, the circle in sketch 261 references center and rim records at offsets 218336 and 218478. Their coordinates give a radius of 8.89 mm. This identifies the 17.78 mm diameter at offset 219738. The other candidate occurs in a different feature. Six dimension records remain ambiguous. The evidence is recorded as `verified_native_radius` in `Input-dimension-evidence.json`.
