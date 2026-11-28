from types import MappingProxyType

# these digests authenticate offline measurement documents and never contribute archive values
KCircAuthPins = MappingProxyType(
    {
        "bc49ba2f4fd8215f2772c16dc7bdfc7c973f2dcacc4214b4890ef2bdb8ad6be0": (
            "kit.sw2026.sdk-circle-native-disclosed.v1",
            "disclosed_lifecycle_passed",
        ),
        "9c0fdd3617ad06f1c7a7d90f3dd59f88794c80e22e7b5d7b54256c75d5a77a10": (
            "kit.sw2026.sdk-circle-ends-disclosed.v1",
            "passed",
        ),
        "a14c4ff431f4e75b129025072d8be8f752df2694467b8c743b0ce861b0401da5": (
            "kit.sw2026.sdk-circle-original-native-receipt.v1",
            "scoped_sdk_heldout_acceptance",
        ),
        "08a866d4922298c892b2126f71adca26ac9ae3f96421f6a0ed9ab77195607ca4": (
            "kit.sw2026.sdk-paired-end-conditions-native.v1",
            "native_acceptance",
        ),
    }
)
