import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

# create empty
e = bpy.data.objects.new("Empty", None)
bpy.context.scene.collection.objects.link(e)
e.location = (0, 0, 1)
e.keyframe_insert(data_path="location", frame=1)
e.location = (1, 1, 1)
e.keyframe_insert(data_path="location", frame=10)

# create arm
arm = bpy.data.armatures.new("Arm")
obj = bpy.data.objects.new("Arm", arm)
bpy.context.scene.collection.objects.link(obj)

bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode="EDIT")
bone = arm.edit_bones.new("Bone")
bone.head = (0,0,0)
bone.tail = (0,0,1)
bpy.ops.object.mode_set(mode="POSE")

pb = obj.pose.bones["Bone"]
c = pb.constraints.new("TRACK_TO")
c.target = e

# select bones
bpy.ops.pose.select_all(action='SELECT')

bpy.ops.nla.bake(frame_start=1, frame_end=10, only_selected=True, visual_keying=True, clear_constraints=True, bake_types={'POSE'})

print("Constraints after bake:", len(pb.constraints))
print("Keyframes on bone:", len(obj.animation_data.action.fcurves))
