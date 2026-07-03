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


def ground_anchor(frames):
    """Plant the feet on the ground so hip sway/bob shows over stationary feet.

    MediaPipe's world landmarks are HIP-centered: the hips sit at the origin every
    frame. If we just use the raw coordinates, the hips are frozen and the feet slide.
    This integrates the movement of the support foot to recover true hip translation,
    ensuring the support foot stays perfectly planted during weight shifts."""
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
        
    # We now have the integrated hip position H.
    # To prevent infinite drift across the room (keeping the dance in-place),
    # we subtract a very heavily smoothed version of H (a high-pass filter).
    # A 2-second window was too aggressive and canceled out the actual dance sways!
    # We use a 10-second window so it only removes very slow global room travel.
    out = []
    fps = 41.43  # approximate, just for window size
    window = int(fps * 10.0)
    
    valid_H = [h for h in H if h is not None]
    smoothed_H = []
    for i in range(len(valid_H)):
        start = max(0, i - window // 2)
        end = min(len(valid_H), i + window // 2)
        chunk = valid_H[start:end]
        avg_x = sum(h[0] for h in chunk) / len(chunk)
        avg_y = sum(h[1] for h in chunk) / len(chunk)
        avg_z = sum(h[2] for h in chunk) / len(chunk)
        smoothed_H.append((avg_x, avg_y, avg_z))
        
    # Apply the shift
    h_idx = 0
    for i, f in enumerate(frames):
        if f is None:
            out.append(None)
            continue
        
        # True hip position minus the slow drift
        hx = H[i][0] - smoothed_H[h_idx][0]
        hy = H[i][1] - smoothed_H[h_idx][1]
        hz = H[i][2] - smoothed_H[h_idx][2]
        h_idx += 1
        
        out.append([[f[lm][0] + hx, f[lm][1] + hy, f[lm][2] + hz, f[lm][3]] for lm in range(33)])
        
    # Finally, shift the whole clip so the median lowest foot is at y=0, x=0, z=0
    # just to center the rig in Blender.
    valid_out = [f for f in out if f is not None]
    if valid_out:
        tgt_y = statistics.median(max(f[27][1], f[28][1]) for f in valid_out)
        tgt_x = statistics.median((f[27][0] + f[28][0])/2 for f in valid_out)
        tgt_z = statistics.median((f[27][2] + f[28][2])/2 for f in valid_out)
        for f in valid_out:
            for lm in range(33):
                f[lm][0] -= tgt_x
                f[lm][1] -= tgt_y
                f[lm][2] -= tgt_z
                
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
    timestamps = []
    with vision.PoseLandmarker.create_from_options(opts) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            
            ts = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            if timestamps and ts <= timestamps[-1]:
                ts = timestamps[-1] + 1
            timestamps.append(ts)
            
            img = mp.Image(image_format=mp.ImageFormat.SRGB,
                           data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            res = landmarker.detect_for_video(img, ts)
            wl = res.pose_world_landmarks  # metric, hip-centered (see CLAUDE.md)
            if wl:
                frames.append([[l.x, l.y, l.z, l.visibility] for l in wl[0]])
            else:
                frames.append(None)  # ponytail: None = no detection; importer skips these
            if len(frames) % 100 == 0:
                print(f"{len(frames)}/{total} frames", flush=True)
    cap.release()

    # Smooth jitter, pin bone lengths, then plant the feet on the ground
    frames = smooth_frames(frames, fps)
    frames = rigidify(frames)
    frames = ground_anchor(frames)

    with open(out, "w") as f:
        json.dump({"fps": fps, "frames": frames, "timestamps": timestamps}, f)
    detected = sum(f is not None for f in frames)
    print(f"done: {detected}/{len(frames)} frames with pose @ {fps:.2f} fps -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
