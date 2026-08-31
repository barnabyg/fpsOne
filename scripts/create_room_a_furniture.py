"""Project-authored editable Room A meshes. Run with Blender 4.5.3 --background.

Units are metres; glTF exports retain material slots for Unreal's PBR materials.
The source is this deterministic script, not a redundant Blender cache/archive.
"""

import math
from pathlib import Path

import bpy


OUTPUT = Path(__file__).resolve().parents[1] / "SourceArt" / "Authored"
OUTPUT.mkdir(parents=True, exist_ok=True)


def material(name, color):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    return result


FABRIC = material("Linen", (0.48, 0.44, 0.36))
PIPING = material("Piping", (0.25, 0.23, 0.19))
WOOD = material("Oak", (0.24, 0.12, 0.045))
METAL = material("Bronze", (0.055, 0.045, 0.033))
SHADE = material("Shade", (0.85, 0.76, 0.58))
RUG = material("Rug", (0.23, 0.28, 0.26))


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def box(name, location, size, mat, bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Soft manufactured edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 6
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    modifier = obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    modifier.keep_sharp = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    # Cube projection with a physical one-metre repeat preserves fabric scale.
    for polygon in obj.data.polygons:
        axis = max(range(3), key=lambda index: abs(polygon.normal[index]))
        axes = [index for index in range(3) if index != axis]
        for loop_index in polygon.loop_indices:
            vertex = obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            obj.data.uv_layers.active.data[loop_index].uv = (vertex[axes[0]], vertex[axes[1]])
    return obj


def cylinder(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Edge highlight", "BEVEL")
    bevel.width = 0.003
    bevel.segments = 3
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def export(name):
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    bpy.context.object.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT / (name + ".glb")), export_format="GLB",
                              use_selection=True, export_cameras=False, export_lights=False)


def sofa():
    clear()
    for x in (-1.01, 1.01):
        for y in (-0.33, 0.33):
            box("Recessed foot", (x, y, 0.085), (0.06, 0.06, 0.17), METAL, 0.007)
    box("Upholstered plinth", (0, 0, 0.26), (2.36, 0.89, 0.24), FABRIC, 0.065)
    box("Back", (0, 0.365, 0.63), (2.34, 0.22, 0.65), FABRIC, 0.075)
    for x in (-1.085, 1.085):
        box("Arm", (x, -0.01, 0.48), (0.23, 0.91, 0.49), FABRIC, 0.073)
    for x in (-0.49, 0.49):
        box("Seat piping", (x, -0.07, 0.407), (0.968, 0.682, 0.012), PIPING, 0.005)
        box("Seat cushion", (x, -0.07, 0.437), (0.96, 0.68, 0.16), FABRIC, 0.073)
        cushion = box("Back cushion", (x, 0.235, 0.725), (0.975, 0.205, 0.45), FABRIC, 0.087)
        cushion.rotation_euler.x = math.radians(8)
    for x, angle in ((-0.81, -13), (0.79, 18)):
        cushion = box("Loose cushion", (x, 0.02, 0.66), (0.34, 0.14, 0.35), RUG, 0.064)
        cushion.rotation_euler = (math.radians(15), math.radians(angle), 0)
    export("SM_LinenSofa")


def sideboard():
    clear()
    for x in (-0.64, 0.64):
        for y in (-0.13, 0.13):
            box("Foot", (x, y, 0.09), (0.045, 0.045, 0.18), METAL, 0.005)
    box("Cabinet", (0, 0, 0.405), (1.6, 0.39, 0.47), WOOD, 0.008)
    for x in (-0.532, 0, 0.532):
        box("Door", (x, -0.207, 0.405), (0.524, 0.025, 0.45), WOOD, 0.004)
        box("Handle", (x + 0.2, -0.23, 0.46), (0.012, 0.025, 0.1), METAL, 0.004)
    box("Top", (0, 0, 0.66), (1.64, 0.43, 0.035), WOOD, 0.007)
    export("SM_Sideboard")


def floor_lamp():
    clear()
    cylinder("Base", (0, 0, 0.018), 0.17, 0.036, METAL)
    cylinder("Stem", (0, 0, 0.73), 0.012, 1.42, METAL)
    # Open truncated-cone shade: light is visible inside, with a physical rim.
    vertices, faces = [], []
    for z, radius in ((1.39, 0.245), (1.75, 0.17), (1.75, 0.166), (1.39, 0.241)):
        vertices.extend((radius * math.cos(i * math.tau / 96), radius * math.sin(i * math.tau / 96), z) for i in range(96))
    for ring in range(4):
        for i in range(96):
            faces.append((ring * 96 + i, ring * 96 + (i + 1) % 96,
                          ((ring + 1) % 4) * 96 + (i + 1) % 96, ((ring + 1) % 4) * 96 + i))
    mesh = bpy.data.meshes.new("Shade")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new("Woven lampshade", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(SHADE)
    export("SM_FloorLamp")


def rug():
    clear()
    box("Bound edge", (0, 0, 0.008), (2.8, 2.2, 0.016), PIPING, 0.006)
    box("Woven field", (0, 0, 0.016), (2.76, 2.16, 0.012), RUG, 0.005)
    export("SM_Rug")


if __name__ == "__main__":
    sofa()
    sideboard()
    floor_lamp()
    rug()
    print("ROOM_A_AUTHORED_MESHES_CREATED")
