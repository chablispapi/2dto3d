# Graph Report - 2dto3d  (2026-07-03)

## Corpus Check
- 6 files · ~93,837 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 37 nodes · 18 edges · 21 communities (3 shown, 18 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9d0d938f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Depth Recovery Concepts|Depth Recovery Concepts]]
- [[_COMMUNITY_Blender Armature Pipeline|Blender Armature Pipeline]]
- [[_COMMUNITY_Pose Extraction Flow|Pose Extraction Flow]]
- [[_COMMUNITY_import_pose.py Code|import_pose.py Code]]
- [[_COMMUNITY_extract_pose.py Code|extract_pose.py Code]]
- [[_COMMUNITY_2dto3d — dance video to 3D Blender animation|2dto3d — dance video to 3D Blender animation]]
- [[_COMMUNITY_graphify|graphify.md]]
- [[_COMMUNITY_graphify|graphify.md]]
- [[_COMMUNITY_Blender Stick-Figure Armature|Blender Stick-Figure Armature]]
- [[_COMMUNITY_Blender Bundled Python Isolation Constraint|Blender Bundled Python Isolation Constraint]]
- [[_COMMUNITY_Video FPS to Blender Scene FPS Synchronization|Video FPS to Blender Scene FPS Synchronization]]
- [[_COMMUNITY_import_pose.py Script|import_pose.py Script]]
- [[_COMMUNITY_Landmark Jitter and Deferred Smoothing|Landmark Jitter and Deferred Smoothing]]
- [[_COMMUNITY_MediaPipe Pose|MediaPipe Pose]]
- [[_COMMUNITY_Monocular Depth Recovery via Human Body Priors|Monocular Depth Recovery via Human Body Priors]]
- [[_COMMUNITY_OpenCV Frame Reading|OpenCV Frame Reading]]
- [[_COMMUNITY_Perspective Projection Depth Loss|Perspective Projection Depth Loss]]
- [[_COMMUNITY_MediaPipe POSE_CONNECTIONS Topology|MediaPipe POSE_CONNECTIONS Topology]]
- [[_COMMUNITY_pose_data.json Intermediate Format|pose_data.json Intermediate Format]]
- [[_COMMUNITY_pose_world_landmarks (Metric Hip-Centered Coordinates)|pose_world_landmarks (Metric Hip-Centered Coordinates)]]
- [[_COMMUNITY_Global Root Translation Loss (Hip-Centered Landmarks)|Global Root Translation Loss (Hip-Centered Landmarks)]]

## God Nodes (most connected - your core abstractions)
1. `2dto3d — dance video to 3D Blender animation` - 7 edges
2. `smooth_frames()` - 3 edges
3. `main()` - 2 edges
4. `mp_to_blender()` - 2 edges
5. `main()` - 2 edges
6. `Extract 3D pose landmarks from a dance video into pose_data.json.  Usage: .venv/` - 1 edges
7. `Apply a simple moving average over each landmark's time series to reduce jitter.` - 1 edges
8. `Build a keyframed stick-figure armature from pose_data.json.  Usage: /Applicatio` - 1 edges
9. `graphify` - 1 edges
10. `Workflow: graphify` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Video to Armature Data Flow** — claude_extract_pose_script, claude_pose_data_json, claude_import_pose_script, claude_blender_armature [EXTRACTED 1.00]

## Communities (21 total, 18 thin omitted)

### Community 3 - "import_pose.py Code"
Cohesion: 0.67
Nodes (3): main(), mp_to_blender(), Build a keyframed stick-figure armature from pose_data.json.  Usage: /Applicatio

### Community 4 - "extract_pose.py Code"
Cohesion: 0.50
Nodes (4): main(), Extract 3D pose landmarks from a dance video into pose_data.json.  Usage: .venv/, Apply a simple moving average over each landmark's time series to reduce jitter., smooth_frames()

### Community 5 - "2dto3d — dance video to 3D Blender animation"
Cohesion: 0.25
Nodes (7): 2dto3d — dance video to 3D Blender animation, Environment, Goal, Non-goals, Pipeline (2 scripts, keep it that way), Technical notes, The core idea

## Knowledge Gaps
- **19 isolated node(s):** `graphify`, `Workflow: graphify`, `Goal`, `The core idea`, `Pipeline (2 scripts, keep it that way)` (+14 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Extract 3D pose landmarks from a dance video into pose_data.json.  Usage: .venv/`, `Apply a simple moving average over each landmark's time series to reduce jitter.`, `Build a keyframed stick-figure armature from pose_data.json.  Usage: /Applicatio` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._