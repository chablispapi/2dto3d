"""Dance video -> animated 3D Blender armature, in one command.

    .venv/bin/python dance_to_3d.py [video ...]

With no arguments, every video in dances/ is processed; each <name>.<ext> becomes
blend-files/<name>.blend. MediaPipe runs in the venv, then this file re-invokes
Blender on ITSELF to build the armature — so you only ever run the one command.

Why one file with two halves: MediaPipe/OpenCV live in the project venv, `bpy` only
exists inside Blender's bundled Python. The two can't share an interpreter, so the
mediapipe/cv2 imports stay inside extract() and the file is safe to import under either.
See CLAUDE.md for the pipeline and coordinate/smoothing notes.
"""
import json
import math
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DANCES = ROOT / "dances"
BLENDS = ROOT / "blend-files"
MODEL = ROOT / "pose_landmarker_full.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_full/float16/latest/pose_landmarker_full.task")
BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
# Yaw the finished figure so motion toward the camera (MediaPipe z -> Blender Y, depth)
# reads from the default front view instead of hiding along the view axis. The dance's
# biggest move — the hip thrust — is encoded as the spine leaning in depth (~30 cm here,
# vs ~18 cm lateral), invisible head-on; 45deg turns it into a visible diagonal lean.
# Presentation only, physics untouched. 0 = front-facing, 90 = full side profile.
PRESENT_YAW_DEG = 45

# MediaPipe POSE_CONNECTIONS (33-landmark topology). Single source of truth now that
# extract and import live in one file.
CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
]


# ─────────────────────────── landmark cleanup (venv side) ───────────────────────────

def _one_euro(series, visibilities, fps, mincutoff, beta, dcutoff=1.0):
    """One Euro filter over one axis of one landmark. None = dropped frame -> reset."""
    def alpha(cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau * fps)

    out, x_prev, dx_prev = [], None, 0.0
    for x, vis in zip(series, visibilities):
        if x is None:
            out.append(None)
            x_prev = None
            continue
        if x_prev is None:
            out.append(x)
            x_prev, dx_prev = x, 0.0
            continue
        dx = (x - x_prev) * fps
        a_d = alpha(dcutoff)
        dx_hat = a_d * dx + (1 - a_d) * dx_prev
        
        # Scale beta by visibility. If visibility is low (e.g. arm behind back during spin),
        # beta approaches 0, creating a heavy low-pass filter that prevents instant teleporting glitches.
        current_beta = beta * (vis if vis is not None else 1.0)
        
        a = alpha(mincutoff + current_beta * abs(dx_hat))  # faster motion -> higher cutoff -> less lag
        x_hat = a * x + (1 - a) * x_prev
        out.append(x_hat)
        x_prev, dx_prev = x_hat, dx_hat
    return out


def smooth_frames(frames, fps, mincutoff=1.5, beta=0.4):
    """Velocity-adaptive One Euro low-pass per landmark axis: heavy smoothing when a
    joint moves slowly (kills jitter), light when fast (no lag on quick dance moves),
    escaping the fixed lag-vs-jitter tradeoff of a moving average. Visibility carried
    through unfiltered. Knobs: lower mincutoff = smoother; higher beta = less lag."""
    if not frames: return frames
    out = [None if f is None else [[0.0, 0.0, 0.0, f[lm][3]] for lm in range(33)] for f in frames]
    for lm in range(33):
        visibilities = [None if f is None else f[lm][3] for f in frames]
        for c in range(3):
            series = [None if f is None else f[lm][c] for f in frames]
            sm = _one_euro(series, visibilities, fps, mincutoff, beta)
            for i, v in enumerate(sm):
                if out[i] is not None:
                    out[i][lm][c] = v
    return out


