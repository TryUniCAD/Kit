# Fusion texture bounds can describe the previous shape

A height edit changed the measured cuboid height from 13.8 mm to 28.3 mm. The edited archive still stored the texture bounds ending at 1.3800000000000001 cm. Restoring the height to 13.8 mm left the texture bounds ending at 2.83 cm. Both graphics cache entries and the Design mapping agreed with the preceding shape. A second control kept its initialized wood origin unchanged across the edit and restore, even though its texture bounds changed.

Do not derive saved bounds from the current body or replace an initialized origin with the center of the bounds. Reconstructing the historical bounds needs the prior solved frame in the native coordinate basis. The [Design texture placement experiment](../../../../Changes/Research/Encoder/FusionDesignTexturePlacement.md) admits only the inverted finite empty box and keeps the supplied origin independent of the current cuboid height.
