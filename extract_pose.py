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
            frames.append(
                [[l.x, l.y, l.z, l.visibility] for l in wl[0]]
                if wl else None  # ponytail: None = no detection; importer skips these
            )
            if len(frames) % 100 == 0:
                print(f"{len(frames)}/{total} frames", flush=True)
    cap.release()

    with open(out, "w") as f:
        json.dump({"fps": fps, "frames": frames}, f)
    detected = sum(f is not None for f in frames)
    print(f"done: {detected}/{len(frames)} frames with pose @ {fps:.2f} fps -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
