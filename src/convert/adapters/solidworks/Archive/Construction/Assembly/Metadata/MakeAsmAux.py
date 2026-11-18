from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeys import (
    MakeAsmKeys,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmTree import (
    MakeAsmTree,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import (
    MakeBiography,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import (
    MakeFreshHist,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# every assembly metadata stream is generated from actual linked graph owners explicit fresh provenance and model computed indexes without saved payload fallback
def MakeAsmAux(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    ManagerHeader: ArchiveNode,
    DefinitionValue: ModelDefGraph,
    References: tuple[ArchiveNode, ...],
) -> dict[str, bytes]:
    HeaderValue, TopHeader = HeadersValue
    return {
        "Header2": WriteHeadGraph(TopHeader, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(HeaderValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHdrMut(ManagerHeader, 19000)[0],
        "Contents/Definition": WriteModelDef(DefinitionValue).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistMut(MakeBiography(), 19000)[0],
        "_MO_VERSION_19000/History": WriteHistMut(
            MakeFreshHist(InputValue.HistoryValue), 19000
        )[0],
        "swXmlContents/KeyWords": MakeAsmKeys(
            StateValue, HeaderValue, ChildValue, References
        ),
        "swXmlContents/COMPINSTANCETREE": MakeAsmTree(
            StateValue, HeaderValue, ChildValue, References
        ),
    }
