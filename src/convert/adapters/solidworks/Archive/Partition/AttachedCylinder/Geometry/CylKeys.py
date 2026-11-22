from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef

# the active partition has one distinct world owner before the body
KCylWorld = PrismRef(101, "world")

# the actual producing arc owns the side instead of either cap
KCylSide = PrismRef(14, "side")

# both circular rims bound the same analytic mantle
KCylMantle = PrismRef(51, "mantle")
