# explicit solids exercise distinct material schemas and actual property changes
KRichBasic: dict[str, object] = {
    "structural_class": "Basic",
    "type": "Generic",
    "component_default": False,
    "mechanics": {
        "conductivity_w_m_k": 2.5,
        "specific_heat_j_kg_k": 780.0,
        "damping": 0.02,
    },
    "thermal": None,
    "finish": {
        "name": "Opaque test finish",
        "kind": "opaque",
        "color_space": 0,
        "roughness": 0.4,
        "anisotropy": 0.125,
        "rotation": 0.25,
        "tint_rgba": [1.0, 1.0, 1.0, 1.0],
        "reflectance": 0.08,
        "translucent": False,
        "scatter_distance_mm": None,
        "scatter_color_rgba": [1.0, 1.0, 1.0, 1.0],
    },
}

# explicit thermal values verify that the package keeps the requested thermal role
KTrialThermal = {
    "density_kg_m3": 7900.0,
    "conductivity_w_m_k": 48.0,
    "specific_heat_j_kg_k": 520.0,
    "emissivity": 0.65,
    "resistivity_ohm_m": 1.6e-7,
    "permeability": 0.0,
    "porosity": 0.001,
    "reflectivity": 0.1,
    "transmits_light": False,
}

# the metal trial needs populated mechanical and thermal aspects plus a metallic finish
KRichMetal: dict[str, object] = {
    "structural_class": "Metal",
    "type": "Metal",
    "component_default": True,
    "mechanics": {
        "conductivity_w_m_k": 48.0,
        "specific_heat_j_kg_k": 520.0,
        "damping": 0.01,
        "young_modulus_pa": 182e9,
        "poisson_ratio": 0.25,
        "shear_modulus_pa": 72e9,
        "yield_strength_pa": 230e6,
        "tensile_strength_pa": 385e6,
        "expansion_per_k": 1e-5,
        "behavior": "Isotropic",
        "directional_expansion_per_k": {
            AxisName: 2e-6 for AxisName in ("1", "2", "X", "Y", "Z")
        },
    },
    "thermal": KTrialThermal,
    "finish": {
        "name": "Metallic test finish",
        "kind": "metal",
        "color_space": 1,
        "roughness": 0.35,
        "anisotropy": 0.125,
        "rotation": 0.25,
        "tint_rgba": [1.0, 1.0, 1.0, 1.0],
    },
}
