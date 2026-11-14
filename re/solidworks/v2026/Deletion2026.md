# SOLIDWORKS 2026 stream deletion classes

Question: which streams of a 2026-saved part must a writer emit for SOLIDWORKS 2026 SP05.2
(`34.5.2`) to open the part with its feature tree and body?

## Method

- Source: `L1_boss.SLDPRT`, authored and saved by 2026 through `re/tooling/sw2026/Author.py`
  (one sketch, one boss extrude, 40 x 20 x 10 mm box, volume 8e-6 m^3).
- `re/tooling/sw2026/Deletion.py` rebuilt the container 41 times with Kit's container writer:
  `full_rebuilt` (all 40 streams) and `drop_NN` (all streams except stream NN). The stream bytes
  are the 2026-saved bytes; only the container is rebuilt. These files are measurement inputs,
  never Kit output.
- `re/tooling/sw2026/Measure.py` opened each variant silently, rebuilt it, and recorded open
  errors, bodies, mass properties and features.
- Pass 1 (one instance, restart every 20 launches) gave 4 crashes and 14 "interface is unknown"
  failures. One control also failed with "interface is unknown" and passed after a restart.
- Pass 2 reran the 18 failures with a fresh SOLIDWORKS before every file and a control after
  every failure (`job_retry.json`, `result_retry.json`). All 19 controls opened with 1 body and
  volume 8e-6 m^3.

## Gotcha

"The interface is unknown" (`0x800706B5`) after an earlier document closes means the
SOLIDWORKS COM server is unhealthy. It does not prove that the next file is bad. Retry such a
failure in a fresh instance, with a control, before you classify it.

## Result (pass 2 for the 18 retried streams, pass 1 for the rest)

| stream | without it | class |
| --- | --- | --- |
| `Contents/CMgr` | SOLIDWORKS process dies (RPC failure); control after restart passes | **load-critical** |
| `Contents/Config-0` | process dies; control passes | **load-critical** |
| `Contents/Definition` | process dies; control passes | **load-critical** |
| `_MO_VERSION_19000/Biography` | process dies; control passes | **load-critical** |
| `_MO_VERSION_19000/History` | process dies; control passes | **load-critical** |
| `Contents/Config-0-ModelHeader` | `OpenDoc6` returns a document with no `FirstFeature`; control passes | **load-critical** |
| `Contents/Config-0-ResolvedFeatures` | opens with 0 errors but 0 bodies and volume 0 | **model-critical** |
| `Header2` | opens, 1 body, 8e-6 m^3 | optional |
| `Contents/Config-0-Partition` | opens, 1 body, 8e-6 m^3 | optional |
| `Contents/Config-0-LWDATA` | opens, 1 body, 8e-6 m^3 | optional |
| `Contents/DisplayLists` | opens, 1 body, 8e-6 m^3 | optional |
| `Contents/CMgrHdr2`, `Contents/CusProps`, `Contents/CnfgObjs` | open, 1 body, 8e-6 m^3 | optional |
| `Contents/3DExperienceExchange2`, `Contents/3DExperienceExchange_ConfigHeader`, `Contents/PMISemanticDataDB`, `Contents/eModelLic`, `Contents/OleItems`, `OleItemInformation/OLE_Item_Data` | open, 1 body, 8e-6 m^3 | optional |
| `ModelStamps`, `_DL_VERSION_19000/DLUpdateStamp`, `Preview`, `PreviewPNG` | open, 1 body, 8e-6 m^3 | optional |
| `SwDocContentMgr/SwDocContentMgrInfo`, `ThirdPty/*`, `ThirdPtyStore/VisualStates` | open, 1 body, 8e-6 m^3 | optional |
| `[Content_Types].xml`, `_rels/.rels`, `docProps/*.xml`, `swXmlContents/Features`, `swXmlContents/KeyWords` | open, 1 body, 8e-6 m^3 | optional |

`full_rebuilt` opened with 0 errors, 1 body and 8e-6 m^3, so Kit's container writer reproduces a
2026 container that SOLIDWORKS accepts.

## Consequence for the writer

The minimum native part is these seven streams, each generated from the model:
`Contents/CMgr`, `Contents/Config-0`, `Contents/Config-0-ModelHeader`,
`Contents/Config-0-ResolvedFeatures`, `Contents/Definition`, `_MO_VERSION_19000/Biography`,
`_MO_VERSION_19000/History`. "Optional" means only that SOLIDWORKS opens and rebuilds the part
without the stream. A stream that carries model information (custom properties, appearances,
display states, configurations) is still required when the neutral document has that
information.

Raw data: `.rescratch/sw26/deletion/L1/` (`names.json`, `result.json`, `result_retry.json`).
