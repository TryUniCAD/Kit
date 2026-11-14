from __future__ import annotations

# expression section declarations; research only
KRefs: tuple[tuple[str, str], ...] = (
    ('UGS::OM::Meta', '02'),
    ('UGS::ESS', '2a'),
    ('UGS::OM::Basic', '0b'),
    ('UGS::ExpKf::ExpGroups', '04'),
    ('UGS::ModlUtils::CachedWaveLinkData', '07'),
)

KClasses: tuple[tuple[str, str, str, str, str], ...] = (
    ('UGS::OM::RootObject', '38', '0b', 'b04ba5fe911bf679', '02'),
    ('UGS::ESS_part', '80c8', '0e', '4bf5723f36e403cc', '01'),
    ('UGS::OM::SaveAuditTrail', '80c9', '0f', '60949c186aa89e41', '01'),
    ('UGS::OM::SaveAuditTrailEntry', '80c8', '0f', 'e7735fb1a6df50f5', '01'),
    ('UGS::OM::OldHashSet', '80aa', '10', '29310cebd3fc218e', '03'),
    ('UGS::OM::HashSet', '8190', '10', '0dcad682a9b6d8b0', '04'),
    ('UGS::ExpKf::ExpGroupManager', '65', '0e', '13a6dd687a4c4f95', '04'),
    ('UGS::ExpKf::ExpGroup', '80c8', '0e', '3ccb8c920580968e', '02'),
    ('UGS::EXP_expression', '81f4', '11', '501cb9b131ab2241', '05'),
    ('UGS::ModlUtils::CachedWaveLinkData', '65', '0f', 'eddfc5d7284603ec', '01'),
    ('UGS::OM::TaggedObject', '06', '0c', '05e636f6280be790', '01'),
    ('UGS::OM::StorableObject', '04', '0d', '4d41ac58055dcc02', '01'),
    ('UGS::OM::MethodicObject', '80ff', '00', '93c3d462055dcc02', '01'),
    ('UGS::OM::VersionedObject', '80c4', '0b', '3d51b00c56517a38', '01'),
    ('UGS::OM::SubObject', '80fd', '0d', '1ed28985055dcc02', '01'),
    ('UGS::OM::Set', '80a0', '0b', '6f742b7001ae02d8', '02'),
    ('UGS::EXP_generic', '8190', '0e', 'cfc3b4e4eea8d595', '02'),
)
