# Graph Report - .  (2026-07-15)

## Corpus Check
- 10 files · ~28,895 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 81 nodes · 121 edges · 10 communities
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Blender Build & Armature|Blender Build & Armature]]
- [[_COMMUNITY_Signal Cleanup Pipeline|Signal Cleanup Pipeline]]
- [[_COMMUNITY_Dance1 Preview Outputs|Dance1 Preview Outputs]]
- [[_COMMUNITY_Dance Preview & Anchoring|Dance Preview & Anchoring]]
- [[_COMMUNITY_Extraction & Rigidify|Extraction & Rigidify]]
- [[_COMMUNITY_Smoothing & Selftest|Smoothing & Selftest]]
- [[_COMMUNITY_Headless Verification|Headless Verification]]
- [[_COMMUNITY_Pipeline Entry & Coord Transform|Pipeline Entry & Coord Transform]]
- [[_COMMUNITY_CLI Dispatch & Dump|CLI Dispatch & Dump]]
- [[_COMMUNITY_Graphify Tooling|Graphify Tooling]]

## God Nodes (most connected - your core abstractions)
1. `Extract Phase (extract())` - 9 edges
2. `Build Phase (build_blend())` - 9 edges
3. `Ground Anchor (Foot Planting & Hip Recovery)` - 7 edges
4. `ground_anchor()` - 6 edges
5. `extract()` - 6 edges
6. `selftest()` - 6 edges
7. `main()` - 6 edges
8. `2dto3d Pipeline` - 6 edges
9. `MediaPipe Pose` - 6 edges
10. `dance.preview.png Contact Sheet` - 6 edges

## Surprising Connections (you probably didn't know these)
- `build_blend()` --implements--> `Blender Armature Screenshot`  [INFERRED]
  dance_to_3d.py → image.png
- `verify()` --implements--> `dance1.preview.png Contact Sheet`  [INFERRED]
  dance_to_3d.py → blend-files/dance1.preview.png
- `verify()` --implements--> `dance.preview.png Contact Sheet`  [INFERRED]
  dance_to_3d.py → blend-files/dance.preview.png
- `Stick-Figure Bone Topology in Blender` --semantically_similar_to--> `dance 3D Stick Figure Reconstructions`  [INFERRED] [semantically similar]
  image.png → blend-files/dance.preview.png
- `ground_anchor()` --rationale_for--> `dance Head-On Hip Trajectory (X 0.57m, up 0.11m)`  [INFERRED]
  dance_to_3d.py → blend-files/dance.preview.png

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Signal Cleanup Pipeline (smooth -> rigidify -> ground_anchor)** — claude_one_euro_filter, claude_rigidify, claude_ground_anchor, claude_extract_phase [EXTRACTED 1.00]
- **Ground Anchor Subsystems (high-pass sway, gain, foot lock)** — claude_ground_anchor, claude_high_pass_sway, claude_gain_knob, claude_foot_lock [EXTRACTED 1.00]
- **Dual-Interpreter Execution (venv extract -> Blender build)** — claude_dual_interpreter, claude_extract_phase, claude_build_phase, claude_json_interchange [EXTRACTED 1.00]
- **Headless Verification System (verify, dump_bones, contact sheet)** — claude_verify, claude_dump_bones, claude_contact_sheet, claude_matplotlib [EXTRACTED 1.00]
- **Proposed Pipeline Improvements (TODO)** — todo_savitzky_golay, todo_foot_contact_locking, todo_bone_roll_improvement, todo_spline_resampling [EXTRACTED 1.00]
- **Blender Integration (coordinate conversion, NLA bake, bone roll, yaw)** — claude_build_phase, claude_coordinate_conversion, claude_nla_bake, claude_bone_roll, claude_present_yaw [EXTRACTED 1.00]

## Communities (10 total, 0 thin omitted)

### Community 0 - "Blender Build & Armature"
Cohesion: 0.16
Nodes (18): Blender, Deterministic Bone Roll, Build Phase (build_blend()), Coordinate System Conversion (mp_to_blender), dance_to_3d.py Script, Dual-Interpreter Execution Model, Loud Failure Policy (--python-exit-code 1), MediaPipe Pose (+10 more)

