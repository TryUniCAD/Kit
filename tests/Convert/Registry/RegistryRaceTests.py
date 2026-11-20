from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook

import pytest as Pytest

from convert.adapters import AdapterInfo, AdapterRegistry, WriteOptions
from interchange import Capability
from tests.Convert.Registry.RegistryPolicyTests import BundleAdapter
from tests.Convert.Registry.RegistryTestSupport import BuildSource


# both boundaries need the ordinary registry to stage the primary file and one companion
def MakeBundle() -> AdapterRegistry:
    RegistryData = AdapterRegistry()
    RegistryData.register(
        BundleAdapter(
            AdapterInfo(
                "format.bundle",
                "Filesystem bundle",
                "1",
                (".bundle",),
                capabilities=frozenset(Capability),
                native_capabilities=frozenset(Capability),
            ),
            Requirements=(),
        )
    )
    return RegistryData


# a peer that creates the companion during publication owns its data after rollback
def CheckFileRace(TmpPath: FilePath) -> None:
    RegistryData = MakeBundle()
    TargetPath = TmpPath / "fresh.bundle"
    PeerPath = TmpPath / "component.bin"
    IsActive = True
    HasCreated = False

    # inject a new file after the entire bundle has passed its initial conflict scan
    def CreatePeer(EventName: str, Arguments: tuple[object, ...]) -> None:
        nonlocal HasCreated
        if (
            IsActive
            and not HasCreated
            and EventName in ("os.rename", "os.link")
            and str(Arguments[1]) == str(TargetPath)
        ):
            HasCreated = True
            with PeerPath.open("xb") as OutputFile:
                _ = OutputFile.write(b"peer component")

    AddAuditHook(CreatePeer)
    try:
        with Pytest.raises(FileExistsError):
            _ = RegistryData.write(BuildSource(), TargetPath, format_id="format.bundle")
    finally:
        IsActive = False
    assert HasCreated and not TargetPath.exists()
    assert PeerPath.read_bytes() == b"peer component"
    assert tuple(TmpPath.iterdir()) == (PeerPath,)


# incomplete backup must restore every earlier file before staging cleanup deletes temporary data
def CheckBackup(TmpPath: FilePath) -> None:
    RegistryData = MakeBundle()
    TargetPath = TmpPath / "saved.bundle"
    ChildPath = TmpPath / "component.bin"
    _ = TargetPath.write_bytes(b"original parent")
    _ = ChildPath.write_bytes(b"original child")
    IsActive = True

    # fail the second backup after replacing the first original path
    def DenyBackup(EventName: str, Arguments: tuple[object, ...]) -> None:
        if (
            IsActive
            and EventName == "os.rename"
            and str(Arguments[0]) == str(ChildPath)
            and FilePath(str(Arguments[1])).parent.name == ".kit-backup"
        ):
            assert not TargetPath.exists()
            raise PermissionError("controlled companion backup failure")

    AddAuditHook(DenyBackup)
    try:
        with Pytest.raises(
            PermissionError, match="controlled companion backup failure"
        ):
            _ = RegistryData.write(
                BuildSource(),
                TargetPath,
                format_id="format.bundle",
                options=WriteOptions(overwrite=True),
            )
    finally:
        IsActive = False
    assert TargetPath.read_bytes() == b"original parent"
    assert ChildPath.read_bytes() == b"original child"
    assert set(TmpPath.iterdir()) == {TargetPath, ChildPath}
