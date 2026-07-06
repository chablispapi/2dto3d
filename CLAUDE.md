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

    video → MediaPipe (x,y,z per joint per frame) → JSON → Blender armature keyframes

## Pipeline (one script, one command)

Everything lives in **`dance_to_3d.py`** and runs with a single command:

    .venv/bin/python dance_to_3d.py [video ...]

With no arguments it processes every video in `dances/`; each `<name>.<ext>` becomes
`blend-files/<name>.blend`. Open a result in Blender and press play. Every build also
writes a `blend-files/<name>.preview.png` contact sheet (see Self-verification below).

The file has two halves that run in different interpreters — this is why it can't just
be a linear script:

1. **extract half** (venv, `extract()`): OpenCV reads frames, MediaPipe Pose estimates
   per-frame world landmarks, they're cleaned (smooth → rigidify → ground-anchor) and
   written to a temporary JSON (fps + frames of 33 × [x,y,z,visibility] + per-frame
   timestamps).
2. **build half** (Blender, `build_blend()`): builds a stick-figure armature over the
   POSE_CONNECTIONS topology, keyframes it, bakes the constraints into bone motion, and
   saves the `.blend`.

The venv half re-invokes Blender on this same file as a subprocess
(`blender --background --python dance_to_3d.py -- <json> <blend>`), so you only run the
one command. `import bpy` succeeds only inside Blender, which is how the file knows which
half to run; the temp JSON is deleted afterward.

## Self-verification (look at the output without opening Blender)

Every build ends with a preview so the result can be eyeballed — and iterated on —
without a human opening Blender:

    .venv/bin/python dance_to_3d.py --verify dances/<name>.<ext>   # redraw preview only, no rebuild

`verify()` (venv) re-invokes Blender (`-- --dump <blend> <json>`) to run `dump_bones()`,
which opens the built `.blend` and writes each bone's **world** head/tail at 8 sample
frames. Back in the venv, matplotlib draws a contact sheet — source video frame beside
the reconstructed 3D skeleton at the matching timestamp — to `blend-files/<name>.preview.png`.
Read that PNG to check the pose and, critically, the coordinate conversion: a wrong axis
shows up immediately as a dancer lying down or mirrored.

Why not render the `.blend` directly: an armature has no mesh, so a normal (F12) render
shows nothing, and `bpy.ops.render.opengl` fails headless ("no opengl context"). Reading
the baked bone matrices out and plotting them is the way to see bones from `--background`.
Not MCP: `blender-mcp` needs a live Blender + addon + socket, which can't verify a
headless batch that builds and exits. Known wart: the last sample frame can overshoot the
video's end, leaving one blank video panel — cosmetic.

## Technical notes

- Use MediaPipe's **`pose_world_landmarks`** (metric meters, origin at hip center),
  NOT `pose_landmarks` (normalized image coordinates).
- **Coordinate systems differ**: MediaPipe is x-right, y-down, z-toward-camera;
  Blender is Z-up, Y-forward. Convert on import: `blender(x, y, z) = (mp_x, mp_z, -mp_y)`
  (verify visually — a wrong axis shows up as a dancer lying down or mirrored).
- Read the video's FPS with OpenCV, store it in the JSON, and set Blender's scene FPS
  from it so playback speed matches the video.
- **Blender ships its own Python** — the build half (`build_blend()` + `mp_to_blender()`)
  may only use stdlib (`json`, `math`) plus `bpy`. Keep the `cv2`/`mediapipe` imports
  inside `extract()` so the file stays importable under Blender (that's what lets it
  re-invoke itself).
- Landmark jitter is cleaned in the extract half after detection, in two passes:
  1. **One Euro filter** (`smooth_frames`) — a velocity-adaptive low-pass per landmark
     axis: heavy smoothing when a joint is slow (kills jitter), light when fast (no lag
     on quick dance moves). Knobs `mincutoff`/`beta` are exposed for taste-tuning; a
     plain moving average was tried first but can't beat the lag-vs-jitter tradeoff.
  2. **Bone-length rigidify** (`rigidify`) — MediaPipe's world landmarks let limbs
     stretch 3-5× frame to frame, which is the main thing that reads as non-human.
     Rebuild each frame over a spanning tree of the skeleton (rooted at a hip): keep each
     joint's observed direction from its parent but pin the bone to its median length.
     Face landmarks (0-10, disconnected from the body graph) pass through unchanged.
- **Feet are planted on the ground** (`ground_anchor`, the last pass) so hip movement
  shows. MediaPipe world landmarks are hip-centered — the hips sit at the origin every
  frame — so a dancer shifting weight over planted feet comes out INVERTED: hips look
  frozen while the feet slide. `ground_anchor` recovers true hip translation by
  integrating the support (lowest) foot's frame-to-frame motion, so the planted foot
  stays put and the hips move over it. To avoid drifting across the room it then subtracts
  a heavily smoothed (10-second window) copy of that translation — a high-pass that keeps
  the fast dance sways but removes only very slow global travel — and centers the median
  foot at the origin. This replaced an earlier monocular hip-screen-translation hack that
  only recovered ~9 cm and was jittery. Trade-off: global floor travel (dancer walking
  across the room) is intentionally dropped — right for an in-place dance.
- **VFR video warning**: this footage is variable-frame-rate (phone/TikTok). OpenCV
  reports an inconsistent frame count and FPS run-to-run; cross-check against
  `ffprobe`'s `avg_frame_rate`/`duration` (here 41.43 fps, 14.70 s) if playback speed
  looks off.
- `CONNECTIONS` (the POSE_CONNECTIONS topology) is now a single module-level constant —
  merging the two scripts into one file removed the copy that used to live in each.
- Video keyframes use the real per-frame timestamps (`cv2.CAP_PROP_POS_MSEC`), stored in
  the JSON, so VFR footage stays in sync; the armature is baked (`nla.bake`) and the
  driver empties deleted, leaving a self-contained keyframed armature in the `.blend`.

## Environment

- Python venv in the project root with `mediapipe` and `opencv-python`.
- Blender installed separately. The script calls it at `/Applications/Blender.app/
  Contents/MacOS/Blender`; override with the `BLENDER` env var if it lives elsewhere.
- Inputs live in `dances/`, outputs in `blend-files/`.

## Non-goals

- No custom depth solver (MediaPipe's learned z is the whole point).
- No body mesh, skinning, or retargeting to rigs like Rigify.
- No realtime processing; offline batch is fine.
- Keep it to the single `dance_to_3d.py`; don't split the pipeline back into two scripts.
