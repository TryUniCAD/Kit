<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Blind rectangular pocket

Neutral model records from the controlled cases described in [the evidence guide](README.md).

```json
{
  "ledger_event_id": 304,
  "units": "mm",
  "cases": [
    {
      "case": "FirstThree0",
      "source_sha256": "238ebaddaef41790c2fb2e2d9d02420e1bf86c7bbdbb89b1ff34ed1601445ca6",
      "reference_archive_sha256": "c3250afe8db467e8000c6d000107bae0aefb7a86380c8f3558ebb167d03e5f57",
      "model_sha256": "39119d6d22d6dc28300ec108cd9a086df336084018292e1b468096fd48120887",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:40",
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
                    "y": 30.0,
                    "z": 20.0
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
              "name": "GrammarBaseProfile",
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
                  "value": 20.0
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
              "name": "GrammarBoss",
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
              "id": "sldprt:feature:33",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "GrammarCutProfile",
              "operation": null,
              "order": 26,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:33",
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
                "reversed": false,
                "second_draft_angle": null,
                "second_end_condition": null,
                "second_length": null,
                "second_offset": null,
                "second_up_to_reference": "",
                "symmetric": false,
                "up_to_reference": ""
              },
              "id": "sldprt:feature:40",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:32", "sldprt:feature:33"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "GrammarCut",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "cut"
              },
              "order": 27,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:40:D1"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:33",
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
                "value": 20.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:40:D1",
              "name": "D1",
              "owner_id": "sldprt:feature:40",
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
                      "sldprt:sketch:26:native:7632",
                      "sldprt:sketch:26:native:7540",
                      "sldprt:sketch:26:native:7816",
                      "sldprt:sketch:26:native:7724"
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
                    "id": "sldprt:constraint:26:relation:8174",
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
                          "entity_id": "sldprt:sketch:26:native:7540",
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
                    "id": "sldprt:constraint:26:relation:7952",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7632",
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
                    "id": "sldprt:constraint:26:relation:8007",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7540",
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
                    "id": "sldprt:constraint:26:relation:8062",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7816",
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
                    "id": "sldprt:constraint:26:relation:8117",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7724",
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
                          "entity_id": "sldprt:sketch:26:native:7632",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7540",
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
                          "entity_id": "sldprt:sketch:26:native:7816",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7724",
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
                          "entity_id": "sldprt:sketch:26:native:7632",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7724",
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
                          "entity_id": "sldprt:sketch:26:native:7540",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7816",
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
                        "y": 30.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7632",
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
                    "id": "sldprt:sketch:26:native:7540",
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
                        "y": 30.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7816",
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
                        "y": 30.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 30.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7724",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "GrammarBaseProfile",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            },
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:33:native:13170",
                      "sldprt:sketch:33:native:13078",
                      "sldprt:sketch:33:native:13354",
                      "sldprt:sketch:33:native:13262"
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
                    "id": "sldprt:constraint:33:relation:13490",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13170",
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
                    "id": "sldprt:constraint:33:relation:13545",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13078",
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
                    "id": "sldprt:constraint:33:relation:13600",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13354",
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
                    "id": "sldprt:constraint:33:relation:13655",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13262",
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
                    "id": "sldprt:constraint:33:vertex:0:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13170",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13078",
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
                    "id": "sldprt:constraint:33:vertex:1:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13354",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13262",
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
                    "id": "sldprt:constraint:33:vertex:2:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13170",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13262",
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
                    "id": "sldprt:constraint:33:vertex:3:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13078",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13354",
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
                        "x": 5.0,
                        "y": 15.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 5.0,
                        "y": 5.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13170",
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
                        "x": 25.0,
                        "y": 5.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 5.0,
                        "y": 5.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13078",
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
                        "x": 25.0,
                        "y": 15.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 25.0,
                        "y": 5.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13354",
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
                        "x": 25.0,
                        "y": 15.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 5.0,
                        "y": 15.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13262",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:33",
              "name": "GrammarCutProfile",
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
          "sha256": "086d3fcc8afa546743960e2781b5313fd85f5b3b68a28578d7acc4dcc3eed70d"
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
      "case": "FirstThree1",
      "source_sha256": "515975f58eb0dbd9a81193bd3036ccced047e4585242fb03c15845e53bb2cd14",
      "reference_archive_sha256": "020590569abada50c7ff905d18d2fb4137f51c35557747436a6bae4650151fa5",
      "model_sha256": "2f2c2d62e838039b353c6524a850d1da5d1f94f055317c5f778a044089a5f997",
      "model": {
        "$type": "CadDocument",
        "assembly": null,
        "bodies": {
          "$tuple": [
            {
              "$type": "Body",
              "attributes": {},
              "final_feature_id": "sldprt:feature:40",
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
                    "y": 30.0,
                    "z": 0.0
                  },
                  "minimum": {
                    "$type": "Vector3",
                    "x": 0.0,
                    "y": 0.0,
                    "z": -20.0
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
              "name": "GrammarBaseProfile",
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
                  "value": 20.0
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
              "name": "GrammarBoss",
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
              "id": "sldprt:feature:33",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:2"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "reference"
              },
              "name": "GrammarCutProfile",
              "operation": null,
              "order": 26,
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:33",
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
              "id": "sldprt:feature:40",
              "input_feature_ids": {
                "$tuple": ["sldprt:feature:32", "sldprt:feature:33"]
              },
              "kind": {
                "$enum": "FeatureKind",
                "value": "extrusion"
              },
              "name": "GrammarCut",
              "operation": {
                "$enum": "BooleanOperation",
                "value": "cut"
              },
              "order": 27,
              "parameter_ids": {
                "$tuple": ["sldprt:parameter:40:D1"]
              },
              "provenance": null,
              "selection_ids": {
                "$tuple": []
              },
              "sketch_id": "sldprt:sketch:33",
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
                "value": 20.0
              }
            },
            {
              "$type": "Parameter",
              "attributes": {},
              "expression": null,
              "id": "sldprt:parameter:40:D1",
              "name": "D1",
              "owner_id": "sldprt:feature:40",
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
                      "sldprt:sketch:26:native:7632",
                      "sldprt:sketch:26:native:7540",
                      "sldprt:sketch:26:native:7816",
                      "sldprt:sketch:26:native:7724"
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
                    "id": "sldprt:constraint:26:relation:8174",
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
                          "entity_id": "sldprt:sketch:26:native:7540",
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
                    "id": "sldprt:constraint:26:relation:7952",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7632",
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
                    "id": "sldprt:constraint:26:relation:8007",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7540",
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
                    "id": "sldprt:constraint:26:relation:8062",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7816",
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
                    "id": "sldprt:constraint:26:relation:8117",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7724",
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
                          "entity_id": "sldprt:sketch:26:native:7632",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7540",
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
                          "entity_id": "sldprt:sketch:26:native:7816",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7724",
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
                          "entity_id": "sldprt:sketch:26:native:7632",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7724",
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
                          "entity_id": "sldprt:sketch:26:native:7540",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:26:native:7816",
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
                        "y": 30.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7632",
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
                    "id": "sldprt:sketch:26:native:7540",
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
                        "y": 30.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 40.0,
                        "y": 0.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7816",
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
                        "y": 30.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 0.0,
                        "y": 30.0
                      }
                    },
                    "id": "sldprt:sketch:26:native:7724",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:26",
              "name": "GrammarBaseProfile",
              "parameter_ids": {
                "$tuple": []
              },
              "provenance": null,
              "support_plane_id": "sldprt:plane:2",
              "suppressed": false
            },
            {
              "$type": "Sketch",
              "attributes": {},
              "closed_profile_entity_ids": {
                "$tuple": [
                  {
                    "$tuple": [
                      "sldprt:sketch:33:native:13170",
                      "sldprt:sketch:33:native:13078",
                      "sldprt:sketch:33:native:13354",
                      "sldprt:sketch:33:native:13262"
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
                    "id": "sldprt:constraint:33:relation:13490",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13170",
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
                    "id": "sldprt:constraint:33:relation:13545",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13078",
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
                    "id": "sldprt:constraint:33:relation:13600",
                    "kind": "vertical",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13354",
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
                    "id": "sldprt:constraint:33:relation:13655",
                    "kind": "horizontal",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13262",
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
                    "id": "sldprt:constraint:33:vertex:0:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13170",
                          "point": "start"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13078",
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
                    "id": "sldprt:constraint:33:vertex:1:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13354",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13262",
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
                    "id": "sldprt:constraint:33:vertex:2:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13170",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13262",
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
                    "id": "sldprt:constraint:33:vertex:3:1",
                    "kind": "coincident",
                    "parameter_id": null,
                    "provenance": null,
                    "references": {
                      "$tuple": [
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13078",
                          "point": "end"
                        },
                        {
                          "$type": "ConstraintReference",
                          "entity_id": "sldprt:sketch:33:native:13354",
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
                        "x": 5.0,
                        "y": 15.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 5.0,
                        "y": 5.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13170",
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
                        "x": 25.0,
                        "y": 5.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 5.0,
                        "y": 5.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13078",
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
                        "x": 25.0,
                        "y": 15.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 25.0,
                        "y": 5.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13354",
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
                        "x": 25.0,
                        "y": 15.0
                      },
                      "start": {
                        "$type": "Vector2",
                        "x": 5.0,
                        "y": 15.0
                      }
                    },
                    "id": "sldprt:sketch:33:native:13262",
                    "kind": "line",
                    "provenance": null
                  }
                ]
              },
              "id": "sldprt:sketch:33",
              "name": "GrammarCutProfile",
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
          "sha256": "e8c18ab2892e1bb0d968ebdd0a1aa8b950e940839e6d405de778a14e0721cb3b"
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
