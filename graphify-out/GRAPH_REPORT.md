# Graph Report - .  (2026-07-04)

## Corpus Check
- Corpus is ~2,822 words - fits in a single context window. You may not need a graph.

## Summary
- 39 nodes · 56 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.82)
- Token cost: 25,407 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Pipeline & Blender Build|Pipeline & Blender Build]]
- [[_COMMUNITY_Pose Extraction & Cleanup|Pose Extraction & Cleanup]]
- [[_COMMUNITY_build_blend Code|build_blend Code]]
- [[_COMMUNITY_Graphify Tool Docs|Graphify Tool Docs]]
- [[_COMMUNITY_Extract & Ground-Anchor Code|Extract & Ground-Anchor Code]]
- [[_COMMUNITY_Smoothing Code|Smoothing Code]]
- [[_COMMUNITY_Entry & Orchestration|Entry & Orchestration]]
- [[_COMMUNITY_Rigidify Code|Rigidify Code]]

## God Nodes (most connected - your core abstractions)
1. `extract() Half (venv)` - 7 edges
2. `build_blend() Half (Blender)` - 7 edges
3. `extract()` - 6 edges
4. `pose_world_landmarks (Metric, Hip-Centered)` - 5 edges
5. `Bone-Length Rigidify (rigidify)` - 5 edges
6. `smooth_frames()` - 4 edges
7. `build_blend()` - 4 edges
8. `process()` - 4 edges
9. `_one_euro()` - 3 edges
10. `rigidify()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `graphify Workflow` --conceptually_related_to--> `graphify Knowledge Graph (graphify-out/)`  [INFERRED]
  .agents/workflows/graphify.md → .agents/rules/graphify.md
- `graphify Skill (SKILL.md)` --conceptually_related_to--> `graphify query/path/explain Tools`  [INFERRED]
  .agents/workflows/graphify.md → .agents/rules/graphify.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three-Pass Landmark Cleaning Flow** — claude_one_euro_filter, claude_bone_length_rigidify, claude_ground_anchor [EXTRACTED 0.90]
- **Video to Blend Pipeline Flow** — claude_mediapipe_pose, claude_pose_data_json, claude_stick_figure_armature, claude_constraint_baking [INFERRED 0.85]

## Communities (8 total, 1 thin omitted)

### Community 0 - "Pipeline & Blender Build"
Cohesion: 0.24
Nodes (10): 2dto3d Dance-to-3D Pipeline, Blender Scene FPS from Video FPS, build_blend() Half (Blender), Constraint Baking (nla.bake), MediaPipe-to-Blender Coordinate Conversion, dance_to_3d.py Single Self-Reinvoking Script, POSE_CONNECTIONS Topology (CONNECTIONS constant), Temporary pose_data JSON (+2 more)

### Community 1 - "Pose Extraction & Cleanup"
Cohesion: 0.52
Nodes (7): Bone-Length Rigidify (rigidify), extract() Half (venv), Ground Anchor Foot Planting (ground_anchor), MediaPipe Pose Monocular 3D Estimator, One Euro Filter (smooth_frames), Perspective Projection Depth Loss, pose_world_landmarks (Metric, Hip-Centered)

### Community 2 - "build_blend Code"
Cohesion: 0.50
Nodes (4): build_blend(), mp_to_blender(), Dance video -> animated 3D Blender armature, in one command.      .venv/bin/pyth, Build a baked stick-figure armature from the landmark JSON. Blender/bpy only.

### Community 3 - "Graphify Tool Docs"
Cohesion: 0.67
Nodes (4): graphify Knowledge Graph (graphify-out/), graphify query/path/explain Tools, graphify Skill (SKILL.md), graphify Workflow

### Community 4 - "Extract & Ground-Anchor Code"
Cohesion: 0.50
Nodes (4): extract(), ground_anchor(), Plant the feet on the ground so hip sway/bob shows over stationary feet.      Me, Run MediaPipe over the video, clean the landmarks, write JSON. venv only.

### Community 5 - "Smoothing Code"
Cohesion: 0.50
Nodes (4): _one_euro(), One Euro filter over one axis of one landmark. None = dropped frame -> reset., Velocity-adaptive One Euro low-pass per landmark axis: heavy smoothing when a, smooth_frames()

### Community 6 - "Entry & Orchestration"
Cohesion: 0.67
Nodes (3): main(), process(), venv-side orchestration for one video: extract -> Blender -> .blend.

## Knowledge Gaps
- **1 isolated node(s):** `2dto3d Dance-to-3D Pipeline`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `extract() Half (venv)` connect `Pose Extraction & Cleanup` to `Pipeline & Blender Build`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `build_blend() Half (Blender)` connect `Pipeline & Blender Build` to `Pose Extraction & Cleanup`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `extract()` connect `Extract & Ground-Anchor Code` to `build_blend Code`, `Smoothing Code`, `Entry & Orchestration`, `Rigidify Code`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **What connects `Dance video -> animated 3D Blender armature, in one command.      .venv/bin/pyth`, `One Euro filter over one axis of one landmark. None = dropped frame -> reset.`, `Velocity-adaptive One Euro low-pass per landmark axis: heavy smoothing when a` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._