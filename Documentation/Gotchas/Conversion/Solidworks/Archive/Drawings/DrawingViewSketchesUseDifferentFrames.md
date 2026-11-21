# Drawing view sketches use different frames

An ordinary absolute view owns both a sheet sketch and a model-side centre mark sketch. At unit scale with Front orientation, translations alone can describe their frames. Scaled and rotated views expose the difference.

The sheet sketch uses an identity rotation, scale `1/s` and translation `-position/s`. The model sketch uses the canonical rotation, unit scale and translation equal to the negative rotated child-box centre. Its plane normal and displayed name position follow the same basis. Isometric changes the view's cached 2D-dimension eligibility and retains the independently set face-valid flag.

Build each support from the appropriate frame and keep its actual plane/profile references. Check both owner graphs in scaled and rotated native files. [Native source rules and comparisons](../../../../../../re/solidworks/records/DrawingScaledSupports2026.md)
