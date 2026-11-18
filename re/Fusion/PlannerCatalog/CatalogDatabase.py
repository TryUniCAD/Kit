from collections import Counter
from csv import writer
from hashlib import sha256
from json import loads
from pathlib import Path
from sqlite3 import connect, sqlite_version

from CatalogRows import JsonText

# a fixed relational schema supports indexed planning queries without loading the whole inventory
KSchema = """
PRAGMA foreign_keys=ON;
PRAGMA user_version=1;
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL CHECK(json_valid(value)));
CREATE TABLE source_records(
 row_id INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, label TEXT NOT NULL, sha256 TEXT NOT NULL,
 application_version TEXT NOT NULL, details TEXT NOT NULL CHECK(json_valid(details)));
CREATE TABLE item_records(
 row_id INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL, parent_id INTEGER,
 source_id INTEGER NOT NULL, details TEXT NOT NULL CHECK(json_valid(details)),
 authoring_status TEXT NOT NULL DEFAULT 'unverified',
 decoding_status TEXT NOT NULL DEFAULT 'unverified',
 writing_status TEXT NOT NULL DEFAULT 'unverified',
 verification_status TEXT NOT NULL DEFAULT 'unverified',
 FOREIGN KEY(parent_id) REFERENCES item_records(row_id) DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY(source_id) REFERENCES source_records(row_id));
CREATE TABLE relation_records(
 owner_id INTEGER NOT NULL, target_id INTEGER NOT NULL, relation TEXT NOT NULL,
 source_id INTEGER NOT NULL, details TEXT NOT NULL CHECK(json_valid(details)),
 PRIMARY KEY(owner_id,target_id,relation,source_id,details),
 FOREIGN KEY(owner_id) REFERENCES item_records(row_id), FOREIGN KEY(target_id) REFERENCES item_records(row_id),
 FOREIGN KEY(source_id) REFERENCES source_records(row_id)) WITHOUT ROWID;
CREATE TABLE gap_records(
 row_id INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, code TEXT NOT NULL, item_id INTEGER, source_id INTEGER NOT NULL,
 details TEXT NOT NULL CHECK(json_valid(details)),
 FOREIGN KEY(item_id) REFERENCES item_records(row_id), FOREIGN KEY(source_id) REFERENCES source_records(row_id));
CREATE INDEX item_kind_name ON item_records(kind,name);
CREATE INDEX item_parent ON item_records(parent_id,kind);
CREATE INDEX item_source ON item_records(source_id,kind);
CREATE INDEX relation_target ON relation_records(target_id,relation);
CREATE INDEX relation_owner ON relation_records(owner_id,relation);
CREATE INDEX gap_code ON gap_records(code,item_id);
CREATE VIEW sources AS SELECT id,kind,label,sha256,application_version,details FROM source_records;
CREATE VIEW items AS SELECT i.id,i.kind,i.name,p.id AS parent_id,s.id AS source_id,i.details,
 i.authoring_status,i.decoding_status,i.writing_status,i.verification_status FROM item_records i
 LEFT JOIN item_records p ON p.row_id=i.parent_id JOIN source_records s ON s.row_id=i.source_id;
CREATE VIEW relations AS SELECT a.id AS owner_id,b.id AS target_id,r.relation,s.id AS source_id,r.details
 FROM relation_records r JOIN item_records a ON a.row_id=r.owner_id
 JOIN item_records b ON b.row_id=r.target_id JOIN source_records s ON s.row_id=r.source_id;
CREATE VIEW gaps AS SELECT g.id,g.code,i.id AS item_id,s.id AS source_id,g.details FROM gap_records g
 LEFT JOIN item_records i ON i.row_id=g.item_id JOIN source_records s ON s.row_id=g.source_id;
CREATE VIEW api_ancestors AS
 WITH RECURSIVE ancestry(type_id,ancestor_id,depth) AS (
  SELECT owner_id,target_id,1 FROM relations WHERE relation='inherits'
  UNION ALL
  SELECT a.type_id,r.target_id,a.depth+1 FROM ancestry a
   JOIN relations r ON r.owner_id=a.ancestor_id AND r.relation='inherits'
 ) SELECT type_id,ancestor_id,MIN(depth) AS depth FROM ancestry GROUP BY type_id,ancestor_id;
CREATE VIEW api_feature_types AS
 SELECT * FROM items WHERE id='api:adsk.fusion.Feature' OR id IN (
 SELECT type_id FROM api_ancestors WHERE ancestor_id='api:adsk.fusion.Feature');
CREATE VIEW api_effective_members AS
 WITH candidates AS (
  SELECT parent_id AS type_id,id AS member_id,kind,name,details,0 AS depth
   FROM items WHERE kind IN ('api_method','api_property','api_constant','api_enum_value')
  UNION ALL
  SELECT a.type_id,i.id,i.kind,i.name,i.details,a.depth FROM api_ancestors a
   JOIN items i ON i.parent_id=a.ancestor_id
   WHERE i.kind IN ('api_method','api_property','api_constant','api_enum_value')
 ), ranked AS (
  SELECT *,ROW_NUMBER() OVER(PARTITION BY type_id,kind,name ORDER BY depth,member_id) AS priority
   FROM candidates)
 SELECT type_id,member_id,kind,name,details,depth FROM ranked WHERE priority=1;
CREATE VIEW native_schemas AS
 SELECT id,parent_id AS native_type_id,json_extract(details,'$.version') AS version,
 json_extract(details,'$.lookup_status') AS lookup_status,
 json_extract(details,'$.member_count') AS member_count FROM items WHERE kind='native_schema';
"""


