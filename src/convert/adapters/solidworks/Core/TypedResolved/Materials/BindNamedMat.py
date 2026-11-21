from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerGraph import ManagerGraph
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatAtoms import (
    CheckMatAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.NamedMatRead import (
    NamedMatRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatCfg import (
    ReadMatCfg,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatDensity import (
    ReadMatDensity,
)
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatIdent import (
    ReadMatIdent,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# project only the physical assignment after proving all binary owners
def BindNamedMat(
    PartGraph: ConfigGraph, ManagerValue: CmgrGraph, HeaderValue: ManagerGraph
) -> NamedMatRead:
    PartValue = RequireNative(PartGraph.RootValue, "moPart_c")
    ConfigValue = ReadMatCfg(ManagerValue, HeaderValue, PartValue)
    CheckMatAtoms(PartGraph, ConfigValue, ManagerValue.RootValue)
    DensityValue = ReadMatDensity(PartGraph, ConfigValue)
    CatalogValue, MaterialName, NativeId = ReadMatIdent(
        PartGraph, ManagerValue, ConfigValue
    )
    return NamedMatRead(
        ReadNativeName(ConfigValue), CatalogValue, MaterialName, NativeId, DensityValue
    )
