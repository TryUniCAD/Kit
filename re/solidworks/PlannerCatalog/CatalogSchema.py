# explicit tables keep planner contracts independent from implementation object layouts
KSchema = """
PRAGMA foreign_keys=ON;
CREATE TABLE sources(id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL,
sha256 TEXT NOT NULL, details TEXT NOT NULL CHECK(json_valid(details)));
CREATE TABLE items(id TEXT PRIMARY KEY,kind TEXT NOT NULL,name TEXT NOT NULL,
parent_id TEXT REFERENCES items(id) DEFERRABLE INITIALLY DEFERRED,
source_id TEXT NOT NULL REFERENCES sources(id),details TEXT NOT NULL CHECK(json_valid(details)),
authoring_status TEXT NOT NULL CHECK(authoring_status='unverified'),
decoding_status TEXT NOT NULL CHECK(decoding_status='unverified'),
writing_status TEXT NOT NULL CHECK(writing_status='unverified'),
verification_status TEXT NOT NULL CHECK(verification_status='unverified'));
CREATE INDEX item_parent ON items(parent_id);
CREATE INDEX item_kind_name ON items(kind,name);
CREATE TABLE relations(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES items(id),
target_id TEXT NOT NULL REFERENCES items(id),kind TEXT NOT NULL,
source_id TEXT NOT NULL REFERENCES sources(id),details TEXT NOT NULL CHECK(json_valid(details)));
CREATE INDEX relation_owner ON relations(owner_id,kind);
CREATE INDEX relation_target ON relations(target_id,kind);
CREATE TABLE gaps(id TEXT PRIMARY KEY,code TEXT NOT NULL,item_id TEXT REFERENCES items(id),
source_id TEXT NOT NULL REFERENCES sources(id),details TEXT NOT NULL CHECK(json_valid(details)));
CREATE INDEX gap_code ON gaps(code);
CREATE VIEW api_types AS SELECT * FROM items WHERE kind='api_type';
CREATE VIEW api_options AS SELECT * FROM items WHERE kind IN ('api_method','api_property_get','api_property_put','api_property_putref','api_function','api_parameter');
CREATE VIEW api_enums AS SELECT * FROM items WHERE kind='api_constant';
CREATE VIEW command_candidates AS SELECT * FROM items WHERE kind='api_constant' AND json_extract(details,'$.command_candidate')=1;
CREATE VIEW feature_plan AS SELECT * FROM items WHERE kind IN ('feature_family','feature_subfeature','feature_option','plan_wave');
CREATE VIEW api_feature_types AS SELECT * FROM api_types WHERE name LIKE '%FeatureData%';
CREATE VIEW native_schemas AS SELECT id,name,NULL AS native_schema,NULL AS member_count,'unobserved' AS lookup_status FROM api_types WHERE 0;
PRAGMA user_version=1;
"""


# declared exports make normal and exhaustive catalogue slices reproducible
KExports = {
    "ApiTypes.csv": "api_types",
    "ApiOptions.csv": "api_options",
    "ApiEnums.csv": "api_enums",
    "Commands.csv": "command_candidates",
    "Features.csv": "feature_plan",
    "Gaps.csv": "gaps",
    "Relations.csv": "relations",
    "NativeSchemas.csv": "native_schemas",
}


# metadata artifacts retain the same notice as their independently authored collectors
KNotice = """SPDX-License-Identifier: MIT"""