# sorted exports preserve exact scalar data while allowing users to inspect common inventory slices
def ExportCsv(Database, OutputPath, FileName, Query):
    Cursor = Database.execute(Query)
    with (OutputPath / FileName).open("w", newline="", encoding="utf-8") as Stream:
        Exporter = writer(Stream, lineterminator="\n")
        Exporter.writerow(Column[0] for Column in Cursor.description)
        Exporter.writerows(Cursor)


# stable row fingerprints distinguish reproducible content from sqlite engine file layout differences
def RecordDigest(Rows):
    Hasher = sha256()
    for Name, Mapping in (
        ("sources", Rows.Sources),
        ("items", Rows.Items),
        ("relations", Rows.Relations),
        ("gaps", Rows.Gaps),
    ):
        for Record in sorted(Mapping.values()):
            Hasher.update((Name + "\t" + JsonText(Record) + "\n").encode())
    return Hasher.hexdigest()


# complete bundles are built in a fresh directory before their final atomic publication
def WriteBundle(Rows, OutputPath, Version, AllCsv=False):
    Rows.Validate()
    Database = connect(OutputPath / "Catalog.sqlite")
    try:
        Database.executescript(KSchema)
        Metadata = {
            "schema": "FusionPlannerCatalog/1",
            "application_version": Version,
            "content_sha256": RecordDigest(Rows),
            "sqlite_version": sqlite_version,
            "scope": "Inventory and evidence metadata only",
            "support_qualification": "unverified",
            "api_wire_mapping": "unresolved",
        }
        Database.executemany(
            "INSERT INTO metadata VALUES (?,?)",
            [(Key, JsonText(Value)) for Key, Value in sorted(Metadata.items())],
        )
        SourceIds = {
            Row[0]: Index for Index, Row in enumerate(sorted(Rows.Sources.values()), 1)
        }
        ItemIds = {
            Row[0]: Index for Index, Row in enumerate(sorted(Rows.Items.values()), 1)
        }
        Database.executemany(
            "INSERT INTO source_records VALUES (?,?,?,?,?,?,?)",
            [(SourceIds[Row[0]], *Row) for Row in sorted(Rows.Sources.values())],
        )
        Database.executemany(
            "INSERT INTO item_records(row_id,id,kind,name,parent_id,source_id,details) VALUES (?,?,?,?,?,?,?)",
            [
                (
                    ItemIds[Uid],
                    Uid,
                    Kind,
                    Name,
                    ItemIds.get(Parent),
                    SourceIds[Source],
                    Details,
                )
                for Uid, Kind, Name, Parent, Source, Details in sorted(
                    Rows.Items.values()
                )
            ],
        )
        Database.executemany(
            "INSERT INTO relation_records VALUES (?,?,?,?,?)",
            [
                (ItemIds[Owner], ItemIds[Target], Relation, SourceIds[Source], Details)
                for Owner, Target, Relation, Source, Details in sorted(
                    Rows.Relations.values()
                )
            ],
        )
        Database.executemany(
            "INSERT INTO gap_records VALUES (?,?,?,?,?,?)",
            [
                (Index, Uid, Code, ItemIds.get(ItemId), SourceIds[Source], Details)
                for Index, (Uid, Code, ItemId, Source, Details) in enumerate(
                    sorted(Rows.Gaps.values()), 1
                )
            ],
        )
        Database.commit()
        if Database.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Catalogue contains dangling foreign keys")
        if Database.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("Catalogue integrity check failed")
        CsvQueries = {
            "ApiOptions.csv": "SELECT id,parent_id,kind,name,details FROM items WHERE kind IN ('api_property','api_method') ORDER BY id",
            "ApiEnums.csv": "SELECT id,parent_id,kind,name,json_extract(details,'$.value') AS value FROM items WHERE kind IN ('api_enum_value','api_constant') ORDER BY id",
            "ApiTypes.csv": "SELECT id,name,source_id,json_extract(details,'$.role') AS role,json_extract(details,'$.preview') AS preview FROM items WHERE kind='api_type' ORDER BY id",
            "Commands.csv": "SELECT id,name,source_id,json_extract(details,'$.command_id') AS command_id,json_extract(details,'$.isApplicable') AS applicable FROM items WHERE kind='ui_command' ORDER BY id",
            "NativeTypes.csv": "SELECT id,name,source_id,details FROM items WHERE kind='native_type' ORDER BY id",
            "Gaps.csv": "SELECT code,item_id,source_id,details FROM gaps ORDER BY code,item_id,id",
        }
        if AllCsv:
            for TableName in ("sources", "items", "relations", "gaps"):
                CsvQueries[TableName.capitalize() + ".csv"] = (
                    "SELECT * FROM " + TableName + " ORDER BY 1,2,3"
                )
        for FileName, Query in sorted(CsvQueries.items()):
            ExportCsv(Database, OutputPath, FileName, Query)
        Counts = Counter(Row[1] for Row in Rows.Items.values())
        GapCounts = Counter(Row[1] for Row in Rows.Gaps.values())
        Database.execute("VACUUM")
    finally:
        Database.close()
    Summary = {
        **Metadata,
        "sources": len(Rows.Sources),
        "items": dict(sorted(Counts.items())),
        "relations": len(Rows.Relations),
        "gaps": dict(sorted(GapCounts.items())),
    }
    Summary["files"] = {
        FilePath.name: {
            "size_bytes": FilePath.stat().st_size,
            "sha256": sha256(FilePath.read_bytes()).hexdigest(),
        }
        for FilePath in sorted(OutputPath.iterdir())
        if FilePath.is_file()
    }
    (OutputPath / "Manifest.json").write_text(JsonText(Summary) + "\n")
    return Summary