def rigidify(frames):
    """Enforce constant bone lengths. MediaPipe's world landmarks let limbs stretch
    3-5x frame to frame (forearm CV ~18%), which is the main thing that reads as
    non-human. Rebuild each frame over a spanning tree of the skeleton (rooted at a
    hip): keep each joint's observed DIRECTION from its parent, but pin the bone to
    its median length across the whole clip. Face landmarks (0-10, disconnected from
    the body graph) are passed through unchanged."""
    from collections import defaultdict, deque

    adj = defaultdict(list)
    for a, b in CONNECTIONS:
        adj[a].append(b)
        adj[b].append(a)
    root = 23  # left hip; BFS reaches every body landmark 11-32
    parent, order, dq = {root: None}, [root], deque([root])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v not in parent:
                parent[v] = u
                order.append(v)
                dq.append(v)

    def dist(f, a, b):
        return sum((f[a][c] - f[b][c]) ** 2 for c in range(3)) ** 0.5

    canon = {}  # child -> median bone length
    for v in order:
        if parent[v] is None:
            continue
        lens = [dist(f, parent[v], v) for f in frames if f is not None]
        canon[v] = statistics.median(lens) if lens else 0.0

    out = []
    for f in frames:
        if f is None:
            out.append(None)
            continue
        pos = {root: f[root][:3]}
        for v in order:
            u = parent[v]
            if u is None:
                continue
            d = [f[v][c] - f[u][c] for c in range(3)]
            n = sum(x * x for x in d) ** 0.5 or 1.0
            pos[v] = [pos[u][c] + d[c] / n * canon[v] for c in range(3)]
            
        # The face landmarks (0-10) are disconnected from the body graph.
        # Shift them by the same amount the neck was shifted by rigidify,
        # so the head stays perfectly attached to the rigidified body.
        raw_neck = [(f[11][c] + f[12][c]) / 2 for c in range(3)]
        rigid_neck = [(pos[11][c] + pos[12][c]) / 2 for c in range(3)]
        delta = [rigid_neck[c] - raw_neck[c] for c in range(3)]
        for lm in range(11):
            pos[lm] = [f[lm][c] + delta[c] for c in range(3)]
            
        out.append([pos[lm] + [f[lm][3]] for lm in range(33)])
    return out


