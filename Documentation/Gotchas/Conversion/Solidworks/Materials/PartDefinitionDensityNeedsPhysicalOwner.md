# Part Definition density needs a physical owner

The first disclosed generated sweep files supplied the requested 1031.7 kg/m³ to `Contents/Definition`. SOLIDWORKS 2026 SP05.2 opened both without errors or warnings and built their geometry. Both returned 1000 kg/m³ for document density and used that value for calculated mass.

All six matched native originals and edited saves store the effective unassigned density in `moPart_c.f1420 → moMaterial_c.f08 → moDensityParameter_c.f58`. Their `f68` is zero, the active configuration's `fc50` is `-1`, and the manager's custom density table is empty. For this profile, the generator now supplies that modeled physical parameter alongside Definition. The current exact failure and same-locator regeneration remain reproducible. [Sweep experiment and density receipt](../../../../../re/solidworks/records/OrdinarySweepColdConstruction2026.md)
