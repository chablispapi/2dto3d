"""Extract 3D pose landmarks from a dance video into pose_data.json.

Usage: .venv/bin/python extract_pose.py [video] [out.json]
"""
import json
import math
import statistics
import sys
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODEL = Path(__file__).parent / "pose_landmarker_full.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_full/float16/latest/pose_landmarker_full.task")

# MediaPipe POSE_CONNECTIONS. Duplicated in import_pose.py on purpose — that script
# runs in Blender's separate Python and can't import this one (see CLAUDE.md).
CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
]


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
        out.append([(pos.get(lm, f[lm][:3])) + [f[lm][3]] for lm in range(33)])
    return out


def _one_euro(series, fps, mincutoff, beta, dcutoff=1.0):
    """One Euro filter over one axis of one landmark. None = dropped frame -> reset."""
    def alpha(cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau * fps)

    out, x_prev, dx_prev = [], None, 0.0
    for x in series:
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
        a = alpha(mincutoff + beta * abs(dx_hat))  # faster motion -> higher cutoff -> less lag
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
        for c in range(3):
            sm = _one_euro([None if f is None else f[lm][c] for f in frames], fps, mincutoff, beta)
            for i, v in enumerate(sm):
                if out[i] is not None:
                    out[i][lm][c] = v
    return out


def main(video="dance.MP4", out="pose_data.json"):
    if not MODEL.exists():
        print("downloading pose model...", flush=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL)

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        sys.exit(f"cannot open {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    opts = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL)),
        running_mode=vision.RunningMode.VIDEO,
    )
    frames = []
    recent_scales = []  # last N accepted meters-per-pixel scales, for spike rejection
    with vision.PoseLandmarker.create_from_options(opts) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            img = mp.Image(image_format=mp.ImageFormat.SRGB,
                           data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            res = landmarker.detect_for_video(img, int(len(frames) * 1000 / fps))
            wl = res.pose_world_landmarks  # metric, hip-centered (see CLAUDE.md)
            nl = res.pose_landmarks        # normalized image coordinates
            
            if wl and nl:
                wl = wl[0]
                nl = nl[0]
                
                # Recover global root translation from normalized hip landmarks.
                # scale = meters-per-pixel, from a size reference that is stable under
                # rotation: full-body vertical extent (shoulder-center -> ankle-center).
                # Hip WIDTH (the obvious choice) collapses toward zero when the dancer
                # turns sideways -> scale explodes; vertical extent barely changes.
                h, w = frame.shape[:2]
                body_px = abs((nl[27].y + nl[28].y) / 2 - (nl[11].y + nl[12].y) / 2) * h
                body_m = abs((wl[27].y + wl[28].y) / 2 - (wl[11].y + wl[12].y) / 2)
                scale = body_m / body_px if body_px > 1e-6 else 0

                # Spike rejection: clamp to the recent median. Even the stable proxy
                # jumps when the lower body is occluded; hold within 2x of median.
                if recent_scales:
                    med = statistics.median(recent_scales)
                    scale = med if scale <= 0 else max(0.5 * med, min(2.0 * med, scale))
                if scale > 0:
                    recent_scales.append(scale)
                    del recent_scales[:-15]

                # Center of screen is roughly origin
                mid_x_n = (nl[23].x + nl[24].x) / 2
                mid_y_n = (nl[23].y + nl[24].y) / 2
                tx = (mid_x_n - 0.5) * w * scale
                ty = (mid_y_n - 0.5) * h * scale

                frames.append([[l.x + tx, l.y + ty, l.z, l.visibility] for l in wl])
            else:
                frames.append(None)  # ponytail: None = no detection; importer skips these
            if len(frames) % 100 == 0:
                print(f"{len(frames)}/{total} frames", flush=True)
    cap.release()

    # Smooth jitter, then pin bone lengths so limbs stop stretching
    frames = smooth_frames(frames, fps)
    frames = rigidify(frames)

    with open(out, "w") as f:
        json.dump({"fps": fps, "frames": frames}, f)
    detected = sum(f is not None for f in frames)
    print(f"done: {detected}/{len(frames)} frames with pose @ {fps:.2f} fps -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
