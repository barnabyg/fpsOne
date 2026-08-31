"""The two CC0 residents, shared by Blender export and Unreal import."""

RECIPES = {
    'A': {
        'macro': dict(gender=1.0, age=0.42, muscle=0.43, weight=0.48, height=0.53, proportions=0.55,
                      race=dict(caucasian=0.85, asian=0.15, african=0.0)),
        'parts': {'ShirtDenim': ('clothes', 'male_casualsuit03', 'Clothes'),
                  'Shoes': ('clothes', 'shoes01', 'Clothes'), 'Hair': ('hair', 'short02', 'Hair'),
                  'Brows': ('eyebrows', 'eyebrow002', 'Eyebrows')},
        'textures': {
            'Skin': ('skins/middleage_caucasian_male/middleage_lightskinned_male_diffuse.png', None, 0.65),
            'ShirtDenim': ('clothes/male_casualsuit03/male_casualsuit03_diffuse.png', 'clothes/male_casualsuit03/male_casualsuit03_normal.png', 0.82),
            'Shoes': ('clothes/shoes01/shoes01_diffuse.png', None, 0.6),
            'Hair': ('hair/short02/short02_diffuse.png', None, 0.6),
            'Brows': ('eyebrows/eyebrow002/eyebrow002.png', None, 0.85),
        },
        'scale': 1.08, 'restYaw': 0, 'gestureSide': 'R', 'blinkTimes': (2.1, 5.7),
    },
    'B': {
        'macro': dict(gender=0.0, age=0.50, muscle=0.27, weight=0.60, height=0.45, proportions=0.46,
                      race=dict(caucasian=0.15, asian=0.85, african=0.0)),
        'parts': {'BlouseSkirt': ('clothes', 'female_elegantsuit01', 'Clothes'),
                  'Shoes': ('clothes', 'shoes03', 'Clothes'), 'Hair': ('hair', 'ponytail01', 'Hair'),
                  'Brows': ('eyebrows', 'eyebrow001', 'Eyebrows')},
        'textures': {
            'Skin': ('skins/middleage_asian_female/middleage_lightskinned_female_diffuse2.png', None, 0.65),
            'BlouseSkirt': ('clothes/female_elegantsuit01/female_elegantsuit01_diffuse.png', 'clothes/female_elegantsuit01/female_elegantsuit01_normal.png', 0.82),
            'Shoes': ('clothes/shoes03/shoes03_diffuse.png', None, 0.6),
            'Hair': ('hair/ponytail01/ponytail01_diffuse.png', None, 0.6),
            'Brows': ('eyebrows/eyebrow001/eyebrow001.png', None, 0.85),
        },
        'scale': 1.08, 'restYaw': 180, 'gestureSide': 'L', 'blinkTimes': (2.4, 6.2),
        'materialTints': {'BlouseSkirt': (0.38, 0.80, 0.68)},
    },
}


def resident_recipe(resident):
    recipe = RECIPES[resident]
    return {
        **recipe,
        'parts': {**recipe['parts'], 'Eyes': ('eyes', 'high-poly', 'Eyes'),
                  'Lashes': ('eyelashes', 'eyelashes01', 'Eyelashes')},
        'textures': {**recipe['textures'], 'Eyes': ('eyes/materials/brown_eye.png', None, 0.18),
                     'Lashes': ('eyelashes/eyelashes01/eyelashes01.png', None, 0.85)},
    }
