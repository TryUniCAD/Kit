from pathlib import Path as FilePath
from plistlib import dumps as DumpPlist


# independently authored syntax exercises full collection without distributing or executing the proprietary sdk
def PrepareApi(TmpPath: FilePath) -> FilePath:
    ProductRoot = TmpPath / "Fixture.app" / "Contents"
    ModuleRoot = ProductRoot / "Api" / "Python" / "packages" / "adsk" / "defs" / "adsk"
    ModuleRoot.mkdir(parents=True)
    (ProductRoot / "Info.plist").write_bytes(
        DumpPlist({"CFBundleShortVersionString": "fixture-only"})
    )
    (ModuleRoot / "__init__.py").write_text(
        "raise AssertionError('metadata must not execute')\n"
    )
    InputRoot = FilePath(__file__).with_name("Inputs")
    for SourceName, ModuleName in (
        ("Core.txt", "core.py"),
        ("Fusion.txt", "fusion.py"),
    ):
        (ModuleRoot / ModuleName).write_bytes((InputRoot / SourceName).read_bytes())
    return ModuleRoot
