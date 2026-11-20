# SOLIDWORKS dimension ownership across control files

A file-driven run now investigates ambiguous dimensions on features the reader already recognizes. It checks whether each named scalar has a consistent byte offset from its feature boundaries or a consistent object ID relative to its owning feature. It learns the relationship from other resolved streams, using at least two different dimension values. At least two independent streams and two values must match exactly. Additional length observations may agree at the precision saved in the document. A held-out match must also agree with the public reader’s exact value, unit and source span.

On the tracked turbine wheel, both chamfers display 45°. Across 52 training observations the angle’s object ID was one less than the chamfer ID. Applying that relationship to the wheel selected offset 163267 for the first chamfer and 242847 for the second. The same search recovered both 1.27 mm chamfer lengths at offsets 161535 and 241115. Three control measurements round to their saved two-decimal millimetre displays, including 1.905 mm displayed as 1.91. Nine other dimension records remain ambiguous.

Run `kit run solidworks --input <part.SLDPRT> --directory <new-directory>` and inspect `held_out_owner_anchor` in `Input-dimension-evidence.json`. Its sample group links the result to the control measurements and stream hashes.
