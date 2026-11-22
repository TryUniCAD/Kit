from inspect import isabstract as IsAbstract
from typing import cast

import pytest as Pytest

from convert import available_adapters as GetAdapters
from convert.adapters import AdapterInfo, AdapterNotFoundError, AdapterRegistry
from convert.adapters.base.AdapterProtocols import CadReaderAdapter, CadWriterAdapter
from interchange import Capability
from tests.Convert.Api.ApiTestHelpers import GetPackNames, ListFormatPacks
from tests.Convert.Api.CatalogAliases import AssertAliases

# existing bidirectional formats retain their established reader and writer capabilities
KLegacyFormats = frozenset({"catia.v5", "freecad.fcstd", "interchange.json"})


# deterministic introspection prevents import order from changing the public format catalog
def CheckDiscovery() -> None:
    PackageNames = ListFormatPacks()
    FirstRegistry = AdapterRegistry()
    FirstIds = FirstRegistry.introspect()
    SecondRegistry = AdapterRegistry()
    SecondIds = SecondRegistry.introspect()
    ReaderValues = FirstRegistry.readers()
    WriterValues = FirstRegistry.writers()
    assert PackageNames
    assert GetPackNames((*ReaderValues, *WriterValues), PackageNames) == set(
        PackageNames
    )
    ReaderIds = tuple(ValueData.info.format_id for ValueData in ReaderValues)
    WriterIds = tuple(ValueData.info.format_id for ValueData in WriterValues)
    assert ReaderIds == tuple(sorted(set(ReaderIds)))
    assert WriterIds == tuple(sorted(set(WriterIds)))
    assert FirstIds == SecondIds == tuple(sorted(set(ReaderIds) | set(WriterIds)))
    assert KLegacyFormats | {"solidworks.sldprt"} <= set(ReaderIds) & set(WriterIds)
    assert "fusion.f3d" in ReaderIds
    for FormatId in ("f3d", "fusion.f3d"):
        assert FirstRegistry.reader(FormatId).info.format_id == "fusion.f3d"
        assert FirstRegistry.writer(FormatId).info.format_id == "fusion.f3d"
    assert "fusion.f3d" in WriterIds
    AssertAliases(FirstRegistry)
    assert FirstRegistry.introspect() == FirstIds
    assert FirstRegistry.readers() == ReaderValues
    assert FirstRegistry.writers() == WriterValues
    assert all(
        not IsAbstract(type(AdapterData))
        and not getattr(type(AdapterData), "_is_protocol", False)
        for AdapterData in (*ReaderValues, *WriterValues)
    )
    AssertCaps((*ReaderValues, *WriterValues))
    AssertSwModes(FirstRegistry)


# the registry advertises capabilities consistently across discovered adapter families
def AssertCaps(
    Adapters: tuple[CadReaderAdapter | CadWriterAdapter, ...],
) -> None:
    assert all(
        AdapterData.info.capabilities == frozenset(Capability)
        for AdapterData in Adapters
        if AdapterData.info.format_id in KLegacyFormats
    )


# the part writer must retain separate capabilities from the assembly capable native reader
def AssertSwModes(Registry: AdapterRegistry) -> None:
    Reader = Registry.reader("solidworks.sldprt")
    PartWriter = Registry.writer("solidworks.sldprt")
    Writer = PartWriter.info
    assert Registry.reader("solidworks.sldasm") is Reader
    assert Reader.info.capabilities == frozenset(Capability)
    assert Writer.extensions == (".sldprt", ".sldasm")
    assert Writer.part_extensions == (".sldprt",)
    assert Writer.assembly_extensions == (".sldasm",)
    assert Writer.aliases == ("solidworks.sldasm",)
    assert (
        Writer.capabilities
        == Writer.native_capabilities
        == {
            Capability.BODY_STRUCTURE,
            Capability.ASSEMBLIES,
            Capability.COMPONENT_DOCUMENTS,
            Capability.CONFIGURATIONS,
            Capability.EDITABLE_SKETCHES,
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.SUPPORT_PLANES,
            Capability.BREP,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
            Capability.SELECTIONS,
        }
    )
    assert Registry.writer("solidworks.sldasm") is PartWriter
    with Pytest.raises(AdapterNotFoundError):
        _ = Registry.writer("solidworks.slddrw")


# document kind extensions remain introspective so clients need no format specific branches
def CheckDocExts() -> None:
    AdapterMap = {InfoData.format_id: InfoData for InfoData in GetAdapters()}
    assert AdapterMap["solidworks.sldprt"].part_extensions == (".sldprt",)
    assert AdapterMap["solidworks.sldprt"].assembly_extensions == (".sldasm",)
    assert AdapterMap["catia.v5"].part_extensions == (".catpart",)
    assert AdapterMap["catia.v5"].assembly_extensions == (".catproduct",)
    assert AdapterMap["freecad.fcstd"].part_extensions == (".FCStd",)
    assert AdapterMap["freecad.fcstd"].assembly_extensions == (".FCStd",)
    for InfoData in AdapterMap.values():
        assert set(InfoData.extensions_for(assembly=False)) <= set(InfoData.extensions)
        assert set(InfoData.extensions_for(assembly=True)) <= set(InfoData.extensions)
    with Pytest.raises(TypeError):
        _ = AdapterMap["freecad.fcstd"].extensions_for(assembly=cast(bool, 1))
    AssemblyInfo = AdapterInfo(
        "format.assembly-only",
        "Assembly only",
        "1",
        (".assembly",),
        assembly_extensions=(".assembly",),
    )
    assert AssemblyInfo.extensions_for(assembly=False) == ()
    assert AssemblyInfo.extensions_for(assembly=True) == (".assembly",)
