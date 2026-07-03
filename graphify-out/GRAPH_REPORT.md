# Graph Report - .  (2026-07-03)

## Corpus Check
- 5 files · ~93,420 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 23 nodes · 24 edges · 5 communities (4 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 20,163 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Depth Recovery Concepts|Depth Recovery Concepts]]
- [[_COMMUNITY_Blender Armature Pipeline|Blender Armature Pipeline]]
- [[_COMMUNITY_Pose Extraction Flow|Pose Extraction Flow]]
- [[_COMMUNITY_import_pose.py Code|import_pose.py Code]]
- [[_COMMUNITY_extract_pose.py Code|extract_pose.py Code]]

## God Nodes (most connected - your core abstractions)
1. `extract_pose.py Script` - 6 edges
2. `import_pose.py Script` - 5 edges
3. `MediaPipe Pose` - 3 edges
4. `pose_data.json Intermediate Format` - 3 edges
5. `pose_world_landmarks (Metric Hip-Centered Coordinates)` - 3 edges
6. `mp_to_blender()` - 2 edges
7. `main()` - 2 edges
8. `2dto3d Dance Video to Blender Pipeline` - 2 edges
9. `Monocular Depth Recovery via Human Body Priors` - 2 edges
10. `MediaPipe to Blender Coordinate Conversion` - 2 edges

## Surprising Connections (you probably didn't know these)
- `2dto3d Dance Video to Blender Pipeline` --references--> `extract_pose.py Script`  [EXTRACTED]
  CLAUDE.md → CLAUDE.md  _Bridges community 1 → community 2_
- `extract_pose.py Script` --references--> `MediaPipe Pose`  [EXTRACTED]
  CLAUDE.md → CLAUDE.md  _Bridges community 0 → community 2_
- `import_pose.py Script` --implements--> `MediaPipe to Blender Coordinate Conversion`  [EXTRACTED]
  CLAUDE.md → CLAUDE.md  _Bridges community 1 → community 0_

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Video to Armature Data Flow** — claude_extract_pose_script, claude_pose_data_json, claude_import_pose_script, claude_blender_armature [EXTRACTED 1.00]

## Communities (5 total, 1 thin omitted)

### Community 0 - "Depth Recovery Concepts"
Cohesion: 0.33
Nodes (6): MediaPipe to Blender Coordinate Conversion, MediaPipe Pose, Monocular Depth Recovery via Human Body Priors, Perspective Projection Depth Loss, pose_world_landmarks (Metric Hip-Centered Coordinates), Global Root Translation Loss (Hip-Centered Landmarks)

### Community 1 - "Blender Armature Pipeline"
Cohesion: 0.40
Nodes (5): 2dto3d Dance Video to Blender Pipeline, Blender Stick-Figure Armature, Blender Bundled Python Isolation Constraint, import_pose.py Script, MediaPipe POSE_CONNECTIONS Topology

### Community 2 - "Pose Extraction Flow"
Cohesion: 0.50
Nodes (5): extract_pose.py Script, Video FPS to Blender Scene FPS Synchronization, Landmark Jitter and Deferred Smoothing, OpenCV Frame Reading, pose_data.json Intermediate Format

### Community 3 - "import_pose.py Code"
Cohesion: 0.67
Nodes (3): main(), mp_to_blender(), Build a keyframed stick-figure armature from pose_data.json.  Usage: /Applicatio

## Knowledge Gaps
- **3 isolated node(s):** `MediaPipe POSE_CONNECTIONS Topology`, `Perspective Projection Depth Loss`, `OpenCV Frame Reading`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `extract_pose.py Script` connect `Pose Extraction Flow` to `Depth Recovery Concepts`, `Blender Armature Pipeline`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `import_pose.py Script` connect `Blender Armature Pipeline` to `Depth Recovery Concepts`, `Pose Extraction Flow`?**
  _High betweenness centrality (0.197) - this node is a cross-community bridge._
- **Why does `MediaPipe Pose` connect `Depth Recovery Concepts` to `Pose Extraction Flow`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **What connects `Extract 3D pose landmarks from a dance video into pose_data.json.  Usage: .venv/`, `Build a keyframed stick-figure armature from pose_data.json.  Usage: /Applicatio`, `MediaPipe POSE_CONNECTIONS Topology` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._