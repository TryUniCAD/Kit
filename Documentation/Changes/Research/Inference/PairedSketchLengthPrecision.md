# Precision of paired SOLIDWORKS sketch lengths

The offline reader recovers a millimetre sketch length from matching display and driving records when their object IDs are distinct, their full-precision values and referenced operands agree, and rounding reproduces the saved keyword at the document’s display precision. The parameter retains the keyword text and points to the driving scalar. The research report records both offsets and the operand indices for qualifying ambiguous pairs.

The turbine-wheel sketch displays 39.41 mm and stores 39.41420312445611 mm. Independent strict reads of the oil pan recovered 63.43778355059032 and 49.73237559483219 mm, and the intake manifold yielded 93.47463127844819 mm. These cases concern named linear sketch dimensions in millimetres. The turbine-wheel report still has seven ambiguous dimension records.

Use `kit decode <part.SLDPRT> --from solidworks.sldprt -o <output.json>` for the parameters and `kit run solidworks --input <part.SLDPRT> --directory <new-directory>` for the evidence.

The audit also [excludes verified integer count slots](../../../Gotchas/Research/Readers/InstanceCountMatchesZeroLength.md) from length candidates, resolving a displayed zero that previously matched both an integer count and a sketch scalar.
