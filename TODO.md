
## Targeted Improvements for the Pipeline

Here are four technical refinements you can introduce to improve the fidelity, temporal stability, and accuracy of your animation system:

### 1. Upgrade from One Euro to Acausal Savitzky-Golay Smoothing

The One Euro filter is causal—it only looks at past frames. While essential for real-time interactive tracking, it introduces a subtle phase lag during sudden directional changes in offline processing.

* **Improvement:** Since your pipeline is strictly offline and batch-oriented, replace the One Euro filter with an **acausal bidirectional filter** like a **Savitzky-Golay filter** or a **Rauch-Tung-Striebel (RTS) Kalman smoother**. By evaluating both past and future frames simultaneously, you achieve zero-phase distortion, eliminating high-frequency jitter while preserving the exact frame-snapped timing of sharp dance accents.

### 2. Add Velocity-Gated Foot Contact Locking

While your lowest-foot ground anchoring is a clever solution for hip translation, residual noise in the foot landmarks can still cause minor "skating" or floor-sliding.

* **Improvement:** Implement a velocity threshold gate for support foot identification. Compute the instantaneous velocity of the ankles/heel landmarks. When the velocity drops below an $\epsilon$ threshold, flag the foot as "planted" and explicitly hard-lock its $XY$ world coordinates across that time window. Only release the lock when the landmark velocity spikes above a "liftoff" threshold.

### 3. Implement Deterministic Bone Roll (Twist) Calculation

Currently, your stick figure connects joints from head to tail as 3D vectors. However, a 3D bone also possesses axial rotation (**roll** or twist). With only head/tail vectors, Blender assigns a default bone roll, which can cause unnatural bending if you ever attach a mesh or apply inverse kinematics later.

* **Improvement:** Use secondary lateral landmarks to construct a stable reference plane for limbs. For example, use the plane formed by `[Shoulder, Elbow, Wrist]` to deterministically compute the normal vector of the arm. Align the bone's local X/Z axis to this normal before baking, ensuring realistic elbow and knee hinge directions.

### 4. Uniform Timestamp Spline Resampling

While storing `cv2.CAP_PROP_POS_MSEC` correctly prevents sync drift in VFR TikTok/phone footage, mapping variable timestamp intervals directly onto Blender's fixed-frame grid can occasionally cause micro-stuttering in fast movements.

* **Improvement:** Before exporting the JSON, pass the cleaned, rigidified landmark time-series through a **cubic spline interpolator** (e.g., using `scipy.interpolate.CubicSpline`). Resample the spatial data onto a strictly uniform temporal grid that matches the target Blender FPS (e.g., exactly every $24.15\text{ ms}$ for a $41.43\text{ fps}$ target). This decouples the video's erratic decoding timestamps from Blender's timeline entirely, resulting in buttery-smooth playback.
