
## 1. System Overview & Architecture

The **2dto3d** pipeline is a headless, single-command batch processing system that converts monocular 2D dance videos into 3D animated stick-figure armatures within Blender.

Because perspective projection maps a 3d point to a 2d screen via $x' = x/z$ and $y' = y/z$, the depth coordinate $z$ is fundamentally lost in single-camera footage. The system bypasses custom depth solvers by leveraging **MediaPipe Pose**, which infers 3D metric world landmarks using learned anthropometric priors (e.g., rigid bone lengths and joint range limits).

### Execution Orchestration

To resolve the dependency conflict between standard Python machine learning libraries (`mediapipe`, `cv2`) and Blender's isolated internal Python environment, the system consolidates the pipeline into a single self-invoking script (`dance_to_3d.py`) operating across two distinct execution contexts:

| Phase | Interpreter Environment | Core Responsibilities | Output Artifacts |
| --- | --- | --- | --- |
| **1. Extract** | Local Virtual Environment (`.venv`) | Video decoding, landmark inference, signal filtering, rigidification, ground anchoring. | Temporary JSON file (fps, timestamps, 33 landmarks $\times$ $[x,y,z, \text{visibility}]$). |
| **2. Build** | Blender Embedded Python | JSON ingestion, topology mapping, coordinate conversion, armature generation, constraint baking. | Final `.blend` file, temporary preview data dump. |
| **3. Verify** | Local Virtual Environment (`.venv`) | Matplotlib contact sheet generation from dumped bone matrices and video frames. | Visual contact sheet (`.preview.png`). |

---

## 2. Data & Signal Processing Pipeline

The extraction phase transforms raw, noisy landmark coordinates into a kinematically stable skeleton through a four-stage sequential cleaning pipeline:

### Stage 1: Landmark Extraction & Synchronization

* **Inference:** Extracts 33 metric world landmarks (`pose_world_landmarks`) per frame, centered at the mid-hip origin.
* **VFR Handling:** Captures exact presentation timestamps (`cv2.CAP_PROP_POS_MSEC`) alongside the average frame rate to prevent drift in Variable Frame Rate (VFR) mobile video footage.

### Stage 2: Adaptive Low-Pass Smoothing (One Euro Filter)

* **Problem:** Raw inference data exhibits high-frequency jitter during static poses and lag during rapid motion.
* **Solution:** Applies a **One Euro Filter** independently to each landmark axis. The filter dynamically adjusts its cutoff frequency based on velocity: heavy low-pass filtering stabilizes slow or static joints, while the filter opens up during fast dance sways to eliminate lag.

### Stage 3: Kinematic Rigidification

* **Problem:** MediaPipe world landmarks treat joints independently, causing limb segments to stretch or compress by 3–5$\times$ between frames.
* **Solution:** Rebuilds the skeletal geometry per frame across a directed spanning tree rooted at the hip center. Each child joint retains its observed direction vector from the parent, but its distance is strictly constrained to the median bone length computed across the entire video. Face landmarks (0–10) are decoupled from the rigid body graph and pass through unchanged.

### Stage 4: Ground Anchoring & High-Pass Sway Recovery

* **Problem:** Because MediaPipe world coordinates are hip-centered $(0,0,0)$, a dancer shifting weight over planted feet appears inverted: the torso remains frozen in space while the floor and feet slide beneath them.
* **Solution:** 1. Identifies the lowest foot landmark per frame as the instantaneous support base.
2. Integrates the frame-to-frame inverse translation of this support foot to derive true global hip movement.
3. Subtracts a heavily smoothed (10-second moving window) copy of this translation to act as a high-pass filter. This removes slow global floor drift (e.g., walking across the room) while preserving fast dance sways.
4. Scales the isolated sway by an adjustable gain factor (default `1.8`) to enhance visual readability.

---

## 3. Spatial Transformations & Blender Integration

### Coordinate System Mapping

MediaPipe and Blender utilize fundamentally different right-handed coordinate spaces. During the JSON ingestion phase within Blender, coordinates are mapped via the transformation:

$$\begin{pmatrix} x_{\text{blender}} \\ y_{\text{blender}} \\ z_{\text{blender}} \end{pmatrix} = \begin{pmatrix} x_{\text{mp}} \\ z_{\text{mp}} \\ -y_{\text{mp}} \end{pmatrix}$$

### Depth Presentation Adjustment

A common movement in dance—a forward hip thrust—is encoded by MediaPipe as anterior spine lean along the depth axis (camera view vector). In a standard head-on orthographic or perspective projection, motion along the Z-axis foreshortens to zero. To preserve the visual readability of depth-heavy choreography without altering the underlying physics, the build script yaws the root armature by **$45^\circ$ around the global Z-axis**, converting orthogonal depth thrusts into visible diagonal sways.

### Armature Construction & Baking

* **Skeleton Generation:** Construct a stick-figure armature using `POSE_CONNECTIONS` topology.
* **Keyframing:** Sets bone head and tail positions frame-by-frame matching the video's FPS.
* **Baking:** Executes `nla.bake` to evaluate constraints and drivers, writing raw transformation matrices directly to the animation curves and purging temporary driver data.

---

## 4. Headless Self-Verification

To eliminate the friction of manually launching Blender to check outputs, the script executes an automated verification pass:

1. Re-invokes Blender in `--background` mode with a `--dump` flag.
2. Reads the baked 3D bone head/tail world matrices across 8 evenly sampled time slices.
3. Generates a matplotlib visual grid in the local venv, pairing the source video frame with orthogonal (front and top-down) projections of the 3D skeleton.
4. Saves a `.preview.png` contact sheet directly to the output directory for immediate quality assurance.

---
