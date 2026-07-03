# 2dto3d — dance video to 3D Blender animation

## Goal

Turn `dance.MP4` (a 2D video of a person dancing, shot with a single camera) into an
animated 3D skeleton/armature in Blender that performs the same dance. No mesh, no
skinning — a keyframed stick figure is the deliverable. A mesh can be parented to the
armature later if ever wanted.

## The core idea

Perspective projection maps a 3D point to the screen with x' = x/z, y' = y/z. The video
only gives us (x', y') — depth z is lost, and no algebra can recover it from a single
view. What *can* recover it is prior knowledge of the human body: bone lengths are fixed,
joints have limited ranges, people don't fold impossibly.

Instead of hand-writing that depth model, we use **MediaPipe Pose**, a pretrained
monocular 3D pose estimator that has learned exactly those priors. Per video frame it
outputs 33 body landmarks with metric (x, y, z) coordinates. So the pipeline is:

    dance.MP4 → MediaPipe (x,y,z per joint per frame) → JSON → Blender armature keyframes

## Pipeline (2 scripts, keep it that way)

1. `extract_pose.py` — runs in the project venv. OpenCV reads frames from `dance.MP4`,
   MediaPipe Pose estimates per-frame landmarks, writes `pose_data.json`:
   video fps + a list of frames, each with 33 × [x, y, z, visibility].
2. `import_pose.py` — runs inside Blender: `blender --python import_pose.py`.
   Reads `pose_data.json`, builds a stick-figure armature (bones following MediaPipe's
   POSE_CONNECTIONS topology), inserts keyframes for every frame.
3. Open the result in Blender and press play.

## Technical notes

- Use MediaPipe's **`pose_world_landmarks`** (metric meters, origin at hip center),
  NOT `pose_landmarks` (normalized image coordinates).
- **Coordinate systems differ**: MediaPipe is x-right, y-down, z-toward-camera;
  Blender is Z-up, Y-forward. Convert on import: `blender(x, y, z) = (mp_x, mp_z, -mp_y)`
  (verify visually — a wrong axis shows up as a dancer lying down or mirrored).
- Read the video's FPS with OpenCV, store it in the JSON, and set Blender's scene FPS
  from it so playback speed matches the video.
- **Blender ships its own Python** — `import_pose.py` may only use stdlib (`json`,
  `math`) plus `bpy`/`mathutils`. Never import mediapipe/cv2/numpy there.
- Landmark jitter between frames is normal. Don't smooth preemptively; if playback looks
  noisy, add a simple moving average over each landmark's time series in
  `extract_pose.py`.
- World landmarks are hip-centered, so global position (the dancer moving across the
  floor) is lost. Acceptable for v1; if needed later, take root translation from the
  normalized hip landmark.

## Environment

- Python venv in the project root with `mediapipe` and `opencv-python`.
- Blender installed separately (invoke as `blender` from the CLI, or full app path).

## Non-goals

- No custom depth solver (MediaPipe's learned z is the whole point).
- No body mesh, skinning, or retargeting to rigs like Rigify.
- No realtime processing; offline batch is fine.
- No more than the 2 scripts above.
