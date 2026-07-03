"""Build a keyframed stick-figure armature from pose_data.json.

Usage: /Applications/Blender.app/Contents/MacOS/Blender --background --python import_pose.py
Writes dance.blend next to this script. Uses only stdlib + bpy (see CLAUDE.md).
"""
import json
from pathlib import Path

import bpy

# MediaPipe POSE_CONNECTIONS (33-landmark topology), hardcoded — no mediapipe in Blender
CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
]

HERE = Path(__file__).parent


def mp_to_blender(x, y, z):
    # MediaPipe: x right, y down, z toward camera -> Blender: Z up (see CLAUDE.md)
    return x, z, -y


def main():
    with open(HERE / "pose_data.json") as f:
        data = json.load(f)
    frames = data["frames"]
    timestamps = data.get("timestamps")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = round(data["fps"])
    scene.render.fps_base = scene.render.fps / data["fps"]  # exact playback speed

    # one empty per landmark, keyframed with the raw motion
    empties = []
    for i in range(33):
        e = bpy.data.objects.new(f"lm.{i:02d}", None)
        e.empty_display_size = 0.02
        scene.collection.objects.link(e)
        empties.append(e)
        
    max_frame = len(frames)
    for i, lms in enumerate(frames):
        if lms is None:
            continue  # no detection: hold interpolation between neighbors
            
        if timestamps:
            f = round(timestamps[i] * data["fps"] / 1000.0) + 1
            max_frame = max(max_frame, f)
        else:
            f = i + 1
            
        for e, (x, y, z, _vis) in zip(empties, lms):
            e.location = mp_to_blender(x, y, z)
            e.keyframe_insert("location", frame=f)
            
    scene.frame_start, scene.frame_end = 1, max_frame

    # armature: one bone per connection, pinned between its two empties
    arm = bpy.data.armatures.new("dancer")
    arm.display_type = "STICK"
    obj = bpy.data.objects.new("dancer", arm)
    scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    for a, b in CONNECTIONS:
        bone = arm.edit_bones.new(f"{a:02d}-{b:02d}")
        bone.head = (0, 0, 0.0)  # rest pose irrelevant; constraints drive everything
        bone.tail = (0, 0, 0.1)
    bpy.ops.object.mode_set(mode="POSE")
    for a, b in CONNECTIONS:
        pb = obj.pose.bones[f"{a:02d}-{b:02d}"]
        c = pb.constraints.new("COPY_LOCATION")
        c.target = empties[a]
        s = pb.constraints.new("STRETCH_TO")
        s.target = empties[b]
    bpy.ops.object.mode_set(mode="OBJECT")

    # Bake constraints into keyframed bone rotations and delete empties
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(
        frame_start=1,
        frame_end=max_frame,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )
    
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    for e in empties:
        e.select_set(True)
    bpy.ops.object.delete()
    
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "dance.blend"))
    print(f"saved dance.blend: {max_frame} frames @ {data['fps']:.2f} fps")


main()
