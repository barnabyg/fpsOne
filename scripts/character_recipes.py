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
        'scale': 1.08, 'restYaw': 0, 'gestureSide': 'R',
        'animationDuration': 24.0,
        'restElbows': {'L': -18.0, 'R': -20.0},
        'restLean': (0.0, -0.7, 0.8),
        'breathCycles': (5, 2),
        'weightShift': {'cycles': (1, 3), 'phases': (-0.4, 0.8)},
        'blinkTimes': (2.1, 5.7, 9.8, 15.2, 21.4),
        'glances': (
            {'start': 3.8, 'peak': 4.9, 'end': 6.1, 'yaw': -3.2, 'pitch': 0.8},
            {'start': 13.0, 'peak': 14.4, 'end': 15.8, 'yaw': 2.4, 'pitch': -0.5},
            {'start': 19.6, 'peak': 20.5, 'end': 21.7, 'yaw': -1.8, 'pitch': 0.4},
        ),
        'handAdjustments': (
            {'start': 10.8, 'peak': 11.8, 'end': 12.8, 'side': 'L', 'wrist': (1.2, -1.8, 1.0), 'curl': 3.0},
            {'start': 17.2, 'peak': 18.0, 'end': 19.0, 'side': 'R', 'wrist': (-1.0, 1.4, -0.8), 'curl': -2.0},
        ),
        'talkGestures': (
            {'start': 1.2, 'peak': 2.5, 'end': 3.8, 'side': 'R',
             'upper': (-7.0, 1.0, -8.0), 'lower': (18.0, -5.0, 0.0),
             'wrist': (1.0, 12.0, 3.0), 'head': (1.4, 0.8, 0.0), 'curl': -3.0},
            {'start': 6.8, 'peak': 8.2, 'end': 9.6, 'side': 'R',
             'upper': (-4.0, -2.0, -11.0), 'lower': (14.0, 3.0, 2.0),
             'wrist': (-2.0, 7.0, -5.0), 'head': (-0.6, -1.1, 0.0), 'curl': 2.0},
        ),
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
        'scale': 1.08, 'restYaw': 180, 'gestureSide': 'L',
        'animationDuration': 24.0,
        'restElbows': {'L': -20.0, 'R': -17.0},
        'restLean': (0.4, 0.8, -0.7),
        'breathCycles': (4, 3),
        'weightShift': {'cycles': (2, 5), 'phases': (0.7, -0.5)},
        'blinkTimes': (1.4, 6.2, 11.1, 17.0, 22.6),
        'glances': (
            {'start': 2.4, 'peak': 3.3, 'end': 4.3, 'yaw': 2.0, 'pitch': -0.4},
            {'start': 9.8, 'peak': 11.2, 'end': 12.7, 'yaw': -3.5, 'pitch': 0.7},
            {'start': 17.0, 'peak': 18.4, 'end': 19.6, 'yaw': 2.8, 'pitch': 0.3},
        ),
        'handAdjustments': (
            {'start': 5.2, 'peak': 6.0, 'end': 6.9, 'side': 'R', 'wrist': (-1.0, 1.6, 0.8), 'curl': 3.5},
            {'start': 14.0, 'peak': 15.0, 'end': 16.0, 'side': 'L', 'wrist': (1.4, -1.2, -1.0), 'curl': -2.5},
        ),
        'talkGestures': (
            {'start': 2.0, 'peak': 3.4, 'end': 4.8, 'side': 'L',
             'upper': (-5.0, -1.0, 9.0), 'lower': (16.0, 5.0, 0.0),
             'wrist': (-1.0, -10.0, -4.0), 'head': (0.6, -1.2, 0.0), 'curl': -2.0},
            {'start': 9.2, 'peak': 10.6, 'end': 12.0, 'side': 'L',
             'upper': (-8.0, 2.0, 6.0), 'lower': (20.0, -3.0, -1.0),
             'wrist': (3.0, -5.0, 6.0), 'head': (1.2, 0.7, 0.0), 'curl': 4.0},
        ),
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
