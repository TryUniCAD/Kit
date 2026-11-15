<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Blind rectangular boss

Neutral model records from the controlled cases described in [the evidence guide](README.md).

```json
{
  "ledger_event_id": 305,
  "units": "mm",
  "cases": [
    {
      "case": "FirstThree2",
      "source_sha256": "7e83de78856c269c4506f68a8188450a87a160006df87eec70b225bdc08f8c0c",
      "reference_archive_sha256": "82a1d919313f0e7c8d2202b47fe2e7b1b80a098aef3f01164fd8a58454afb856",
      "model_sha256": "018c1612f516e2ecb6420e4156c51a20699c76dda5b359454d1fa5a8228cc254",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:1",
              "material_id": null,
              "name": "Body 1",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": {
                  "$type": "BoundingBox",
                  "maximum": {
                    "$type": "Vector3",
                    "x": 40.0,
                    "y": 20.0,
                    "z": 12.0
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0
                  }
                },
                "edge_count": 0,
                "face_count": 0,
                "shell_count": 0,
                "solid_count": 1,
                "surface_area": null,
                "valid": null,
                "vertex_count": 0,
                "volume": null
              }
            }
          ]
        },
        "brep": null,
        "brep_payloads": {
          "$tuple": []
        },
        "capabilities": {
          "$frozenset": [
            {
              "$enum": "Capability",
              "value": "body_structure"
            },
            {
              "$enum": "Capability",
              "value": "configurations"
            },
            {
              "$enum": "Capability",
              "value": "editable_sketches"
            },
            {
              "$enum": "Capability",
              "value": "parameters"
            },
            {
              "$enum": "Capability",
              "value": "parametric_history"
            },
            {
              "$enum": "Capability",
              "value": "support_planes"
            }
          ]
        },
        "configurations": {
          "$tuple": [
            {
              "$type": "Configuration",
              "active": true,
              "attributes": {},
              "id": "sldprt:configuration:0",
              "name": "Default",
              "overrides": {
                "$tuple": []
              },
              "parent_id": null,
              "suppressed_feature_ids": {
                "$tuple": []
              }
            }
          ]
        },
        "diagnostics": {
          "$tuple": []
        },
        "feature_timeline": {
          "$tuple": [
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Plane",
                "support_plane_id": "sldprt:plane:2"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:2",
              "input_feature_ids": {
                "$tuple": []
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Front Plane",
              "operation": null,
              "order": 14,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Sketch"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:26",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Profile87ed31a80941492d84ba4fac888886b2",
              "operation": null,
              "order": 24,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {},
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "blind"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 12.0
                },
                "offset": null,
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "Bossc3aea6497bb04e7882bbc10ab14deb34",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "join"
              },
              "order": 25,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:D1"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            }
          ]
        },
        "meshes": {
          "$tuple": []
        },
        "metadata": {},
        "parameters": {
          "$tuple": [
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:D1",
              "name": "D1",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 12.0
              }
            }
          ]
        },
        "schema_version": "1.0",
        "selections": {
          "$tuple": []
        },
        "sketches": {
          "$tuple": [
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:26:native:7436",
                      "sldprt:sketch:26:native:7344",
                      "sldprt:sketch:26:native:7620",
                      "sldprt:sketch:26:native:7528"
                    ]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7978",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "",
                          "point": "origin"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7756",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7811",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7866",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7921",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:0:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:1:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": "end"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:2:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:3:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  }
                ]
              },
              "entities": {
                "$tuple": [
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7436",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7344",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7620",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7528",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "Profile87ed31a80941492d84ba4fac888886b2",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            }
          ]
        },
        "source": {
          "$type": "CadSource",
          "application_version": "",
          "attributes": {},
          "container_version": "",
          "format_id": "interchange.json",
          "path": "editable-extrusion",
          "sha256": "a462bfa210479658a9a2d67040bd9e9cdff2e90d1c2026ad693ba02f61ab26f5"
        },
        "support_planes": {
          "$tuple": [
            {
              "$type": "SupportPlane",
              "attributes": {},
              "id": "sldprt:plane:2",
              "name": "Front Plane",
              "offset_parameter_id": null,
              "provenance": null,
              "support_selection_id": null,
              "transform": {
                "$type": "Transform",
                "origin": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "x_axis": {
                  "$type": "Vector3",
                  "x": 1.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "y_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 1.0,
                  "z": 0.0
                },
                "z_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 1.0
                }
              }
            }
          ]
        },
        "units": {
          "$enum": "UnitSystem",
          "value": "mm"
        }
      }
    },
    {
      "case": "FirstThree3",
      "source_sha256": "5f3aa2b695ca12aed2e91b6e354cc46d266f20d76adc3aabf367e61499a0ea96",
      "reference_archive_sha256": "5b066dc0adf25bc94f4f33d95dee09f9c39e6fa7d67a1f9a773b47a5312b2a3e",
      "model_sha256": "079ff7cb1b519dc1b3edbcf2e854398c1c4913dc938dbe8a4b95f92c5aedd5f7",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:1",
              "material_id": null,
              "name": "Body 1",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": {
                  "$type": "BoundingBox",
                  "maximum": {
                    "$type": "Vector3",
                    "x": 40.0,
                    "y": 20.0,
                    "z": 0.0
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": 0.0,
                    "y": 0.0,
                    "z": -18.000000000000004
                  }
                },
                "edge_count": 0,
                "face_count": 0,
                "shell_count": 0,
                "solid_count": 1,
                "surface_area": null,
                "valid": null,
                "vertex_count": 0,
                "volume": null
              }
            }
          ]
        },
        "brep": null,
        "brep_payloads": {
          "$tuple": []
        },
        "capabilities": {
          "$frozenset": [
            {
              "$enum": "Capability",
              "value": "body_structure"
            },
            {
              "$enum": "Capability",
              "value": "configurations"
            },
            {
              "$enum": "Capability",
              "value": "editable_sketches"
            },
            {
              "$enum": "Capability",
              "value": "parameters"
            },
            {
              "$enum": "Capability",
              "value": "parametric_history"
            },
            {
              "$enum": "Capability",
              "value": "support_planes"
            }
          ]
        },
        "configurations": {
          "$tuple": [
            {
              "$type": "Configuration",
              "active": true,
              "attributes": {},
              "id": "sldprt:configuration:0",
              "name": "Default",
              "overrides": {
                "$tuple": []
              },
              "parent_id": null,
              "suppressed_feature_ids": {
                "$tuple": []
              }
            }
          ]
        },
        "diagnostics": {
          "$tuple": []
        },
        "feature_timeline": {
          "$tuple": [
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Plane",
                "support_plane_id": "sldprt:plane:2"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:2",
              "input_feature_ids": {
                "$tuple": []
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Front Plane",
              "operation": null,
              "order": 14,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Sketch"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:26",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Profile216499ba9532456989b687a6612e0fb6",
              "operation": null,
              "order": 24,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {},
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "blind"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 18.000000000000004
                },
                "offset": null,
                "reversed": true,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "Bossed943ea183d34723b3483021596ae191",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "join"
              },
              "order": 25,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:D1"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            }
          ]
        },
        "meshes": {
          "$tuple": []
        },
        "metadata": {},
        "parameters": {
          "$tuple": [
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:D1",
              "name": "D1",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 18.000000000000004
              }
            }
          ]
        },
        "schema_version": "1.0",
        "selections": {
          "$tuple": []
        },
        "sketches": {
          "$tuple": [
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:26:native:7436",
                      "sldprt:sketch:26:native:7344",
                      "sldprt:sketch:26:native:7620",
                      "sldprt:sketch:26:native:7528"
                    ]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7978",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "",
                          "point": "origin"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7756",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7811",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7866",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7921",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:0:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:1:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": "end"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:2:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:3:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  }
                ]
              },
              "entities": {
                "$tuple": [
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7436",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7344",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7620",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7528",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "Profile216499ba9532456989b687a6612e0fb6",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            }
          ]
        },
        "source": {
          "$type": "CadSource",
          "application_version": "",
          "attributes": {},
          "container_version": "",
          "format_id": "interchange.json",
          "path": "editable-extrusion",
          "sha256": "c113bef8dd041599bef173c8d48acbf6150a3fc63b92f86a583c9c3a6603a438"
        },
        "support_planes": {
          "$tuple": [
            {
              "$type": "SupportPlane",
              "attributes": {},
              "id": "sldprt:plane:2",
              "name": "Front Plane",
              "offset_parameter_id": null,
              "provenance": null,
              "support_selection_id": null,
              "transform": {
                "$type": "Transform",
                "origin": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "x_axis": {
                  "$type": "Vector3",
                  "x": 1.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "y_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 1.0,
                  "z": 0.0
                },
                "z_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 1.0
                }
              }
            }
          ]
        },
        "units": {
          "$enum": "UnitSystem",
          "value": "mm"
        }
      }
    },
    {
      "case": "FirstThree4",
      "source_sha256": "88b0caafd53d3cd57874ce6b3139b8301b339b9b3ab77721effd6163b4a642bc",
      "reference_archive_sha256": "1ccf190ae07c77feb76414a92bcafe8fd1b01a5d03506f18ca69802154eebe70",
      "model_sha256": "5c85219a9aa0c7d32db42c2ca1ec9e1edc57b3ee5a4f580a1bfca9092c9ba69f",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:32",
              "id": "sldprt:body:1",
              "material_id": null,
              "name": "Body 1",
              "provenance": null,
              "topology": {
                "$type": "TopologySummary",
                "bounding_box": {
                  "$type": "BoundingBox",
                  "maximum": {
                    "$type": "Vector3",
                    "x": 40.0,
                    "y": 20.0,
                    "z": 0.0
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": 0.0,
                    "y": 0.0,
                    "z": -10.0
                  }
                },
                "edge_count": 0,
                "face_count": 0,
                "shell_count": 0,
                "solid_count": 1,
                "surface_area": null,
                "valid": null,
                "vertex_count": 0,
                "volume": null
              }
            }
          ]
        },
        "brep": null,
        "brep_payloads": {
          "$tuple": []
        },
        "capabilities": {
          "$frozenset": [
            {
              "$enum": "Capability",
              "value": "body_structure"
            },
            {
              "$enum": "Capability",
              "value": "configurations"
            },
            {
              "$enum": "Capability",
              "value": "editable_sketches"
            },
            {
              "$enum": "Capability",
              "value": "parameters"
            },
            {
              "$enum": "Capability",
              "value": "parametric_history"
            },
            {
              "$enum": "Capability",
              "value": "support_planes"
            }
          ]
        },
        "configurations": {
          "$tuple": [
            {
              "$type": "Configuration",
              "active": true,
              "attributes": {},
              "id": "sldprt:configuration:0",
              "name": "Default",
              "overrides": {
                "$tuple": []
              },
              "parent_id": null,
              "suppressed_feature_ids": {
                "$tuple": []
              }
            }
          ]
        },
        "diagnostics": {
          "$tuple": []
        },
        "feature_timeline": {
          "$tuple": [
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Plane",
                "support_plane_id": "sldprt:plane:2"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:2",
              "input_feature_ids": {
                "$tuple": []
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Front Plane",
              "operation": null,
              "order": 14,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": null,
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {
                "native_type": "Sketch"
              },
              "configuration_states": {
                "$tuple": []
              },
              "definition": null,
              "id": "sldprt:feature:26",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "Profile8a31f730a0a9436da733680a8598788b",
              "operation": null,
              "order": 24,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            },
            {
              "$type": "FeatureStep",
              "attributes": {},
              "configuration_states": {
                "$tuple": []
              },
              "definition": {
                "$type": "ExtrusionFeature",
                "direction": null,
                "draft_angle": null,
                "end_condition": {
                  "$enum": "ExtrusionEndCondition",
                  "value": "blind"
                },
                "length": {
                  "$type": "ParameterValue",
                  "kind": {
                    "$enum": "ValueKind",
                    "value": "length"
                  },
                  "unit": "mm",
                  "value": 10.0
                },
                "offset": null,
                "reversed": true,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:32",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:26"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "Boss1da9cfc851374399b896b6dce50d1295",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "join"
              },
              "order": 25,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:32:D1"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:26",
              "suppressed": false
            }
          ]
        },
        "meshes": {
          "$tuple": []
        },
        "metadata": {},
        "parameters": {
          "$tuple": [
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:32:D1",
              "name": "D1",
              "owner_id": "sldprt:feature:32",
              "provenance": null,
              "role": {
                "$enum": "ParameterRole",
                "value": "driving"
              },
              "value": {
                "$type": "ParameterValue",
                "kind": {
                  "$enum": "ValueKind",
                  "value": "length"
                },
                "unit": "mm",
                "value": 10.0
              }
            }
          ]
        },
        "schema_version": "1.0",
        "selections": {
          "$tuple": []
        },
        "sketches": {
          "$tuple": [
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:26:native:7436",
                      "sldprt:sketch:26:native:7344",
                      "sldprt:sketch:26:native:7620",
                      "sldprt:sketch:26:native:7528"
                    ]
                  }
                ]
              },
              "constraints": {
                "$tuple": [
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7978",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "",
                          "point": "origin"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7756",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7811",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7866",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:relation:7921",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": ""
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:0:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:1:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": "end"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:2:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7436",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7528",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  },
                  {
                    "$type": "SketchConstraint",
                    "attributes": {},
                    "driving": true,
                    "id": "sldprt:constraint:26:vertex:3:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7344",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7620",
                          "point": "start"
                        }
                      ]
                    },
                    "suppressed": false
                  }
                ]
              },
              "entities": {
                "$tuple": [
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7436",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7344",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7620",
                    "kind": "line",
                    "provenance": null
                  },
                  {
                    "$type": "SketchEntity",
                    "attributes": {},
                    "construction": false,
                    "fixed": false,
                    "geometry": {
                      "$type": "LineGeometry",
                      "end": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 20.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 20.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7528",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "Profile8a31f730a0a9436da733680a8598788b",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            }
          ]
        },
        "source": {
          "$type": "CadSource",
          "application_version": "",
          "attributes": {},
          "container_version": "",
          "format_id": "interchange.json",
          "path": "editable-extrusion",
          "sha256": "a07d72708aaca0b04726f0c9cafcbde8f7b6d4e859c08506c84515d8bada8c08"
        },
        "support_planes": {
          "$tuple": [
            {
              "$type": "SupportPlane",
              "attributes": {},
              "id": "sldprt:plane:2",
              "name": "Front Plane",
              "offset_parameter_id": null,
              "provenance": null,
              "support_selection_id": null,
              "transform": {
                "$type": "Transform",
                "origin": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "x_axis": {
                  "$type": "Vector3",
                  "x": 1.0,
                  "y": 0.0,
                  "z": 0.0
                },
                "y_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 1.0,
                  "z": 0.0
                },
                "z_axis": {
                  "$type": "Vector3",
                  "x": 0.0,
                  "y": 0.0,
                  "z": 1.0
                }
              }
            }
          ]
        },
        "units": {
          "$enum": "UnitSystem",
          "value": "mm"
        }
      }
    }
  ]
}
```