### Community 1 - "Signal Cleanup Pipeline"
Cohesion: 0.16
Nodes (18): Extract Phase (extract()), Velocity-Gated Foot Lock, Sway Gain Knob (default 1.8), Ground Anchor (Foot Planting & Hip Recovery), High-Pass Sway Recovery, Temporary JSON Interchange Format, One Euro Filter (smooth_frames), OpenCV (cv2) (+10 more)

### Community 2 - "Dance1 Preview Outputs"
Cohesion: 0.38
Nodes (7): dance1.preview.png Contact Sheet, dance1 Head-On Hip Trajectory (X 0.69m, up 0.25m), dance1 3D Stick Figure Reconstructions, dance1 Top-Down Hip Trajectory (X 0.69m, depth 0.75m), dance1 Source Video Frames, Blender Armature Screenshot, Stick-Figure Bone Topology in Blender

### Community 3 - "Dance Preview & Anchoring"
Cohesion: 0.43
Nodes (7): dance.preview.png Contact Sheet, dance Head-On Hip Trajectory (X 0.57m, up 0.11m), dance 3D Stick Figure Reconstructions, dance Top-Down Hip Trajectory (X 0.57m, depth 0.39m), dance.MP4 Source Video Frames, ground_anchor(), Plant the feet on the ground so hip sway/bob shows over stationary feet.      Me

### Community 4 - "Extraction & Rigidify"
Cohesion: 0.33
Nodes (6): extract(), process(), Enforce constant bone lengths. MediaPipe's world landmarks let limbs stretch, Run MediaPipe over the video, clean the landmarks, write JSON. venv only., venv-side orchestration for one video: extract -> Blender -> .blend., rigidify()

### Community 5 - "Smoothing & Selftest"
Cohesion: 0.33
Nodes (6): _one_euro(), One Euro filter over one axis of one landmark. None = dropped frame -> reset., Run the cleanup passes over a synthetic noisy skeleton (stdlib only, no video,, Velocity-adaptive One Euro low-pass per landmark axis: heavy smoothing when a, selftest(), smooth_frames()

### Community 6 - "Headless Verification"
Cohesion: 0.60
Nodes (5): Contact Sheet Preview (.preview.png), dump_bones() Function, Matplotlib, Self-Verification (verify / --verify), Headless Self-Verification (DESIGN)

### Community 7 - "Pipeline Entry & Coord Transform"
Cohesion: 0.50
Nodes (4): build_blend(), mp_to_blender(), Dance video -> animated 3D Blender armature, in one command.      .venv/bin/pyth, Build a baked stick-figure armature from the landmark JSON. Blender/bpy only.

### Community 8 - "CLI Dispatch & Dump"
Cohesion: 0.40
Nodes (5): dump_bones(), main(), Blender side: open a built .blend and dump each bone's world head/tail at n, venv side: pull the baked bones out of the .blend and render a contact sheet —, verify()

### Community 9 - "Graphify Tooling"
Cohesion: 0.67
Nodes (4): graphify Knowledge Graph (graphify-out/), graphify query/path/explain Tools, graphify Skill (SKILL.md), graphify Workflow

## Knowledge Gaps
- **6 isolated node(s):** `POSE_CONNECTIONS Topology`, `Matplotlib`, `Proposed: Savitzky-Golay Filter Upgrade`, `Proposed: Deterministic Bone Roll Calculation`, `Proposed: Cubic Spline Timestamp Resampling` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Extract Phase (extract())` connect `Signal Cleanup Pipeline` to `Blender Build & Armature`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `Build Phase (build_blend())` connect `Blender Build & Armature` to `Signal Cleanup Pipeline`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `verify()` connect `CLI Dispatch & Dump` to `Dance1 Preview Outputs`, `Dance Preview & Anchoring`, `Pipeline Entry & Coord Transform`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ground_anchor()` (e.g. with `dance Head-On Hip Trajectory (X 0.57m, up 0.11m)` and `dance Top-Down Hip Trajectory (X 0.57m, depth 0.39m)`) actually correct?**
  _`ground_anchor()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Dance video -> animated 3D Blender armature, in one command.      .venv/bin/pyth`, `One Euro filter over one axis of one landmark. None = dropped frame -> reset.`, `Velocity-adaptive One Euro low-pass per landmark axis: heavy smoothing when a` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._