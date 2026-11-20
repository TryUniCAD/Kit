from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef

# the bare local envelope carries a single root body without a world
KPrismBody = PrismRef(12, "body")

# the finite shell bounds the material region owned by the local body
KPrismSolidRegion = PrismRef(19, "solid")

# the exterior region keeps the front side of each solid face reachable
KPrismVoidRegion = PrismRef(19, "void")

# the positive face chain belongs to the material shell
KPrismSolidShell = PrismRef(13, "solid")

# the exterior shell needs a front chain without a direct body pointer
KPrismVoidShell = PrismRef(13, "void")
