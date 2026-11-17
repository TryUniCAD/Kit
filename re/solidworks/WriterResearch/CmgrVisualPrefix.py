from dataclasses import dataclass as Dataclass
from pathlib import PureWindowsPath
from struct import pack as PackFields, unpack as UnpackFields

from CmgrVisualProfile import KExplicitProfile, SelectVisualProfile
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KDefaultMaterialAsset = ("data", "graphics", "materials", "color.p2m")
KDefaultShader = "defaultplastic"
KRecordedBump = UnpackFields("<f", PackFields("<f", 0.001))[0]


@Dataclass(frozen=True, slots=True)
class CmgrVisualFields:
    SurfaceColor: int
    WireColor: int
    HiddenLineColor: int
    MaterialName: str
    AppearanceId: int
    MaterialColor: int
    NativeAssetPath: str
    MappingMode: int
    BumpStrength: float
    DisplacementDistance: float
    UsesNormalMap: bool
    UsesDefaultAppearance: bool


def RequireVisualFields(
    Generation: int,
    Fields: CmgrVisualFields,
    *,
    AllowSystemTexture: bool = False,
) -> None:
    RequireArch(Generation, 19000, "CMgr visual prefix generation")
    Colors = (
        Fields.SurfaceColor,
        Fields.WireColor,
        Fields.HiddenLineColor,
        Fields.MaterialColor,
    )
    RequireArch(
        all(0 <= Color <= 0xFFFFFF for Color in Colors),
        True,
        "CMgr packed visual colors",
    )
    RequireArch(
        0 < Fields.AppearanceId < 1 << 64,
        True,
        "CMgr allocated PW material appearance ID",
    )
    RequireArch(Fields.MaterialName, "Steel", "CMgr ordinary ID name")
    Profile = SelectVisualProfile(Fields.UsesDefaultAppearance)
    RequireArch(
        (Fields.MappingMode, Fields.UsesNormalMap, Fields.UsesDefaultAppearance),
        (3, Profile.UsesNormalMap, Profile.UsesDefaultAppearance),
        "CMgr ordinary RealView and default appearance modes",
    )
    RequireArch(
        Fields.BumpStrength
        in (Profile.BumpStrength, RecordedFloat(Profile.BumpStrength))
        and Fields.DisplacementDistance
        in (Profile.DisplacementDistance, RecordedFloat(Profile.DisplacementDistance)),
        True,
        "CMgr retained bump and displacement settings",
    )
    if Profile is KExplicitProfile:
        RequireArch(
            type(Fields.MappingMode) is int
            and Fields.UsesNormalMap is False
            and all(type(Color) is int for Color in Colors)
            and type(Fields.AppearanceId) is int
            and Fields.SurfaceColor == Fields.MaterialColor,
            True,
            "explicit model color identity and matching RealView color",
        )
    Locator = PureWindowsPath(Fields.NativeAssetPath)
    InstalledLocator = (
        Locator.is_absolute()
        and tuple(Part.casefold() for Part in Locator.parts[-4:])
        == KDefaultMaterialAsset
    )
    SystemLocator = (
        AllowSystemTexture and Fields.NativeAssetPath == Profile.SystemTexturePath
    )
    RequireArch(
        (
            InstalledLocator or SystemLocator,
            ".." in Locator.parts,
            any(ord(Char) < 32 for Char in Fields.NativeAssetPath),
        ),
        (True, False, False),
        "CMgr installed default material locator",
    )


# recorded float fields also accept their written representation at the typed input boundary
def RecordedFloat(Value: float) -> float:
    return UnpackFields("<f", PackFields("<f", Value))[0]


# The filename is supplied by the document's target installation.
def WriteRealView(Writer: ArchiveWriter, Fields: CmgrVisualFields) -> None:
    Profile = SelectVisualProfile(Fields.UsesDefaultAppearance)
    Writer.raw(PackFields("<Q", Fields.AppearanceId))
    Writer.string(KDefaultShader)
    Writer.raw(PackFields("<BI", Fields.MappingMode, Fields.MaterialColor))
    # Mapping basis, origin, face width and the single color form.
    Writer.raw(PackFields("<10fi", 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1))
    # Reflectivity, color mix, three original-term sentinels and illumination axes.
    Writer.raw(PackFields("<5fi2f", *Profile.ReflectivityTerms))
    Writer.string(Fields.NativeAssetPath)
    Writer.raw(PackFields("<I2f", *Profile.SpecularTerms))
    Writer.string("")
    # Double-sided surface and the caller's custom bump convention.
    SurfaceFlags = Profile.SurfaceFlags
    Writer.raw(
        PackFields(
            "<3fifi",
            Fields.BumpStrength,
            Fields.DisplacementDistance,
            0,
            SurfaceFlags,
            0,
            0,
        )
    )
    Writer.raw(PackFields("<13f", 1, 0, 0, 0, 1, 0, 0, 0, 1, 90, 1, -1, -1))
    Writer.string("")
    Writer.raw(PackFields("<f", 0))


# The body is inline in the already-open visual object and ends at the DSPBR body.
def WriteCmgrVisualPrefix(
    Writer: ArchiveWriter,
    Generation: int,
    Fields: CmgrVisualFields,
    *,
    AllowSystemTexture: bool = False,
) -> None:
    RequireVisualFields(Generation, Fields, AllowSystemTexture=AllowSystemTexture)
    Profile = SelectVisualProfile(Fields.UsesDefaultAppearance)
    Writer.raw(
        PackFields("<3I", Fields.SurfaceColor, Fields.WireColor, Fields.HiddenLineColor)
    )
    Writer.string("")
    Writer.string(Fields.MaterialName)
    # Ambient, diffuse, specular, shininess, transparency, emission and absent texture.
    Writer.raw(PackFields("<6di", 1, 1, 0.5, 0.3125, 0, 0, 0))
    Writer.raw(PackFields("<5i", *Profile.LegacyWords))
    Writer.string("")
    Writer.raw(PackFields("<2i", 1, 1))
    WriteRealView(Writer, Fields)
    # Empty PLM identifier, absent secondary texture and empty material map.
    Writer.string("")
    Writer.raw(PackFields("<2i", 0, 0))
    # Empty add-in identifier, lightweight rendering and unnamed appearance.
    Writer.string("")
    Writer.raw(PackFields("<2i", 0, 1))
    Writer.string("")
    Writer.raw(PackFields("<6i", 0, Fields.UsesDefaultAppearance, -1, 0, 0, 1))
