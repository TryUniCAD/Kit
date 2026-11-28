from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import (
    MakeBiography,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import (
    MakeFreshHist,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# recursive and flat assemblies need identical header definition and history construction while their computed document indexes have different closure scopes
def MakeAsmCommon(
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    ManagerHeader: ArchiveNode,
    DefinitionValue: ModelDefGraph,
) -> dict[str, bytes]:
    HeaderValue, TopHeader = HeadersValue
    return {
        "Header2": WriteHeadGraph(TopHeader, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(HeaderValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHeader(ManagerHeader, 19000)[0],
        "Contents/Definition": WriteModelDef(
            DefinitionValue, Assembly=True
        ).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistGraph(MakeBiography(), 19000)[0],
        "_MO_VERSION_19000/History": WriteHistGraph(
            MakeFreshHist(InputValue.HistoryValue), 19000
        )[0],
    }
