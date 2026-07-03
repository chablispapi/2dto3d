"""Extract 3D pose landmarks from a dance video into pose_data.json.

Usage: .venv/bin/python extract_pose.py [video] [out.json]
"""
import json
import sys
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODEL = Path(__file__).parent / "pose_landmarker_full.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_full/float16/latest/pose_landmarker_full.task")


def smooth_frames(frames, window=5):
    """Apply a simple moving average over each landmark's time series to reduce jitter."""
    if not frames: return frames
    smoothed = []
    half = window // 2
    for i in range(len(frames)):
        if frames[i] is None:
            smoothed.append(None)
            continue
            
        start = max(0, i - half)
        end = min(len(frames), i + half + 1)
        valid = [frames[j] for j in range(start, end) if frames[j] is not None]
        
        if not valid:
            smoothed.append(None)
            continue
            
        num_lms = len(frames[i])
        avg_lm = []
        for lm_idx in range(num_lms):
            avg_x = sum(n[lm_idx][0] for n in valid) / len(valid)
            avg_y = sum(n[lm_idx][1] for n in valid) / len(valid)
            avg_z = sum(n[lm_idx][2] for n in valid) / len(valid)
            avg_v = sum(n[lm_idx][3] for n in valid) / len(valid)
            avg_lm.append([avg_x, avg_y, avg_z, avg_v])
        smoothed.append(avg_lm)
    return smoothed


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
                
                # Recover global root translation from normalized hip landmarks
                h, w = frame.shape[:2]
                dx_w = wl[23].x - wl[24].x
                dy_w = wl[23].y - wl[24].y
                dist_w = (dx_w**2 + dy_w**2)**0.5
                
                dx_n = (nl[23].x - nl[24].x) * w
                dy_n = (nl[23].y - nl[24].y) * h
                dist_n = (dx_n**2 + dy_n**2)**0.5
                
                scale = dist_w / dist_n if dist_n > 0 else 0
                
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

    # Apply moving average to smooth landmark jitter
    frames = smooth_frames(frames, window=5)

    with open(out, "w") as f:
        json.dump({"fps": fps, "frames": frames}, f)
    detected = sum(f is not None for f in frames)
    print(f"done: {detected}/{len(frames)} frames with pose @ {fps:.2f} fps -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
