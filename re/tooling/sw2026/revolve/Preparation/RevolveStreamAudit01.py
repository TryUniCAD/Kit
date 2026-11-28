from hashlib import sha256
from xml.etree.ElementTree import fromstring

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut


def stream_audit(archive, link):
    config_bytes, config = WriteConfigMut(link.ConfigValue.RootValue,19000,link.ConfigValue.HeaderValue)
    resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue,link.ResolvedValue.ExtraFields,
        19000,config.MapValue,link.ResolvedValue.ContextValue)
    emitted = {'Contents/Config-0':config_bytes,'Contents/Config-0-ResolvedFeatures':resolved_bytes}
    for name in ('Header2','Contents/Config-0-ModelHeader'):
        emitted[name] = WriteHeadGraph(ReadHeaderGraph(archive.require(name),19000),19000)
    emitted['Contents/CMgr'] = WriteCmgrMut(ReadCmgrMut(archive.require('Contents/CMgr'),19000).RootValue,19000)
    emitted['Contents/CMgrHdr2'] = WriteMgrHeader(ReadMgrHeader(archive.require('Contents/CMgrHdr2'),19000).RootValue,19000)[0]
    emitted['Contents/Definition'] = WriteModelDef(ReadModelDef(archive.require('Contents/Definition'),19000).GraphValue).OutputValue
    for name in ('_MO_VERSION_19000/Biography','_MO_VERSION_19000/History'):
        emitted[name] = WriteHistMut(ReadHistMut(archive.require(name),19000).RootValue,19000)[0]
    emitted['swXmlContents/KeyWords'] = FrameKeywords(fromstring(archive.require('swXmlContents/KeyWords')[1:]),True)
    for graph in (config,resolved):
        if not graph.ReportValue['completed'] or graph.ReportValue['missing_schemas'] or graph.ReportValue['provisional_schemas']:
            raise ValueError('critical native graph reaches unqualified schema')
    if any(data != archive.require(name) for name,data in emitted.items()):
        raise ValueError('critical native stream re-emission differs: '+','.join(name for name,data in emitted.items() if data!=archive.require(name)))
    return {name:{'bytes':len(data),'sha256':sha256(data).hexdigest(),'byte_identity':True} for name,data in emitted.items()}
