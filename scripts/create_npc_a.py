"""Editable NPC A recipe; original pose/animation contributions are CC0-1.0.

Blender 4.5.3 + MPFB 2.0.8. Run with -- --tools C:/.../character-tools.
Only selected MakeHuman core assets are used (see ASSETS.md). No mocap.
"""
import argparse
import json
import hashlib
import math
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'SourceArt/Characters/NPC_A'
parser = argparse.ArgumentParser()
parser.add_argument('--tools', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
assert bpy.app.version[:3] == (4, 5, 3), 'Use the pinned Blender 4.5.3'
tools = args.tools.resolve()
OUTPUT.mkdir(parents=True, exist_ok=True)
bpy.ops.preferences.extension_repo_add(name='fpsone', custom_directory=str(tools / 'extensions'), use_custom_directory=True, type='LOCAL')
bpy.context.preferences.extensions.repos[-1].module = 'fpsone'
bpy.ops.preferences.addon_enable(module='bl_ext.fpsone.mpfb')
from bl_ext.fpsone.mpfb import VERSION
from bl_ext.fpsone.mpfb.services.humanservice import HumanService
from bl_ext.fpsone.mpfb.services.targetservice import TargetService
assert VERSION == (2, 0, 8), 'Use pinned MPFB 2.0.8'

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
macro = TargetService.get_default_macro_info_dict()
macro.update(gender=1.0, age=0.42, muscle=0.43, weight=0.48, height=0.53, proportions=0.55)
macro['race'] = dict(caucasian=0.85, asian=0.15, african=0.0)
body = HumanService.create_human(macro_detail_dict=macro)
body.name = 'ResidentA'
rig = HumanService.add_builtin_rig(body, 'default')
# Unreal's legacy FBX importer strips nodes literally named Armature. Retain
# this explicit root so the metre-to-centimetre transform also survives in clips.
rig.name = 'ResidentARig'


def load_part(folder, name, kind):
    return HumanService.add_mhclo_asset(str(tools / 'core' / folder / name / (name + '.mhclo')),
                                       body, asset_type=kind, subdiv_levels=0, material_type='NONE')


parts = {'Skin': body,
         'ShirtDenim': load_part('clothes', 'male_casualsuit03', 'Clothes'),
         'Shoes': load_part('clothes', 'shoes01', 'Clothes'),
         'Hair': load_part('hair', 'short02', 'Hair'),
         'Eyes': load_part('eyes', 'high-poly', 'Eyes'),
         'Brows': load_part('eyebrows', 'eyebrow002', 'Eyebrows'),
         'Lashes': load_part('eyelashes', 'eyelashes01', 'Eyelashes')}
textures = {
    'Skin': ('skins/middleage_caucasian_male/middleage_lightskinned_male_diffuse.png', None, 0.65),
    'ShirtDenim': ('clothes/male_casualsuit03/male_casualsuit03_diffuse.png', 'clothes/male_casualsuit03/male_casualsuit03_normal.png', 0.82),
    'Shoes': ('clothes/shoes01/shoes01_diffuse.png', None, 0.6),
    'Hair': ('hair/short02/short02_diffuse.png', None, 0.6),
    'Eyes': ('eyes/materials/brown_eye.png', None, 0.18),
    'Brows': ('eyebrows/eyebrow002/eyebrow002.png', None, 0.85),
    'Lashes': ('eyelashes/eyelashes01/eyelashes01.png', None, 0.85),
}
texture_sources = []


def texture(relative):
    source = tools / 'core' / relative
    destination = OUTPUT / 'Textures' / source.name
    destination.parent.mkdir(exist_ok=True)
    shutil.copyfile(source, destination)
    image = bpy.data.images.load(str(destination), check_existing=True)
    if max(image.size) > 2048:
        ratio = 2048 / max(image.size)
        image.scale(round(image.size[0] * ratio), round(image.size[1] * ratio))
        image.save()
    texture_sources.append(dict(path='Textures/' + destination.name, archivePath=relative,
                               upstreamSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                               sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    return image


for name, obj in parts.items():
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    diffuse, normal, roughness = textures[name]
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = texture(diffuse)
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = roughness
    if name in ('Hair', 'Brows', 'Lashes', 'Eyes'):
        mat.node_tree.links.new(tex.outputs['Alpha'], shader.inputs['Alpha'])
        mat.surface_render_method = 'DITHERED'
    if name == 'Skin':
        # Match the Unreal skin calibration under the apartment's bright sun.
        gain = mat.node_tree.nodes.new('ShaderNodeMixRGB')
        gain.blend_type = 'MULTIPLY'
        gain.inputs[0].default_value = 1
        gain.inputs[2].default_value = (0.72, 0.72, 0.72, 1)
        mat.node_tree.links.new(tex.outputs['Color'], gain.inputs[1])
        mat.node_tree.links.new(gain.outputs['Color'], shader.inputs['Base Color'])
        shader.inputs['Specular IOR Level'].default_value = 0.25
    if normal:
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = texture(normal)
        node.image.colorspace_settings.name = 'Non-Color'
        bump = mat.node_tree.nodes.new('ShaderNodeNormalMap')
        mat.node_tree.links.new(node.outputs['Color'], bump.inputs['Color'])
        mat.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# Retain the macro prescription in the editable source. Bake its evaluated mesh
# for FBX, remove helpers and covered body faces using MakeHuman's masks, and
# subdivide once for a smooth close-view silhouette. Skin weights interpolate.
TargetService.bake_targets(body)
for obj in parts.values():
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers):
        if modifier.type == 'MASK':
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    if obj == body:
        modifier = obj.modifiers.new('Close-view surface', 'SUBSURF')
        modifier.levels = 1
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    for face in obj.data.polygons:
        face.use_smooth = True

scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, 241
rig.animation_data_create()
relaxed_arms = {}
for side, sign in (('L', 1), ('R', -1)):
    bone = rig.data.bones['upperarm01.' + side]
    direction = bone.matrix_local.to_3x3().inverted() @ Vector((sign * 0.14, -0.03, -1))
    relaxed_arms[side] = Vector((0, 1, 0)).rotation_difference(direction.normalized()).to_euler('XYZ')


def pose(bone, degrees):
    item = rig.pose.bones[bone]
    item.rotation_mode = 'XYZ'
    item.rotation_euler = tuple(math.radians(v) for v in degrees)


def animate(name, talking=False):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data.action = action
    for frame in range(1, 242):
        t = (frame - 1) / 30
        breath = math.sin(t * math.tau / 4)
        shift = math.sin(t * math.tau / 8)
        gesture = math.sin(math.pi * min(1, max(0, (t - 1) / 3))) ** 2 if talking else 0
        for bone in rig.pose.bones:
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = (0, 0, 0)
        # Relax MPFB's A-pose, keep feet planted, breathe through upper spine.
        for side, sign in (('L', 1), ('R', -1)):
            rig.pose.bones['upperarm01.' + side].rotation_euler = relaxed_arms[side]
            pose('lowerarm01.' + side, (6, 0, 0))
            for finger in range(2, 6):
                for joint in range(1, 4):
                    pose(f'finger{finger}-{joint}.{side}', (0, 0, sign * 12))
        pose('spine02', (0.6 * breath, 0, 0.45 * shift))
        pose('neck01', (0.35 * breath + 1.2 * gesture, 0.5 * shift, 0))
        pose('head', (0.4 * breath + 1.5 * gesture, 0.7 * shift, 0))
        if talking:
            upper = rig.pose.bones['upperarm01.R']
            upper.rotation_euler.x += math.radians(-8 * gesture)
            upper.rotation_euler.z += math.radians(8 * gesture)
            pose('lowerarm01.R', (6 + 38 * gesture, -10 * gesture, 0))
            pose('wrist.R', (0, 12 * gesture, 3 * gesture))
        # Two short eyelid closures per eight-second loop; no mouth animation.
        blink = max(max(0, 1 - abs(t - centre) / 0.12) for centre in (2.1, 5.7))
        for side in ('L', 'R'):
            pose('orbicularis03.' + side, (-22 * blink, 0, 0))
            pose('orbicularis04.' + side, (8 * blink, 0, 0))
        for bone in rig.pose.bones:
            bone.keyframe_insert('rotation_euler', frame=frame, group=bone.name)
    return action


idle = animate('A_Idle')
talk = animate('A_Talk', True)
rig.animation_data.action = idle
scene.frame_set(1)
rig['fpsOne_macro_recipe'] = json.dumps(macro, sort_keys=True)
rig['fpsOne_license'] = 'CC0-1.0; MakeHuman core geometry and original fpsOne animation'
bpy.context.preferences.filepaths.save_version = 0
for image in bpy.data.images:
    if image.filepath:
        image.filepath = '//Textures/' + Path(image.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / 'NPC_A.blend'))
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for obj in parts.values():
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
export = dict(use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
              axis_forward='-Y', axis_up='Z', mesh_smooth_type='FACE', use_mesh_modifiers=True,
              bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
              bake_anim_simplify_factor=0.0, path_mode='STRIP')
bpy.ops.export_scene.fbx(filepath=str(OUTPUT / 'SK_NPC_A.fbx'), bake_anim=False, **export)
for obj in parts.values():
    obj.select_set(False)
for action in (idle, talk):
    rig.animation_data.action = action
    bpy.ops.export_scene.fbx(filepath=str(OUTPUT / (action.name + '.fbx')), bake_anim=True, **export)
(OUTPUT / 'recipe.json').write_text(json.dumps(dict(macro=macro, textures=texture_sources,
    rig='MPFB default', parts={name: str(obj.name) for name, obj in parts.items()},
    animations=['A_Idle', 'A_Talk'], author='fpsOne contributors', license='CC0-1.0'), indent=2) + '\n')
print('T06_CHARACTER_EXPORT_PASSED')