def ground_anchor(frames, fps, gain=1.8):
    """Plant the feet on the ground so hip sway/bob shows over stationary feet.

    MediaPipe's world landmarks are HIP-centered: the hips sit at the origin every
    frame. If we just use the raw coordinates, the hips are frozen and the feet slide.
    This integrates the movement of the support foot to recover true hip translation,
    ensuring the support foot stays perfectly planted during weight shifts.

    `gain` scales the recovered sway: gain=1.0 is physically exact (planted foot stays
    put); >1 exaggerates hip movement for readability at the cost of the planted foot
    sliding by (gain-1)x its motion. Only the high-pass sway is scaled, not global drift."""
    frozen = [f for f in frames if f is not None]
    if not frozen:
        return frames

    H = []
    curr_H = [0.0, 0.0, 0.0]
    prev_f = None
    for f in frames:
        if f is None:
            H.append(None)
            continue
        if prev_f is not None:
            # support foot is the one with max y (world-DOWN)
            s = 27 if f[27][1] > f[28][1] else 28
            curr_H[0] += prev_f[s][0] - f[s][0]
            curr_H[1] += prev_f[s][1] - f[s][1]
            curr_H[2] += prev_f[s][2] - f[s][2]
        H.append(list(curr_H))
        prev_f = f

    # We now have the integrated hip position H. To prevent infinite drift across the
    # room (keeping the dance in-place), subtract a heavily smoothed version of H (a
    # high-pass filter). A 2-second window canceled the actual sways; a 10-second window
    # only removes very slow global room travel.
    window = int(fps * 10.0)
    valid_H = [h for h in H if h is not None]
    smoothed_H = []
    for i in range(len(valid_H)):
        start = max(0, i - window // 2)
        end = min(len(valid_H), i + window // 2)
        chunk = valid_H[start:end]
        smoothed_H.append((sum(h[0] for h in chunk) / len(chunk),
                           sum(h[1] for h in chunk) / len(chunk),
                           sum(h[2] for h in chunk) / len(chunk)))

    out, h_idx = [], 0
    for i, f in enumerate(frames):
        if f is None:
            out.append(None)
            continue
        hx = (H[i][0] - smoothed_H[h_idx][0]) * gain
        hy = (H[i][1] - smoothed_H[h_idx][1]) * gain
        hz = (H[i][2] - smoothed_H[h_idx][2]) * gain
        h_idx += 1
        out.append([[f[lm][0] + hx, f[lm][1] + hy, f[lm][2] + hz, f[lm][3]] for lm in range(33)])

    # Center the rig: shift so the median lowest-foot sits at the origin.
    valid_out = [f for f in out if f is not None]
    if valid_out:
        tgt_x = statistics.median((f[27][0] + f[28][0]) / 2 for f in valid_out)
        tgt_y = statistics.median(max(f[27][1], f[28][1]) for f in valid_out)
        tgt_z = statistics.median((f[27][2] + f[28][2]) / 2 for f in valid_out)
        for f in valid_out:
            for lm in range(33):
                f[lm][0] -= tgt_x
                f[lm][1] -= tgt_y
                f[lm][2] -= tgt_z
    return out


def extract(video, json_path):
    """Run MediaPipe over the video, clean the landmarks, write JSON. venv only."""
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    if not MODEL.exists():
        print("downloading pose model...", flush=True)
        import urllib.request
        urllib.request.urlretrieve(MODEL_URL, MODEL)

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        sys.exit(f"cannot open {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    opts = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL)),
        running_mode=vision.RunningMode.VIDEO,
    )
    frames, timestamps = [], []
    with vision.PoseLandmarker.create_from_options(opts) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            ts = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            if timestamps and ts <= timestamps[-1]:  # VFR: keep timestamps strictly rising
                ts = timestamps[-1] + 1
            timestamps.append(ts)
            img = mp.Image(image_format=mp.ImageFormat.SRGB,
                           data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            res = landmarker.detect_for_video(img, ts)
            wl = res.pose_world_landmarks  # metric, hip-centered (see CLAUDE.md)
            frames.append([[l.x, l.y, l.z, l.visibility] for l in wl[0]] if wl else None)
            if len(frames) % 100 == 0:
                print(f"  {len(frames)}/{total} frames", flush=True)
    cap.release()

    # Smooth jitter, pin bone lengths, then plant the feet on the ground
    frames = smooth_frames(frames, fps)
    frames = rigidify(frames)
    frames = ground_anchor(frames, fps)

    json_path.write_text(json.dumps({"fps": fps, "frames": frames, "timestamps": timestamps}))
    detected = sum(f is not None for f in frames)
    print(f"  {detected}/{len(frames)} frames with pose @ {fps:.2f} fps")


# ─────────────────────────── armature build (Blender side) ───────────────────────────

def mp_to_blender(x, y, z):
    # MediaPipe: x right, y down, z toward camera -> Blender: Z up (see CLAUDE.md)
    return x, z, -y


def build_blend(json_path, blend_path):
    """Build a baked stick-figure armature from the landmark JSON. Blender/bpy only."""
    import bpy

    data = json.loads(Path(json_path).read_text())
    frames = data["frames"]
    timestamps = data.get("timestamps")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = round(data["fps"])
    scene.render.fps_base = scene.render.fps / data["fps"]  # exact playback speed

    # one empty per landmark, keyframed with the raw motion
    # We add 3 virtual landmarks: 33 (Neck), 34 (Pelvis), 35 (Head Center)
    empties = []
    for i in range(36):
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
            
        # Scale up hands (make fingers visually larger)
        hand_scale = 1.5
        for wrist, fingers in [(15, [17, 19, 21]), (16, [18, 20, 22])]:
            for fing in fingers:
                for c in range(3):
                    lms[fing][c] = lms[wrist][c] + (lms[fing][c] - lms[wrist][c]) * hand_scale
            
        neck = [(lms[11][c] + lms[12][c]) / 2 for c in range(4)]
        pelvis = [(lms[23][c] + lms[24][c]) / 2 for c in range(4)]
        head = [(lms[7][c] + lms[8][c]) / 2 for c in range(4)]
        extended_lms = lms + [neck, pelvis, head]
        
        for e, (x, y, z, _vis) in zip(empties, extended_lms):
            e.location = mp_to_blender(x, y, z)
            e.keyframe_insert("location", frame=f)
    scene.frame_start, scene.frame_end = 1, max_frame

    arm = bpy.data.armatures.new("dancer")
    arm.display_type = "OCTAHEDRAL"
    obj = bpy.data.objects.new("dancer", arm)
    scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    
    BLENDER_CONNECTIONS = [
        (34, 33),  # Pelvis -> Neck (Spine)
        (33, 35),  # Neck -> Head (Midpoint of Ears)
        (33, 11),  # Neck -> L Shoulder
        (33, 12),  # Neck -> R Shoulder
        (34, 23),  # Pelvis -> L Hip
        (34, 24),  # Pelvis -> R Hip
        # Left Arm
        (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        # Right Arm
        (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
        # Left Leg
        (23, 25), (25, 27), (27, 29), (27, 31),
        # Right Leg
        (24, 26), (26, 28), (28, 30), (28, 32),
    ]
    
    # Find first valid frame to set the correct edit mode rest lengths
    valid_frames = [f for f in frames if f is not None]
    if valid_frames:
        f0 = valid_frames[0]
        # Make sure to scale hands in frame 0 too!
        for wrist, fingers in [(15, [17, 19, 21]), (16, [18, 20, 22])]:
            for fing in fingers:
                for c in range(3):
                    f0[fing][c] = f0[wrist][c] + (f0[fing][c] - f0[wrist][c]) * hand_scale
        neck_f0 = [(f0[11][c] + f0[12][c]) / 2 for c in range(4)]
        pelvis_f0 = [(f0[23][c] + f0[24][c]) / 2 for c in range(4)]
        head_f0 = [(f0[7][c] + f0[8][c]) / 2 for c in range(4)]
        ext_f0 = f0 + [neck_f0, pelvis_f0, head_f0]
    else:
        ext_f0 = [[0, 0, 0, 0]] * 36

    for a, b in BLENDER_CONNECTIONS:
        bone = arm.edit_bones.new(f"{a:02d}-{b:02d}")
        bone.head = mp_to_blender(*ext_f0[a][:3])
        bone.tail = mp_to_blender(*ext_f0[b][:3])
    bpy.ops.object.mode_set(mode="POSE")
    for a, b in BLENDER_CONNECTIONS:
        pb = obj.pose.bones[f"{a:02d}-{b:02d}"]
        pb.constraints.new("COPY_LOCATION").target = empties[a]
        c = pb.constraints.new("STRETCH_TO")
        c.target = empties[b]
        c.volume = 'NO_VOLUME'

    # bake constraints into keyframed bone motion, then drop the empties so the
    # .blend is a self-contained armature
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.nla.bake(frame_start=1, frame_end=max_frame, only_selected=True,
                     visual_keying=True, clear_constraints=True, bake_types={"POSE"})
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for e in empties:
        e.select_set(True)
    bpy.ops.object.delete()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    obj.rotation_euler = (0.0, 0.0, math.radians(PRESENT_YAW_DEG))  # present depth motion

    scene.frame_set(1)
    Path(blend_path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"  saved {Path(blend_path).name}: {max_frame} frames @ {data['fps']:.2f} fps")


# ─────────────────────────── self-verification ───────────────────────────

def dump_bones(blend_path, out_json, n=8):
    """Blender side: open a built .blend and dump each bone's world head/tail at n
    sample frames. No GL needed (OpenGL render is impossible headless), so this is how
    we get the baked armature back out to look at it."""
    import bpy

    bpy.ops.wm.open_mainfile(filepath=blend_path)
    scene = bpy.context.scene
    arm = next(o for o in scene.objects if o.type == "ARMATURE")
    f0, f1 = scene.frame_start, scene.frame_end
    frames = sorted({round(f0 + (f1 - f0) * k / (n - 1)) for k in range(n)})
    fps = scene.render.fps / scene.render.fps_base
    samples = []
    for f in frames:
        scene.frame_set(f)
        segs = [[list(arm.matrix_world @ b.head), list(arm.matrix_world @ b.tail)]
                for b in arm.pose.bones]
        samples.append({"frame": f, "segments": segs})
    # pelvis (hip midpoint) every frame, so translation the per-frame skeletons hide
    # (each is auto-centered) shows up as a trajectory
    track = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        track.append(list(arm.matrix_world @ arm.pose.bones["34-33"].head))
    Path(out_json).write_text(json.dumps(
        {"fps": fps, "samples": samples, "hip_track": track}))


def verify(video):
    """venv side: pull the baked bones out of the .blend and render a contact sheet —
    source video frame beside the reconstructed 3D skeleton — so the pose/coordinate
    conversion can be eyeballed. Writes blend-files/<name>.preview.png."""
    import subprocess
    import tempfile
    import cv2
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    video = Path(video)
    blend = BLENDS / f"{video.stem}.blend"
    if not blend.exists():
        sys.exit(f"no .blend to verify: {blend}")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        jp = Path(tmp.name)
    try:
        subprocess.run([BLENDER, "--background", "--python", __file__, "--",
                        "--dump", str(blend), str(jp)], check=True)
        d = json.loads(jp.read_text())
    finally:
        jp.unlink(missing_ok=True)

    fps = d["fps"]
    samples = d["samples"]
    n = len(samples)

    # One sequential decode pass, keeping the frame nearest each sample's timestamp.
    # Seeking (POS_MSEC/POS_FRAMES) is unreliable on VFR footage; this isn't, and the
    # last sample naturally lands on the true final frame instead of overshooting to blank.
    targets = [(s["frame"] - 1) / fps * 1000.0 for s in samples]
    best = [None] * n
    cap = cv2.VideoCapture(str(video))
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC)
        for j, tgt in enumerate(targets):
            dist = abs(t - tgt)
            if best[j] is None or dist < best[j][0]:
                best[j] = (dist, frame.copy())
    cap.release()

    gs = GridSpec(3, n, height_ratios=[3, 3, 2])
    fig = plt.figure(figsize=(2.4 * n, 8))
    for i, s in enumerate(samples):
        ax = fig.add_subplot(gs[0, i])
        if best[i] is not None:
            ax.imshow(cv2.cvtColor(best[i][1], cv2.COLOR_BGR2RGB))
        ax.set_title(f"frame {s['frame']}", fontsize=8)
        ax.axis("off")

        ax3 = fig.add_subplot(gs[1, i], projection="3d")
        pts = [c for h, t in s["segments"] for c in (h, t)]
        for h, t in s["segments"]:
            ax3.plot([h[0], t[0]], [h[1], t[1]], [h[2], t[2]], "-o", c="k", ms=1.5, lw=1)
        # equal aspect cube so limb lengths / "lying down" read truthfully
        ctr = [statistics.mean(p[c] for p in pts) for c in range(3)]
        r = max((max(p[c] for p in pts) - min(p[c] for p in pts)) for c in range(3)) / 2 or 1
        for c, lim in enumerate((ax3.set_xlim3d, ax3.set_ylim3d, ax3.set_zlim3d)):
            lim(ctr[c] - r, ctr[c] + r)
        ax3.view_init(elev=8, azim=-90)  # front view (camera down -Y), Z up
        ax3.set_box_aspect((1, 1, 1))
        ax3.axis("off")

    # hip trajectory, two projections (translation the auto-centered skeletons hide):
    # head-on = what you see from the front (depth invisible along view axis unless yawed),
    # top-down = proves the depth motion is there regardless.
    track = d["hip_track"]
    xs = [p[0] for p in track]
    ys = [p[1] for p in track]
    zs = [p[2] for p in track]
    t = range(len(track))
    half = n // 2 or 1
    axf = fig.add_subplot(gs[2, :half])
    axf.scatter(xs, zs, c=t, cmap="viridis", s=5)
    axf.set_aspect("equal")
    axf.set_xlabel("left-right X (m)")
    axf.set_ylabel("up Z (m)")
    axf.set_title(f"head-on view — X {max(xs) - min(xs):.2f} m, up {max(zs) - min(zs):.2f} m",
                  fontsize=8)
    axt = fig.add_subplot(gs[2, half:])
    axt.scatter(xs, ys, c=t, cmap="viridis", s=5)
    axt.set_aspect("equal")
    axt.set_xlabel("left-right X (m)")
    axt.set_ylabel("depth Y (m)")
    axt.set_title(f"top-down — X {max(xs) - min(xs):.2f} m, depth {max(ys) - min(ys):.2f} m",
                  fontsize=8)
    out_png = BLENDS / f"{video.stem}.preview.png"
    fig.savefig(out_png, dpi=80, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out_png.name}")
    return out_png


# ─────────────────────────── entry point ───────────────────────────

def process(video):
    """venv-side orchestration for one video: extract -> Blender -> .blend."""
    import subprocess
    import tempfile

    video = Path(video)
    blend = BLENDS / f"{video.stem}.blend"
    print(f"{video.name} -> {blend.name}")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json_path = Path(tmp.name)
    try:
        extract(video, json_path)
        subprocess.run([BLENDER, "--background", "--python", __file__, "--",
                        str(json_path), str(blend)], check=True)
    finally:
        json_path.unlink(missing_ok=True)


def main():
    try:
        import bpy  # noqa: F401 — only importable inside Blender
        argv = sys.argv[sys.argv.index("--") + 1:]
        if argv[0] == "--dump":
            dump_bones(argv[1], argv[2])
        else:
            build_blend(argv[0], argv[1])
        return
    except ImportError:
        pass

    args = sys.argv[1:]
    verify_only = "--verify" in args           # --verify: skip the build, just (re)draw preview
    videos = [Path(a) for a in args if not a.startswith("--")]
    if not videos:
        videos = sorted(p for p in DANCES.iterdir() if p.suffix.lower() in VIDEO_EXT)
    if not videos:
        sys.exit(f"no videos given and none found in {DANCES}/")
    for v in videos:
        if not verify_only:
            process(v)
        verify(v)  # every build ends with a preview PNG to eyeball


if __name__ == "__main__":
    main()
