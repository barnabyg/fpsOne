"""Export an editable resident; original pose/animation contributions are CC0-1.0.

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
sys.path.insert(0, str(ROOT / 'scripts'))
from character_recipes import resident_recipe

parser = argparse.ArgumentParser()
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--resident', choices=('A', 'B'), required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
resident = args.resident
recipe = resident_recipe(resident)
OUTPUT = ROOT / 'SourceArt/Characters' / ('NPC_' + resident)
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
macro.update(recipe['macro'])
body = HumanService.create_human(macro_detail_dict=macro)
body.name = 'Resident' + resident
rig = HumanService.add_builtin_rig(body, 'default')
# Unreal's legacy FBX importer strips nodes literally named Armature. Retain
# this explicit root so the metre-to-centimetre transform also survives in clips.
rig.name = 'Resident' + resident + 'Rig'


def load_part(folder, name, kind):
    return HumanService.add_mhclo_asset(str(tools / 'core' / folder / name / (name + '.mhclo')),
                                       body, asset_type=kind, subdiv_levels=0, material_type='NONE')


parts = {'Skin': body, **{name: load_part(*part) for name, part in recipe['parts'].items()}}
textures = recipe['textures']
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
    tint = recipe.get('materialTints', {}).get(name)
    if tint:
        # Retain authored folds/stripes while giving B a distinct sage palette.
        luminance = mat.node_tree.nodes.new('ShaderNodeRGBToBW')
        gain = mat.node_tree.nodes.new('ShaderNodeMixRGB')
        gain.blend_type = 'MULTIPLY'
        gain.inputs[0].default_value = 1
        gain.inputs[2].default_value = (*tint, 1)
        mat.node_tree.links.new(tex.outputs['Color'], luminance.inputs['Color'])
        mat.node_tree.links.new(luminance.outputs['Val'], gain.inputs[1])
        mat.node_tree.links.new(gain.outputs['Color'], shader.inputs['Base Color'])
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
duration = recipe['animationDuration']
scene.frame_start, scene.frame_end = 1, int(duration * scene.render.fps) + 1
rig.animation_data_create()
relaxed_arms = {}
for side, sign in (('L', 1), ('R', -1)):
    bone = rig.data.bones['upperarm01.' + side]
    direction = bone.matrix_local.to_3x3().inverted() @ Vector((sign * 0.10, -0.03, -1))
    relaxed_arms[side] = Vector((0, 1, 0)).rotation_difference(direction.normalized()).to_euler('XYZ')


def pose(bone, degrees):
    item = rig.pose.bones[bone]
    item.rotation_mode = 'XYZ'
    item.rotation_euler = tuple(math.radians(v) for v in degrees)


def add_pose(bone, degrees, amount=1.0):
    item = rig.pose.bones[bone]
    item.rotation_mode = 'XYZ'
    for axis, value in enumerate(degrees):
        item.rotation_euler[axis] += math.radians(value * amount)


def pulse(time, start, peak, end):
    if time <= start or time >= end:
        return 0.0
    if time <= peak:
        phase = (time - start) / (peak - start)
    else:
        phase = (end - time) / (end - peak)
    return math.sin(math.pi * 0.5 * phase) ** 2


def animate(name, talking=False):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data.action = action
    for frame in range(scene.frame_start, scene.frame_end + 1):
        t = (frame - scene.frame_start) / scene.render.fps
        phase = t / duration
        primary, secondary = recipe['breathCycles']
        breath = (math.sin(math.tau * primary * phase) +
                  0.22 * math.sin(math.tau * secondary * phase + 0.35))
        shift_cycles = recipe['weightShift']['cycles']
        shift_phases = recipe['weightShift']['phases']
        shift = (math.sin(math.tau * shift_cycles[0] * phase + shift_phases[0]) +
                 0.28 * math.sin(math.tau * shift_cycles[1] * phase + shift_phases[1]))
        for bone in rig.pose.bones:
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = (0, 0, 0)
        # Relax MPFB's A-pose. The pelvis and legs remain untouched so the feet
        # stay planted; small opposing spine rotations imply weight transfer.
        for side, sign in (('L', 1), ('R', -1)):
            rig.pose.bones['upperarm01.' + side].rotation_euler = relaxed_arms[side]
            pose('lowerarm01.' + side, (recipe['restElbows'][side], 0, 0))
            pose('wrist.' + side, (0, 0, sign * (0.7 if side == recipe['gestureSide'] else 0.2)))
            for finger in range(1, 6):
                for joint in range(1, 4):
                    curve = (7, 13, 10)[joint - 1] + (finger - 3) * 0.6
                    splay = sign * (finger - 3) * 0.35 if joint == 1 else 0
                    pose(f'finger{finger}-{joint}.{side}', (curve, 0, splay))
        lean = recipe['restLean']
        pose('spine01', (0.18 * shift, 0, -0.25 * shift))
        pose('spine02', (lean[0] + 0.55 * breath, lean[1] + 0.14 * shift,
                         lean[2] + 0.42 * shift))
        pose('spine03', (0.28 * breath, -0.08 * shift, -0.18 * shift))
        pose('neck01', (0.18 * breath, 0.22 * shift, 0))
        pose('head', (0.20 * breath, 0.28 * shift, 0))
        for glance in recipe['glances']:
            amount = pulse(t, glance['start'], glance['peak'], glance['end'])
            add_pose('neck01', (glance['pitch'] * 0.35, glance['yaw'] * 0.35, 0), amount)
            add_pose('head', (glance['pitch'], glance['yaw'], 0), amount)
        for adjustment in recipe['handAdjustments']:
            amount = pulse(t, adjustment['start'], adjustment['peak'], adjustment['end'])
            side = adjustment['side']
            add_pose('wrist.' + side, adjustment['wrist'], amount)
            for finger in range(2, 6):
                for joint in range(1, 4):
                    add_pose(f'finger{finger}-{joint}.{side}',
                             (adjustment['curl'], 0, 0), amount)
        if talking:
            for gesture in recipe['talkGestures']:
                amount = pulse(t, gesture['start'], gesture['peak'], gesture['end'])
                side = gesture['side']
                add_pose('upperarm01.' + side, gesture['upper'], amount)
                add_pose('lowerarm01.' + side, gesture['lower'], amount)
                add_pose('wrist.' + side, gesture['wrist'], amount)
                add_pose('head', gesture['head'], amount)
                for finger in range(2, 6):
                    for joint in range(1, 4):
                        add_pose(f'finger{finger}-{joint}.{side}',
                                 (gesture['curl'], 0, 0), amount)
        # Irregular short closures across the long loop; no mouth animation.
        blink = max(max(0, 1 - abs(t - centre) / 0.12) for centre in recipe['blinkTimes'])
        for side in ('L', 'R'):
            pose('orbicularis03.' + side, (-22 * blink, 0, 0))
            pose('orbicularis04.' + side, (8 * blink, 0, 0))
        for bone in rig.pose.bones:
            bone.keyframe_insert('rotation_euler', frame=frame, group=bone.name)
    return action


idle = animate(resident + '_Idle')
talk = animate(resident + '_Talk', True)
rig.animation_data.action = idle
scene.frame_set(1)
rig['fpsOne_macro_recipe'] = json.dumps(macro, sort_keys=True)
rig['fpsOne_license'] = 'CC0-1.0; MakeHuman core geometry and original fpsOne animation'
bpy.context.preferences.filepaths.save_version = 0
for image in bpy.data.images:
    if image.filepath:
        image.filepath = '//Textures/' + Path(image.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / ('NPC_' + resident + '.blend')))
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for obj in parts.values():
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
export = dict(use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
              axis_forward='-Y', axis_up='Z', mesh_smooth_type='FACE', use_mesh_modifiers=True,
              bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
              bake_anim_simplify_factor=0.0, path_mode='STRIP')
bpy.ops.export_scene.fbx(filepath=str(OUTPUT / ('SK_NPC_' + resident + '.fbx')), bake_anim=False, **export)
for obj in parts.values():
    obj.select_set(False)
for action in (idle, talk):
    rig.animation_data.action = action
    bpy.ops.export_scene.fbx(filepath=str(OUTPUT / (action.name + '.fbx')), bake_anim=True, **export)
(OUTPUT / 'recipe.json').write_text(json.dumps(dict(macro=macro, textures=texture_sources,
    rig='MPFB default', parts={name: str(obj.name) for name, obj in parts.items()},
    materialTints=recipe.get('materialTints', {}), animations=[idle.name, talk.name],
    animation=dict(durationSeconds=duration, fps=scene.render.fps,
                   restElbows=recipe['restElbows'], restLean=recipe['restLean'],
                   breathCycles=recipe['breathCycles'], weightShift=recipe['weightShift'],
                   blinkTimes=recipe['blinkTimes'],
                   glances=recipe['glances'], handAdjustments=recipe['handAdjustments'],
                   talkGestures=recipe['talkGestures']),
    author='fpsOne contributors', license='CC0-1.0'), indent=2) + '\n')
print('CHARACTER_EXPORT_PASSED NPC_' + resident)
